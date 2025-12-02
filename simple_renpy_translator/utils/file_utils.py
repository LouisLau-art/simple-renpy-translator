"""
File utility functions for Simple RenPy Translator
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any


def ensure_directory(path: Path) -> None:
    """Ensure that a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def safe_copy(src: Path, dst: Path, backup: bool = True) -> bool:
    """
    Safely copy a file, optionally creating a backup.
    
    Args:
        src: Source file path
        dst: Destination file path
        backup: Whether to create a backup before copying
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if dst.exists():
            if backup:
                backup_path = dst.with_suffix(dst.suffix + '.backup')
                shutil.copy2(dst, backup_path)
            else:
                dst.unlink()
        
        ensure_directory(dst.parent)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"Error copying file {src} to {dst}: {e}")
        return False


def read_text_file(file_path: Path) -> Optional[str]:
    """Read text file with proper encoding detection."""
    encodings = ['utf-8', 'gbk', 'shift-jis', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    print(f"Failed to decode file {file_path} with any encoding")
    return None


def write_text_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Write text file with specified encoding."""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    try:
        content = read_text_file(file_path)
        if content:
            return json.loads(content)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
    return None


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to JSON file."""
    try:
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return write_text_file(file_path, content)
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False


def find_files(directory: Path, pattern: str = "*.rpy") -> List[Path]:
    """Find files matching pattern in directory recursively."""
    files = []
    try:
        files = list(directory.rglob(pattern))
    except Exception as e:
        print(f"Error searching files in {directory}: {e}")
    return files


def get_file_stats(file_path: Path) -> Dict[str, Any]:
    """Get file statistics."""
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'exists': file_path.exists()
        }
    except Exception as e:
        print(f"Error getting stats for {file_path}: {e}")
        return {}


def is_renpy_project(directory: Path) -> bool:
    """Check if directory appears to be a RenPy project."""
    game_dir = directory / "game"
    return game_dir.exists() and game_dir.is_dir()


def create_backup(file_path: Path) -> Optional[Path]:
    """Create a backup of a file."""
    if not file_path.exists():
        return None
    
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup for {file_path}: {e}")
        return None