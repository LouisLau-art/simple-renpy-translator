"""
Configuration management for Simple RenPy Translator
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Simple configuration manager."""
    
    DEFAULT_CONFIG = {
        'project': {
            'default_export_format': 'html',
            'output_dir': './exports',
            'backup_original': True
        },
        'translation': {
            'keep_formatting': True,
            'skip_empty': True,
            'backup_original': True
        },
        'html': {
            'template': 'default',
            'include_stats': True
        }
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        if config_dir is None:
            config_dir = Path.home() / '.simple_renpy_translator'
        
        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Return default config and save it
        self.save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'project.output_dir')."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def reset_to_default(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
    
    @classmethod
    def get_default_instance(cls) -> 'Config':
        """Get default configuration instance."""
        return cls()


# Global config instance
_global_config = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config.get_default_instance()
    return _global_config


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _global_config
    _global_config = config