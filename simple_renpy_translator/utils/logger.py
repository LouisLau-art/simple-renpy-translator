"""
Simple logging utilities for Simple RenPy Translator
"""

import sys
from typing import Optional
from datetime import datetime


class SimpleLogger:
    """Simple logger for the application."""
    
    LEVELS = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3
    }
    
    def __init__(self, level: str = 'INFO', show_timestamp: bool = True):
        """Initialize logger."""
        self.level = self.LEVELS.get(level.upper(), self.LEVELS['INFO'])
        self.show_timestamp = show_timestamp
    
    def _format_message(self, level: str, message: str) -> str:
        """Format log message with optional timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.show_timestamp:
            return f"[{timestamp}] {level}: {message}"
        return f"{level}: {message}"
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        if self.level <= self.LEVELS['DEBUG']:
            print(self._format_message('DEBUG', message), file=sys.stderr)
    
    def info(self, message: str) -> None:
        """Log info message."""
        if self.level <= self.LEVELS['INFO']:
            print(self._format_message('INFO', message), file=sys.stdout)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        if self.level <= self.LEVELS['WARNING']:
            print(self._format_message('WARNING', message), file=sys.stdout)
    
    def error(self, message: str) -> None:
        """Log error message."""
        if self.level <= self.LEVELS['ERROR']:
            print(self._format_message('ERROR', message), file=sys.stderr)
    
    def log_exception(self, message: str, exception: Exception) -> None:
        """Log exception with traceback."""
        self.error(f"{message}: {exception}")
        import traceback
        traceback.print_exc()


# Global logger instance
_global_logger = SimpleLogger()


def get_logger() -> SimpleLogger:
    """Get global logger instance."""
    return _global_logger


def set_logger(logger: SimpleLogger) -> None:
    """Set global logger instance."""
    global _global_logger
    _global_logger = logger