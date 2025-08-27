"""Configuration management for deimos-router."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from .default_models import get_all_default_models


class Config:
    """Configuration manager for API credentials and settings."""
    
    def __init__(self):
        self.api_url: Optional[str] = None
        self.api_key: Optional[str] = None
        self.default_models: Dict[str, str] = {}
        
        # Logging configuration
        self.logging_enabled: bool = True
        self.log_directory: str = "./logs"
        self.log_level: str = "full"  # "full" or "metadata_only"
        self.log_rotation: str = "daily"  # "daily" or "size"
        self.custom_pricing: Optional[Dict[str, Dict[str, float]]] = None
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from various sources in order of precedence."""
        # Initialize default models first
        self._set_default_models()
        
        # 1. Environment variables (highest precedence)
        self.api_url = os.getenv('DEIMOS_API_URL')
        self.api_key = os.getenv('DEIMOS_API_KEY')
        self._load_default_models_from_env()
        
        # 2. secrets.json in current working directory
        if not (self.api_url and self.api_key):
            self._load_from_file('secrets.json')
        
        # 3. config.json in current working directory
        if not (self.api_url and self.api_key):
            self._load_from_file('config.json')
        
        # 4. .secrets file in current working directory
        if not (self.api_url and self.api_key):
            self._load_from_file('.secrets')
        
        # 5. secrets.json in user's home directory
        if not (self.api_url and self.api_key):
            home_secrets = Path.home() / 'secrets.json'
            if home_secrets.exists():
                self._load_from_file(str(home_secrets))
    
    def _set_default_models(self) -> None:
        """Set the built-in default models for various tasks."""
        self.default_models = get_all_default_models()
    
    def _load_default_models_from_env(self) -> None:
        """Load default model overrides from environment variables."""
        # Allow overriding specific default models via environment variables
        env_prefix = 'DEIMOS_DEFAULT_MODEL_'
        for key in self.default_models.keys():
            env_key = f"{env_prefix}{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                self.default_models[key] = env_value
    
    def _load_from_file(self, filepath: str) -> None:
        """Load configuration from a JSON file."""
        try:
            path = Path(filepath)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                
                if not self.api_url and 'api_url' in data:
                    self.api_url = data['api_url']
                
                if not self.api_key and 'api_key' in data:
                    self.api_key = data['api_key']
                
                # Load logging configuration
                self._load_logging_config_from_data(data)
                
                # Load default models from file (overrides built-in defaults but not env vars)
                if 'default_models' in data and isinstance(data['default_models'], dict):
                    for key, value in data['default_models'].items():
                        if key in self.default_models and isinstance(value, str):
                            # Only override if not already set by environment variable
                            env_key = f"DEIMOS_DEFAULT_MODEL_{key.upper()}"
                            if not os.getenv(env_key):
                                self.default_models[key] = value
        
        except (json.JSONDecodeError, IOError, KeyError):
            # Silently ignore file loading errors
            pass
    
    def _load_logging_config_from_data(self, data: Dict) -> None:
        """Load logging configuration from config data."""
        # Load logging settings from environment variables first (highest precedence)
        self.logging_enabled = os.getenv('DEIMOS_LOGGING_ENABLED', str(self.logging_enabled)).lower() == 'true'
        self.log_directory = os.getenv('DEIMOS_LOG_DIRECTORY', self.log_directory)
        self.log_level = os.getenv('DEIMOS_LOG_LEVEL', self.log_level)
        self.log_rotation = os.getenv('DEIMOS_LOG_ROTATION', self.log_rotation)
        
        # Then load from config file (lower precedence)
        if 'logging' in data and isinstance(data['logging'], dict):
            logging_config = data['logging']
            
            if 'enabled' in logging_config and not os.getenv('DEIMOS_LOGGING_ENABLED'):
                self.logging_enabled = bool(logging_config['enabled'])
            
            if 'directory' in logging_config and not os.getenv('DEIMOS_LOG_DIRECTORY'):
                self.log_directory = str(logging_config['directory'])
            
            if 'level' in logging_config and not os.getenv('DEIMOS_LOG_LEVEL'):
                self.log_level = str(logging_config['level'])
            
            if 'rotation' in logging_config and not os.getenv('DEIMOS_LOG_ROTATION'):
                self.log_rotation = str(logging_config['rotation'])
            
            # Load custom pricing if provided
            if 'custom_pricing' in logging_config and isinstance(logging_config['custom_pricing'], dict):
                self.custom_pricing = logging_config['custom_pricing']
    
    def is_configured(self) -> bool:
        """Check if both API URL and API key are configured."""
        return bool(self.api_url and self.api_key)
    
    def get_credentials(self) -> Dict[str, str]:
        """Get API credentials as a dictionary."""
        if not self.is_configured():
            raise ValueError(
                "API credentials not configured. Please set DEIMOS_API_URL and "
                "DEIMOS_API_KEY environment variables, or create a secrets.json file. "
                "See README.md for detailed instructions."
            )
        
        return {
            'api_url': self.api_url,
            'api_key': self.api_key
        }
    
    def get_default_model(self, task: str) -> str:
        """Get the default model for a specific task.
        
        Args:
            task: The task name (e.g., 'code_language_detection', 'general_chat')
            
        Returns:
            The model name for the task, or 'gpt-4o-mini' if task not found
        """
        return self.default_models.get(task, 'gpt-4o-mini')
    
    def get_all_default_models(self) -> Dict[str, str]:
        """Get all default models as a dictionary."""
        return self.default_models.copy()


# Global configuration instance
config = Config()
