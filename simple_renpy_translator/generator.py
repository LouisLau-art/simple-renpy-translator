"""
RenPy translation file generator for Simple RenPy Translator
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .parser import TextBlock
from .project import Project
from .scanner import get_scanner
from .utils.file_utils import write_text_file, ensure_directory, create_backup
from .utils.logger import get_logger


class TranslationFileGenerator:
    """Generates RenPy translation files from translated text."""
    
    def __init__(self):
        """Initialize translation file generator."""
        self.logger = get_logger()
    
    def generate_translation_files(self, project: Project, language: str) -> bool:
        """
        Generate RenPy translation files for a project and language.
        
        Args:
            project: The RenPy project
            language: Target language code
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get scan results with translations
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, language)
        if not scan_results:
            self.logger.error(f"No scan results found for language '{language}'. Run 'rt scan' first.")
            return False
        
        # Convert text blocks back to objects for processing
        text_blocks = [TextBlock.from_dict(block_data) for block_data in scan_results["text_blocks"]]
        
        # Filter only translated blocks
        translated_blocks = [block for block in text_blocks if block.is_translated and block.translation.strip()]
        
        if not translated_blocks:
            self.logger.warning("No translated text blocks found")
            print("⚠️  No translations found to generate files for")
            return False
        
        self.logger.info(f"Found {len(translated_blocks)} translated blocks")
        
        # Group translations by file
        translations_by_file = self._group_translations_by_file(translated_blocks)
        
        # Generate translation files
        generated_files = []
        for file_path, translations in translations_by_file.items():
            if self._generate_translation_file(project, language, file_path, translations):
                generated_files.append(file_path)
        
        if generated_files:
            print(f"✅ Generated translation files for project '{project.name}'")
            print(f"   Language: {language}")
            print(f"   Files generated: {len(generated_files)}")
            for file_path in generated_files:
                print(f"   - {file_path}")
            
            # Update project statistics
            stats = scan_results.get("statistics", {})
            stats["files_with_translations"] = len(generated_files)
            project.update_language_info(language, stats)
            
            return True
        else:
            self.logger.error("Failed to generate any translation files")
            return False
    
    def _group_translations_by_file(self, translated_blocks: List[TextBlock]) -> Dict[str, List[TextBlock]]:
        """Group translations by their source file."""
        grouped = {}
        
        for block in translated_blocks:
            # Get relative path from project source directory
            relative_path = str(block.file_path.relative_to(block.file_path.parent.parent.parent))
            group_key = relative_path
            
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(block)
        
        return grouped
    
    def _generate_translation_file(self, project: Project, language: str, 
                                  source_file_path: str, translations: List[TextBlock]) -> bool:
        """Generate a single RenPy translation file."""
        
        # Determine output path
        # Convert game/test.rpy to game/tl/language/test.rpy
        if source_file_path.startswith("game/"):
            game_relative_path = source_file_path[5:]  # Remove "game/" prefix
            translation_file_path = Path(game_relative_path)
        else:
            translation_file_path = Path(source_file_path)
        
        # Create output directory
        output_dir = project.game_path / "game" / "tl" / language
        ensure_directory(output_dir)
        
        # Full path to translation file
        translation_file = output_dir / translation_file_path
        
        # Ensure parent directory exists
        ensure_directory(translation_file.parent)
        
        # Generate translation file content
        content = self._generate_translation_file_content(translations, language)
        
        # Create backup if file exists
        if translation_file.exists():
            backup_file = create_backup(translation_file)
            if backup_file:
                self.logger.info(f"Created backup: {backup_file}")
        
        # Write translation file
        success = write_text_file(translation_file, content)
        if success:
            self.logger.info(f"Generated translation file: {translation_file}")
            return True
        else:
            self.logger.error(f"Failed to write translation file: {translation_file}")
            return False
    
    def _generate_translation_file_content(self, translations: List[TextBlock], language: str) -> str:
        """Generate content for a RenPy translation file."""
        
        # Sort translations by line number for consistent output
        translations = sorted(translations, key=lambda x: x.line_number)
        
        lines = []
        
        # Header comment
        lines.append(f"# Simple RenPy Translator - {language.upper()} Translation")
        lines.append(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# Total translations: {len(translations)}")
        lines.append("")
        
        # Group by dialogue vs strings for better organization
        dialogue_translations = [t for t in translations if t.text_type == 'dialogue']
        string_translations = [t for t in translations if t.text_type == 'string']
        
        # Add dialogue translations
        if dialogue_translations:
            lines.append("# Dialogue translations")
            lines.append("")
            
            for translation in dialogue_translations:
                lines.append(self._format_dialogue_translation(translation))
            lines.append("")
        
        # Add string translations
        if string_translations:
            lines.append("# String translations")
            lines.append("")
            
            for translation in string_translations:
                lines.append(self._format_string_translation(translation))
        
        return "\n".join(lines)
    
    def _format_dialogue_translation(self, translation: TextBlock) -> str:
        """Format a dialogue translation for RenPy."""
        
        # Get the original text and translation
        original_text = translation.original_text
        translated_text = translation.translation
        
        # Escape for RenPy
        original_escaped = self._escape_renpy_text(original_text)
        translated_escaped = self._escape_renpy_text(translated_text)
        
        # Format based on original structure
        if translation.character:
            # Format: character "original text" if character and not "original text"
            if not original_text.startswith('"') and not original_text.startswith("'"):
                return f'{translation.character} "{translated_escaped}"  # Original: "{original_escaped}"'
            else:
                return f'{translation.character} {translated_escaped}  # Original: {original_escaped}'
        else:
            # Format: "original text" -> "translated text"
            return f'{translated_escaped}  # Original: "{original_escaped}"'
    
    def _format_string_translation(self, translation: TextBlock) -> str:
        """Format a string translation for RenPy."""
        
        original_text = translation.original_text
        translated_text = translation.translation
        
        # Extract variable name from context if available
        var_name = None
        if translation.context and "string variable:" in translation.context:
            var_name = translation.context.replace("string variable: ", "").strip()
        
        original_escaped = self._escape_renpy_text(original_text)
        translated_escaped = self._escape_renpy_text(translated_text)
        
        if var_name:
            return f'{var_name} = "{translated_escaped}"  # Original: "{original_escaped}"'
        else:
            return f'# String: "{original_escaped}" -> "{translated_escaped}"'
    
    def _escape_renpy_text(self, text: str) -> str:
        """Escape text for proper RenPy format."""
        
        # Replace newlines with RenPy format
        text = text.replace('\n', '\\n')
        
        # Handle quotes
        if '"' in text and "'" not in text:
            # Use single quotes if no single quotes in text
            return f"'{text}'"
        else:
            # Use double quotes and escape internal double quotes
            text = text.replace('"', '\\"')
            return f'"{text}"'
    
    def validate_translation_files(self, project: Project, language: str) -> Dict[str, Any]:
        """Validate existing translation files for a project and language."""
        
        tl_dir = project.game_path / "game" / "tl" / language
        if not tl_dir.exists():
            return {'valid': False, 'error': 'Translation directory not found'}
        
        rpy_files = list(tl_dir.rglob("*.rpy"))
        
        validation_results = {
            'valid': True,
            'files_found': len(rpy_files),
            'files': [],
            'errors': []
        }
        
        for file_path in rpy_files:
            file_result = self._validate_single_translation_file(file_path)
            validation_results['files'].append(file_result)
            
            if not file_result['valid']:
                validation_results['valid'] = False
                validation_results['errors'].extend(file_result['errors'])
        
        return validation_results
    
    def _validate_single_translation_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single translation file."""
        
        result = {
            'file': str(file_path),
            'valid': True,
            'errors': [],
            'warnings': [],
            'translation_count': 0
        }
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            translation_count = 0
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and ('=' in line or '"' in line or "'" in line):
                    translation_count += 1
            
            result['translation_count'] = translation_count
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Cannot read file: {e}")
        
        return result


# Global generator instance
_global_generator = None


def get_generator() -> TranslationFileGenerator:
    """Get global generator instance."""
    global _global_generator
    if _global_generator is None:
        _global_generator = TranslationFileGenerator()
    return _global_generator