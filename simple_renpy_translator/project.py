"""
Project management for Simple RenPy Translator
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .utils.file_utils import ensure_directory, safe_copy, load_json_file, save_json_file, is_renpy_project
from .utils.logger import get_logger


class Project:
    """Represents a RenPy translation project."""
    
    def __init__(self, game_path: str, name: Optional[str] = None):
        """
        Initialize a project.
        
        Args:
            game_path: Path to the RenPy game directory
            name: Optional project name (defaults to game directory name)
        """
        self.game_path = Path(game_path).resolve()
        self.name = name or self.game_path.name
        self.created_at = datetime.now()
        
        # Project directories
        self.source_dir = self.game_path / "game"
        self.tl_dir = self.game_path / "game" / "tl"
        self.project_dir = Path.home() / ".simple_renpy_translator" / "projects" / self.name
        
        # Project metadata
        self.metadata_file = self.project_dir / "project.json"
        self.metadata = self._load_metadata()
        
        self.logger = get_logger()
        
        # Validate project structure
        if not self._validate_structure():
            raise ValueError(f"Not a valid RenPy project: {self.game_path}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load project metadata."""
        if self.metadata_file.exists():
            data = load_json_file(self.metadata_file)
            if data:
                return data
        
        # Create new metadata
        return {
            "name": self.name,
            "game_path": str(self.game_path),
            "source_dir": str(self.source_dir),
            "tl_dir": str(self.tl_dir),
            "created_at": self.created_at.isoformat(),
            "languages": [],
            "last_scan": {},
            "statistics": {}
        }
    
    def _save_metadata(self) -> bool:
        """Save project metadata."""
        try:
            ensure_directory(self.metadata_file.parent)
            return save_json_file(self.metadata_file, self.metadata)
        except Exception as e:
            self.logger.error(f"Failed to save project metadata: {e}")
            return False
    
    def _validate_structure(self) -> bool:
        """Validate RenPy project structure."""
        if not self.game_path.exists():
            self.logger.error(f"Game directory does not exist: {self.game_path}")
            return False
        
        if not is_renpy_project(self.game_path):
            self.logger.error(f"Directory is not a RenPy project: {self.game_path}")
            return False
        
        if not self.source_dir.exists():
            self.logger.error(f"Game source directory missing: {self.source_dir}")
            return False
        
        return True
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages in the project."""
        languages = []
        
        if self.tl_dir.exists():
            for lang_dir in self.tl_dir.iterdir():
                if lang_dir.is_dir() and not lang_dir.name.startswith('.'):
                    languages.append(lang_dir.name)
        
        return sorted(languages)
    
    def get_rpy_files(self) -> List[Path]:
        """Get all RPY files in the project."""
        rpy_files = []
        if self.source_dir.exists():
            try:
                rpy_files = list(self.source_dir.rglob("*.rpy"))
            except Exception as e:
                self.logger.error(f"Error scanning for RPY files: {e}")
        
        return rpy_files
    
    def get_rpyc_files(self) -> List[Path]:
        """Get all RPYC files in the project."""
        rpyc_files = []
        if self.source_dir.exists():
            try:
                rpyc_files = list(self.source_dir.rglob("*.rpyc"))
            except Exception as e:
                self.logger.error(f"Error scanning for RPYC files: {e}")
        
        return rpyc_files
    
    def has_language(self, language: str) -> bool:
        """Check if project has translations for the specified language."""
        lang_dir = self.tl_dir / language
        return lang_dir.exists()
    
    def get_language_files(self, language: str) -> List[Path]:
        """Get all translation files for a specific language."""
        if not self.has_language(language):
            return []
        
        lang_dir = self.tl_dir / language
        try:
            return list(lang_dir.rglob("*.rpy"))
        except Exception as e:
            self.logger.error(f"Error scanning language files for {language}: {e}")
            return []
    
    def update_language_info(self, language: str, info: Dict[str, Any]) -> None:
        """Update language information in metadata."""
        self.metadata["languages"] = [lang for lang in self.metadata["languages"] if lang != language]
        self.metadata["languages"].append(language)
        self.metadata["last_scan"][language] = datetime.now().isoformat()
        
        if "statistics" not in self.metadata:
            self.metadata["statistics"] = {}
        
        self.metadata["statistics"][language] = info
        self._save_metadata()
    
    def get_translation_statistics(self, language: str) -> Dict[str, int]:
        """Get translation statistics for a language."""
        stats = self.metadata.get("statistics", {}).get(language, {})
        return {
            "total": stats.get("total", 0),
            "translated": stats.get("translated", 0),
            "untranslated": stats.get("untranslated", 0),
            "completion_rate": 0.0
        }
    
    def save(self) -> bool:
        """Save project configuration."""
        return self._save_metadata()
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive project information."""
        return {
            "name": self.name,
            "game_path": str(self.game_path),
            "source_dir": str(self.source_dir),
            "tl_dir": str(self.tl_dir),
            "created_at": self.created_at.isoformat(),
            "languages": self.get_available_languages(),
            "rpy_files_count": len(self.get_rpy_files()),
            "rpyc_files_count": len(self.get_rpyc_files())
        }
    
    def __str__(self) -> str:
        return f"Project('{self.name}', path='{self.game_path}')"
    
    def __repr__(self) -> str:
        return self.__str__()


