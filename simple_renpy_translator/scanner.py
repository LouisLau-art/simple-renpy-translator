"""
Text scanning and management for Simple RenPy Translator
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .parser import TextExtractor, TextBlock
from .project import Project
from .utils.file_utils import ensure_directory, save_json_file, load_json_file
from .utils.logger import get_logger


class TextScanner:
    """Scans and manages translatable text in a RenPy project."""
    
    def __init__(self):
        """Initialize text scanner."""
        self.extractor = TextExtractor()
        self.logger = get_logger()
    
    def scan_project(self, project: Project, language: str) -> Dict[str, Any]:
        """
        Scan a project for translatable text.
        
        Args:
            project: The RenPy project to scan
            language: Target language code
            
        Returns:
            Dictionary with scan results and statistics
        """
        self.logger.info(f"Scanning project '{project.name}' for language '{language}'")
        
        # Extract all text blocks
        text_blocks = self.extractor.extract_from_project(project.source_dir)
        
        # Remove duplicates based on text content and location
        unique_blocks = self._deduplicate_text_blocks(text_blocks)
        
        # Create scan results
        scan_result = {
            "project_name": project.name,
            "language": language,
            "scan_time": datetime.now().isoformat(),
            "statistics": self._calculate_statistics(unique_blocks),
            "text_blocks": [block.to_dict() for block in unique_blocks],
            "files_processed": len(project.get_rpy_files()) + len(project.get_rpyc_files())
        }
        
        # Update project metadata
        project.update_language_info(language, scan_result["statistics"])
        
        # Save scan results
        self._save_scan_results(project, language, scan_result)
        
        self.logger.info(f"Scan complete: {len(unique_blocks)} unique text blocks found")
        return scan_result
    
    def get_scan_results(self, project: Project, language: str) -> Optional[Dict[str, Any]]:
        """
        Get cached scan results for a project and language.
        
        Args:
            project: The RenPy project
            language: Target language code
            
        Returns:
            Scan results dictionary or None if not found
        """
        scan_file = self._get_scan_file_path(project, language)
        if scan_file and scan_file.exists():
            return load_json_file(scan_file)
        return None
    
    def _deduplicate_text_blocks(self, text_blocks: List[TextBlock]) -> List[TextBlock]:
        """Remove duplicate text blocks based on content and location."""
        seen = set()
        unique_blocks = []
        
        for block in text_blocks:
            # Create a key based on text content and file location
            key = (
                block.text_type,
                block.original_text.strip(),
                str(block.file_path),
                block.line_number
            )
            
            if key not in seen:
                seen.add(key)
                unique_blocks.append(block)
            else:
                # Log duplicate found
                self.logger.debug(f"Skipping duplicate: {block.original_text[:50]}...")
        
        self.logger.info(f"Deduplicated {len(text_blocks)} blocks to {len(unique_blocks)} unique blocks")
        return unique_blocks
    
    def _calculate_statistics(self, text_blocks: List[TextBlock]) -> Dict[str, int]:
        """Calculate statistics for text blocks."""
        total = len(text_blocks)
        dialogue_count = sum(1 for block in text_blocks if block.text_type == 'dialogue')
        string_count = sum(1 for block in text_blocks if block.text_type == 'string')
        
        # Calculate file distribution
        files = {}
        for block in text_blocks:
            file_key = str(block.file_path.relative_to(block.file_path.parent.parent))
            files[file_key] = files.get(file_key, 0) + 1
        
        return {
            "total": total,
            "dialogue": dialogue_count,
            "string": string_count,
            "files": files,
            "translated": 0,  # Will be updated when translations are imported
            "untranslated": total
        }
    
    def _get_scan_file_path(self, project: Project, language: str) -> Optional[Path]:
        """Get the file path for scan results."""
        return project.project_dir / f"scan_{language}.json"
    
    def _save_scan_results(self, project: Project, language: str, results: Dict[str, Any]) -> bool:
        """Save scan results to file."""
        scan_file = self._get_scan_file_path(project, language)
        if scan_file:
            return save_json_file(scan_file, results)
        return False
    
    def get_translation_statistics(self, project: Project, language: str) -> Dict[str, Any]:
        """
        Get translation statistics for a project and language.
        
        Args:
            project: The RenPy project
            language: Target language code
            
        Returns:
            Translation statistics
        """
        # Get scan results
        scan_results = self.get_scan_results(project, language)
        if not scan_results:
            return {
                "total": 0,
                "translated": 0,
                "untranslated": 0,
                "completion_rate": 0.0
            }
        
        stats = scan_results.get("statistics", {})
        total = stats.get("total", 0)
        
        # Calculate actual translated count from text blocks
        text_blocks = scan_results.get("text_blocks", [])
        translated_count = sum(1 for block in text_blocks if block.get("is_translated", False) and block.get("translation", "").strip())
        untranslated_count = total - translated_count
        
        # Calculate completion rate
        completion_rate = (translated_count / total * 100) if total > 0 else 0.0
        
        return {
            "total": total,
            "translated": translated_count,
            "untranslated": untranslated_count,
            "completion_rate": completion_rate,
            "dialogue_count": stats.get("dialogue", 0),
            "string_count": stats.get("string", 0),
            "files_count": len(stats.get("files", {})),
            "last_scan": scan_results.get("scan_time")
        }


# Global scanner instance
_global_scanner = None


def get_scanner() -> TextScanner:
    """Get global scanner instance."""
    global _global_scanner
    if _global_scanner is None:
        _global_scanner = TextScanner()
    return _global_scanner