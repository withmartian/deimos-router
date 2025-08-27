"""Tests for configuration management."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from deimos_router.config import Config


class TestConfig:
    """Test cases for the Config class."""
    
    def test_environment_variables_take_precedence(self):
        """Test that environment variables have highest precedence."""
        with patch.dict(os.environ, {
            'DEIMOS_API_URL': 'https://env-api.com',
            'DEIMOS_API_KEY': 'env-key'
        }):
            config = Config()
            assert config.api_url == 'https://env-api.com'
            assert config.api_key == 'env-key'
            assert config.is_configured()
    
    def test_secrets_json_file_loading(self):
        """Test loading from secrets.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_file = Path(temp_dir) / 'secrets.json'
            secrets_data = {
                'api_url': 'https://file-api.com',
                'api_key': 'file-key'
            }
            
            with open(secrets_file, 'w') as f:
                json.dump(secrets_data, f)
            
            # Change to temp directory and create config
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                config = Config()
                assert config.api_url == 'https://file-api.com'
                assert config.api_key == 'file-key'
                assert config.is_configured()
            finally:
                os.chdir(original_cwd)
    
    def test_config_json_file_loading(self):
        """Test loading from config.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'config.json'
            config_data = {
                'api_url': 'https://config-api.com',
                'api_key': 'config-key'
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                config = Config()
                assert config.api_url == 'https://config-api.com'
                assert config.api_key == 'config-key'
                assert config.is_configured()
            finally:
                os.chdir(original_cwd)
    
    def test_unconfigured_state(self):
        """Test behavior when no configuration is provided."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    config = Config()
                    assert not config.is_configured()
                    assert config.api_url is None
                    assert config.api_key is None
                finally:
                    os.chdir(original_cwd)
    
    def test_get_credentials_success(self):
        """Test successful credential retrieval."""
        with patch.dict(os.environ, {
            'DEIMOS_API_URL': 'https://test-api.com',
            'DEIMOS_API_KEY': 'test-key'
        }):
            config = Config()
            credentials = config.get_credentials()
            assert credentials == {
                'api_url': 'https://test-api.com',
                'api_key': 'test-key'
            }
    
    def test_get_credentials_failure(self):
        """Test credential retrieval when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    config = Config()
                    with pytest.raises(ValueError, match="API credentials not configured"):
                        config.get_credentials()
                finally:
                    os.chdir(original_cwd)
    
    def test_invalid_json_file_ignored(self):
        """Test that invalid JSON files are silently ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_file = Path(temp_dir) / 'secrets.json'
            
            # Write invalid JSON
            with open(secrets_file, 'w') as f:
                f.write('{ invalid json }')
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                config = Config()
                # Should not raise an exception, just not be configured
                assert not config.is_configured()
            finally:
                os.chdir(original_cwd)
    
    def test_partial_configuration_from_env(self):
        """Test partial configuration from environment variables."""
        with patch.dict(os.environ, {
            'DEIMOS_API_URL': 'https://partial-api.com'
            # Missing DEIMOS_API_KEY
        }, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    config = Config()
                    assert config.api_url == 'https://partial-api.com'
                    assert config.api_key is None
                    assert not config.is_configured()
                finally:
                    os.chdir(original_cwd)