class ProjectManager:
    """Manages multiple translation projects."""
    
    def __init__(self):
        """Initialize project manager."""
        self.projects_dir = Path.home() / ".simple_renpy_translator" / "projects"
        self.logger = get_logger()
    
    def create_project(self, game_path: str, name: Optional[str] = None) -> Project:
        """Create a new translation project."""
        project = Project(game_path, name)
        
        # Ensure project directory exists
        ensure_directory(project.project_dir)
        
        # Save project metadata
        project.save()
        
        self.logger.info(f"Created project '{project.name}' for game: {game_path}")
        return project
    
    def get_project(self, name_or_path: str) -> Optional[Project]:
        """
        Get project by name or path.
        
        Args:
            name_or_path: Project name or full game path
            
        Returns:
            Project instance or None if not found
        """
        # First try as a direct path
        if Path(name_or_path).exists():
            try:
                return Project(name_or_path)
            except ValueError:
                pass
        
        # Then try as project name
        project_dir = self.projects_dir / name_or_path
        metadata_file = project_dir / "project.json"
        
        if metadata_file.exists():
            metadata = load_json_file(metadata_file)
            if metadata and "game_path" in metadata:
                try:
                    return Project(metadata["game_path"], metadata.get("name"))
                except ValueError as e:
                    self.logger.warning(f"Invalid project data for '{name_or_path}': {e}")
        
        return None
    
    def list_projects(self) -> List[Project]:
        """List all available projects."""
        projects = []
        
        if not self.projects_dir.exists():
            return projects
        
        try:
            for project_dir in self.projects_dir.iterdir():
                if project_dir.is_dir():
                    metadata_file = project_dir / "project.json"
                    if metadata_file.exists():
                        metadata = load_json_file(metadata_file)
                        if metadata and "game_path" in metadata:
                            try:
                                project = Project(
                                    metadata["game_path"], 
                                    metadata.get("name")
                                )
                                projects.append(project)
                            except ValueError:
                                continue
        except Exception as e:
            self.logger.error(f"Error listing projects: {e}")
        
        return sorted(projects, key=lambda p: p.created_at)
    
    def delete_project(self, name: str) -> bool:
        """Delete a project."""
        project = self.get_project(name)
        if not project:
            self.logger.error(f"Project '{name}' not found")
            return False
        
        try:
            import shutil
            if project.project_dir.exists():
                shutil.rmtree(project.project_dir)
            self.logger.info(f"Deleted project '{name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete project '{name}': {e}")
            return False


# Global project manager instance
_global_project_manager = None


def get_project_manager() -> ProjectManager:
    """Get global project manager instance."""
    global _global_project_manager
    if _global_project_manager is None:
        _global_project_manager = ProjectManager()
    return _global_project_manager