"""
HTML Import functionality for Simple RenPy Translator
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser
import html

from .parser import TextBlock
from .project import Project
from .scanner import get_scanner
from .utils.file_utils import read_text_file
from .utils.logger import get_logger


class TranslationTableParser(HTMLParser):
    """Parse translation table from HTML file."""
    
    def __init__(self):
        super().__init__()
        self.table_data = []
        self.current_row = []
        self.in_table = False
        self.in_td = False
        self.cell_content = ""
        self.row_index = 0
    
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'td' and self.in_table:
            self.in_td = True
            self.cell_content = ""
    
    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'td' and self.in_table:
            self.current_row.append(self.cell_content.strip())
            self.in_td = False
        elif tag == 'tr' and self.in_table:
            if self.current_row and len(self.current_row) >= 8:  # Valid row with enough columns
                self.table_data.append(self.current_row.copy())
            self.current_row = []
            self.row_index += 1
    
    def handle_data(self, data):
        if self.in_td:
            self.cell_content += data


class HTMLImporter:
    """Imports translatable text from HTML format."""
    
    def __init__(self):
        """Initialize HTML importer."""
        self.logger = get_logger()
    
    def import_project(self, project: Project, language: str, file_path: Path) -> bool:
        """
        Import translations from HTML file.
        
        Args:
            project: The RenPy project to import to
            language: Target language code
            file_path: Path to HTML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path.exists():
            self.logger.error(f"Import file not found: {file_path}")
            return False
        
        # Read HTML file
        html_content = read_text_file(file_path)
        if html_content is None:
            self.logger.error(f"Failed to read HTML file: {file_path}")
            return False
        
        # Parse HTML to extract translations
        translations = self._parse_html_translations(html_content)
        if not translations:
            self.logger.error("No translations found in HTML file")
            return False
        
        # Get current scan results
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, language)
        if not scan_results:
            self.logger.error(f"No scan results found for language '{language}'. Run 'rt scan' first.")
            return False
        
        # Match translations with text blocks
        matched_translations = self._match_translations_with_text_blocks(
            translations, scan_results["text_blocks"]
        )
        
        if not matched_translations:
            self.logger.warning("No matching translations found")
            return False
        
        # Update text blocks with translations
        updated_count = self._update_text_blocks(project, language, matched_translations)
        
        if updated_count > 0:
            print(f"📥 Import completed!")
            print(f"   Updated translations: {updated_count}")
            print(f"   Language: {language}")
            print(f"   Project: {project.name}")
            return True
        else:
            print("⚠️  No translations were imported (possibly already translated)")
            return False
    
    def _parse_html_translations(self, html_content: str) -> List[Dict[str, str]]:
        """Parse HTML content to extract translations."""
        parser = TranslationTableParser()
        parser.feed(html_content)
        
        translations = []
        
        # Skip header row (first row)
        for row in parser.table_data[1:]:
            if len(row) >= 4:  # Ensure we have at least index, type, original, translation
                try:
                    index = int(row[0])
                    text_type = row[1].upper()
                    original_text = row[2].strip()
                    translation = row[3].strip()
                    
                    # Only include if there's actually a translation
                    if translation and not translation.startswith('<em>'):
                        translations.append({
                            'index': index,
                            'type': text_type,
                            'original_text': original_text,
                            'translation': translation
                        })
                except (ValueError, IndexError):
                    continue
        
        self.logger.info(f"Parsed {len(translations)} translations from HTML")
        return translations
    
    def _match_translations_with_text_blocks(self, translations: List[Dict[str, str]], 
                                           text_blocks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match translations with existing text blocks."""
        
        # Convert text blocks to lookup dictionary
        text_block_lookup = {}
        for i, block_data in enumerate(text_blocks_data):
            # Use a combination of index and text content for matching
            lookup_key = (
                i + 1,  # 1-based index
                block_data['original_text'],
                block_data['text_type']
            )
            text_block_lookup[lookup_key] = block_data
        
        matched_translations = []
        
        for translation in translations:
            # Try exact index match first
            lookup_key = (translation['index'], translation['original_text'], translation['type'])
            
            if lookup_key in text_block_lookup:
                matched_translations.append({
                    'text_block_data': text_block_lookup[lookup_key],
                    'translation': translation['translation']
                })
            else:
                # Try fuzzy matching based on text content
                fuzzy_match = self._find_fuzzy_match(translation, text_blocks_data)
                if fuzzy_match:
                    matched_translations.append({
                        'text_block_data': fuzzy_match,
                        'translation': translation['translation']
                    })
        
        self.logger.info(f"Matched {len(matched_translations)} translations with text blocks")
        return matched_translations
    
    def _find_fuzzy_match(self, translation: Dict[str, str], 
                         text_blocks_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find fuzzy match for translation in text blocks."""
        
        translation_original = translation['original_text'].lower().strip()
        
        for block_data in text_blocks_data:
            block_original = block_data['original_text'].lower().strip()
            
            # Exact match
            if translation_original == block_original:
                return block_data
            
            # Close match (allow minor differences)
            if self._text_similarity(translation_original, block_original) > 0.8:
                return block_data
        
        return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        if not text1 or not text2:
            return 0.0
        
        # Simple character-based similarity
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _update_text_blocks(self, project: Project, language: str, 
                           matched_translations: List[Dict[str, Any]]) -> int:
        """Update text blocks with new translations."""
        
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, language)
        if not scan_results:
            return 0
        
        text_blocks = scan_results["text_blocks"]
        updated_count = 0
        
        # Create a mapping for quick lookup
        for matched in matched_translations:
            target_block_data = matched['text_block_data']
            translation = matched['translation']
            
            # Find and update the corresponding text block
            for block_data in text_blocks:
                if (block_data['original_text'] == target_block_data['original_text'] and
                    block_data['text_type'] == target_block_data['text_type'] and
                    block_data['file_path'] == target_block_data['file_path'] and
                    block_data['line_number'] == target_block_data['line_number']):
                    
                    # Update translation
                    block_data['translation'] = translation
                    block_data['is_translated'] = True
                    updated_count += 1
                    break
        
        # Save updated scan results
        if updated_count > 0:
            scanner._save_scan_results(project, language, scan_results)
            
            # Update project statistics
            stats = scan_results['statistics']
            stats['translated'] = sum(1 for block in text_blocks if block.get('is_translated', False))
            stats['untranslated'] = stats['total'] - stats['translated']
            
            project.update_language_info(language, stats)
        
        return updated_count
    
    def validate_translation_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate HTML translation file and return statistics."""
        if not file_path.exists():
            return {'valid': False, 'error': 'File not found'}
        
        html_content = read_text_file(file_path)
        if html_content is None:
            return {'valid': False, 'error': 'Cannot read file'}
        
        translations = self._parse_html_translations(html_content)
        
        return {
            'valid': True,
            'translation_count': len(translations),
            'file_size': len(html_content),
            'sample_translations': translations[:3] if translations else []
        }