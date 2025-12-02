"""
RenPy file parser for Simple RenPy Translator
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .utils.file_utils import read_text_file, get_file_stats
from .utils.logger import get_logger


@dataclass
class TextBlock:
    """Represents a translatable text block."""
    
    # Basic identification
    identifier: str
    text_type: str  # 'dialogue', 'string', 'comment'
    
    # Content
    original_text: str
    
    # Location info
    file_path: Path
    line_number: int
    
    # Optional fields
    translation: str = ""
    start_pos: int = 0
    end_pos: int = 0
    character: Optional[str] = None  # For dialogue
    context: str = ""
    is_translated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'identifier': self.identifier,
            'text_type': self.text_type,
            'original_text': self.original_text,
            'translation': self.translation,
            'file_path': str(self.file_path),
            'line_number': self.line_number,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'character': self.character,
            'context': self.context,
            'is_translated': self.is_translated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextBlock':
        """Create from dictionary."""
        return cls(
            identifier=data['identifier'],
            text_type=data['text_type'],
            original_text=data['original_text'],
            translation=data.get('translation', ''),
            file_path=Path(data['file_path']),
            line_number=data['line_number'],
            start_pos=data.get('start_pos', 0),
            end_pos=data.get('end_pos', 0),
            character=data.get('character'),
            context=data.get('context', ''),
            is_translated=data.get('is_translated', False)
        )


class TextExtractor:
    """Extracts translatable text from RenPy files."""
    
    # Text identification patterns
    DIALOGUE_PATTERN = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*["\']([^"\']*)["\']', re.MULTILINE)
    SAY_PATTERN = re.compile(r'(?:say|voice)\s+([^:\n]*?):\s*(["\'])(.*?)\2', re.MULTILINE | re.DOTALL)
    STRING_PATTERN = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(["\'])(.*?)\2', re.MULTILINE | re.DOTALL)
    
    # Ignore patterns (comments, code)
    IGNORE_PATTERNS = [
        re.compile(r'^\s*#.*$', re.MULTILINE),  # Comments
        re.compile(r'^\s*label\s+', re.MULTILINE),  # Labels
        re.compile(r'^\s*python\s*:', re.MULTILINE),  # Python blocks
        re.compile(r'^\s*init\s*:', re.MULTILINE),  # Init blocks
    ]
    
    def __init__(self):
        """Initialize text extractor."""
        self.logger = get_logger()
        self.text_counter = 0
    
    def extract_from_file(self, file_path: Path) -> List[TextBlock]:
        """
        Extract text from a single RenPy file.
        
        Args:
            file_path: Path to the .rpy file
            
        Returns:
            List of TextBlock objects
        """
        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return []
        
        if not file_path.suffix.lower() in ['.rpy', '.rpyc']:
            self.logger.warning(f"Skipping non-RenPy file: {file_path}")
            return []
        
        content = read_text_file(file_path)
        if content is None:
            return []
        
        # Parse based on file type
        if file_path.suffix.lower() == '.rpy':
            return self._extract_from_rpy(file_path, content)
        elif file_path.suffix.lower() == '.rpyc':
            # RPYC files are compiled, very limited text extraction possible
            return self._extract_from_rpyc(file_path, content)
        
        return []
    
    def _extract_from_rpy(self, file_path: Path, content: str) -> List[TextBlock]:
        """Extract text from RPY file."""
        text_blocks = []
        lines = content.split('\n')
        
        # Track position for accurate text locations
        current_line = 0
        current_pos = 0
        
        for line_num, line in enumerate(lines, 1):
            line_start_pos = current_pos
            
            # Skip if line should be ignored
            if self._should_ignore_line(line):
                current_pos += len(line) + 1  # +1 for newline
                continue
            
            # Try to extract dialogue
            dialogue_text = self._extract_dialogue(line, file_path, line_num, line_start_pos)
            if dialogue_text:
                text_blocks.append(dialogue_text)
            
            # Try to extract strings
            string_texts = self._extract_strings(line, file_path, line_num, line_start_pos)
            text_blocks.extend(string_texts)
            
            current_pos += len(line) + 1  # +1 for newline
        
        self.logger.info(f"Extracted {len(text_blocks)} text blocks from {file_path}")
        return text_blocks
    
    def _extract_from_rpyc(self, file_path: Path, content: str) -> List[TextBlock]:
        """Extract text from RPYC file (limited extraction)."""
        # RPYC files are compiled, very limited text extraction
        # We can try to find string literals that might be translatable
        text_blocks = []
        
        # Simple pattern for quoted strings in RPYC
        string_pattern = re.compile(r'(["\'])(.*?)\1')
        
        matches = string_pattern.finditer(content)
        for match in matches:
            text = match.group(2)
            if len(text.strip()) > 0 and self._looks_like_translatable_text(text):
                text_block = TextBlock(
                    identifier=self._generate_identifier(file_path, 'S'),
                    text_type='string',
                    original_text=text,
                    file_path=file_path,
                    line_number=1,  # RPYC doesn't have reliable line numbers
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context='RPYC extracted'
                )
                text_blocks.append(text_block)
        
        self.logger.info(f"Extracted {len(text_blocks)} text blocks from RPYC {file_path}")
        return text_blocks
    
    def _should_ignore_line(self, line: str) -> bool:
        """Check if a line should be ignored."""
        stripped_line = line.strip()
        
        # Empty lines are fine
        if not stripped_line:
            return False
        
        # Check against ignore patterns
        for pattern in self.IGNORE_PATTERNS:
            if pattern.match(line):
                return True
        
        return False
    
    def _extract_dialogue(self, line: str, file_path: Path, line_num: int, start_pos: int) -> Optional[TextBlock]:
        """Extract dialogue text from a line."""
        # Check for quoted strings first (standalone dialogue)
        quote_match = re.search(r'\s*(["\'])([^"\']*?)\1', line)
        if quote_match:
            text = quote_match.group(2)
            
            # Try to identify speaker
            # Pattern: character_name "text"
            dialogue_match = re.search(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(["\'])([^"\']*?)\2', line)
            if dialogue_match:
                character = dialogue_match.group(1)
                text = dialogue_match.group(3)
            else:
                character = None
            
            if self._looks_like_translatable_text(text):
                return TextBlock(
                    identifier=self._generate_identifier(file_path, 'D'),
                    text_type='dialogue',
                    original_text=text,
                    file_path=file_path,
                    line_number=line_num,
                    start_pos=start_pos + quote_match.start(),
                    end_pos=start_pos + quote_match.end(),
                    character=character,
                    context='dialogue'
                )
        
        return None
    
    def _extract_strings(self, line: str, file_path: Path, line_num: int, start_pos: int) -> List[TextBlock]:
        """Extract string assignments from a line."""
        text_blocks = []
        matches = self.STRING_PATTERN.finditer(line)
        
        for match in matches:
            var_name = match.group(1)
            text = match.group(3)
            
            # Skip common non-translatable variables
            if var_name.lower() in ['version', 'save_name', 'config', 'gui', 'style']:
                continue
            
            if self._looks_like_translatable_text(text):
                text_block = TextBlock(
                    identifier=self._generate_identifier(file_path, 'S'),
                    text_type='string',
                    original_text=text,
                    file_path=file_path,
                    line_number=line_num,
                    start_pos=start_pos + match.start(),
                    end_pos=start_pos + match.end(),
                    context=f'string variable: {var_name}'
                )
                text_blocks.append(text_block)
        
        return text_blocks
    
    def _generate_identifier(self, file_path: Path, prefix: str) -> str:
        """Generate a unique identifier for a text block."""
        self.text_counter += 1
        return f"{prefix}{self.text_counter}_{file_path.stem}"
    
    def _looks_like_translatable_text(self, text: str) -> bool:
        """
        Check if text looks like it should be translated.
        
        This is a heuristic based on text characteristics.
        """
        # Strip quotes and whitespace
        cleaned_text = text.strip().strip('"\'')
        
        # Skip very short text
        if len(cleaned_text) < 2:
            return False
        
        # Skip if it looks like code or variables
        if cleaned_text.startswith(('$', '{', '[')) or '{' in cleaned_text:
            return False
        
        # Skip file paths (common in RenPy projects)
        if self._is_file_path(cleaned_text):
            return False
        
        # Skip common RenPy keywords and system strings
        if self._is_renpy_keyword(cleaned_text):
            return False
        
        # Skip if it's mostly numbers or special characters
        letters = sum(1 for c in cleaned_text if c.isalpha())
        if letters == 0:
            return False
        
        # Skip single words that are likely identifiers
        if len(cleaned_text.split()) == 1 and self._looks_like_identifier(cleaned_text):
            return False
        
        # Looks translatable if it has a reasonable amount of text
        return True
    
    def _is_file_path(self, text: str) -> bool:
        """Check if text looks like a file path."""
        # Common file extensions in RenPy
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.ogg', '.mp3', '.wav', '.mp4', '.webm', '.ttf', '.otf', '.pyc']
        
        # Check if it contains file extensions
        for ext in extensions:
            if ext in text:
                return True
        
        # Check if it looks like a file path (contains slashes or backslashes)
        if '/' in text or '\\' in text:
            return True
        
        # Check if it's a RenPy resource path
        if text.startswith(('images/', 'audio/', 'game/', 'gui/')):
            return True
        
        return False
    
    def _is_renpy_keyword(self, text: str) -> bool:
        """Check if text is a common RenPy keyword that doesn't need translation."""
        keywords = {
            # File references and GUI elements
            'default', 'say', 'image', 'show', 'hide', 'scene', 'menu', 'choice',
            # Common identifiers that are not user-facing
            'idle', 'hover', 'activate_sound', 'hover_sound', 'background', 'foreground',
            'top_bar', 'bottom_bar', 'left_bar', 'right_bar', 'thumb', 'mouse',
            # GUI style names
            'gui', 'style', 'config', 'version', 'viewport', 'navigation', 'button',
            'frame', 'label', 'window', 'namebox', 'input', 'check', 'radio', 'slider',
            # Common UI text
            'Back', 'History', 'Skip', 'Auto', 'Q.Save', 'Q.Load', 'Menu', 'Save', 'Load',
            'Options', 'New Game', 'Main Menu', 'Memory Room', 'Credits', 'Support', 'Quit',
            'Return', 'About', 'Yes', 'No', 'Disable', 'Left', 'Right', 'Unseen Text',
            'After Choices', 'Transitions', 'English', 'Russian', 'French', 'Test',
            'Mute All', 'All mute', 'Keyboard', 'Mouse', 'Gamepad', 'Calibrate',
            'Skipping', 'confirm', 'skip', 'notify', 'nvl_window', 'nvl_button',
            # Variables and technical terms
            'audio', 'music', 'sound', 'voice', 'volume', 'time', 'text speed',
            'all mute', 'replace', 'replaced', 'hide', 'show', 'page', 'slot',
            'choice_button', 'choice_prompt', 'file_info', 'line', 'file',
            # Animation and transition terms
            'fade', 'dissolve', 'move', 'ease', 'linear', 'smooth',
            # Status indicators
            'Locked', 'none', 'alternate', 'block', 'type', 'what', 'who',
            'code', 'new_code', 'parsed', 'missing_count', 'usage_count',
            # Common single words that are technical
            'say', 'voice', 'music', 'image', 'scene', 'hide', 'show', 'jump',
            'call', 'return', 'if', 'else', 'elif', 'while', 'for', 'with',
            'init', 'default', 'transform', 'screen', 'python', 'on'
        }
        
        return text.lower() in keywords
    
    def _looks_like_identifier(self, text: str) -> bool:
        """Check if text looks like a programming identifier."""
        # Pure identifiers (letters, numbers, underscores, no spaces)
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', text))
    
    def extract_from_project(self, source_dir: Path) -> List[TextBlock]:
        """
        Extract text from all files in a project directory.
        
        Args:
            source_dir: Path to the 'game' directory of a RenPy project
            
        Returns:
            List of all TextBlock objects
        """
        all_text_blocks = []
        
        # Find all RPY and RPYC files
        rpy_files = list(source_dir.rglob("*.rpy"))
        rpyc_files = list(source_dir.rglob("*.rpyc"))
        
        self.logger.info(f"Found {len(rpy_files)} RPY files and {len(rpyc_files)} RPYC files")
        
        # Extract from RPY files first (more reliable)
        for rpy_file in rpy_files:
            text_blocks = self.extract_from_file(rpy_file)
            all_text_blocks.extend(text_blocks)
        
        # Then from RPYC files
        for rpyc_file in rpyc_files:
            text_blocks = self.extract_from_file(rpyc_file)
            all_text_blocks.extend(text_blocks)
        
        self.logger.info(f"Total extracted: {len(all_text_blocks)} text blocks")
        
        # Reset counter for next extraction
        self.text_counter = 0
        
        return all_text_blocks