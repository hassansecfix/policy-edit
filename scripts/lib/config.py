#!/usr/bin/env python3
"""
Configuration module for Policy Automation Scripts
Reads configuration values from config.sh to provide a single source of truth
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional


class Config:
    """
    Configuration manager that reads from config.sh for consistency
    """
    
    def __init__(self):
        self._config_file = Path(__file__).parent.parent.parent / "config.sh"
        self._config_cache = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.sh file"""
        if not self._config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self._config_file}")
        
        try:
            # Read the shell script and extract variable assignments
            with open(self._config_file, 'r') as f:
                content = f.read()
            
            # Extract variable assignments using regex
            # Matches patterns like: VARIABLE_NAME="value" or VARIABLE_NAME='value'
            pattern = r'^([A-Z_]+)=[\'""]([^\'""]+)[\'""]'
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                    
                match = re.match(pattern, line)
                if match:
                    var_name, var_value = match.groups()
                    self._config_cache[var_name] = var_value
                    
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value by key"""
        return self._config_cache.get(key, default)
    
    @property
    def policy_instructions_path(self) -> str:
        """Get the policy instructions file path"""
        result = self.get('DEFAULT_POLICY_INSTRUCTIONS')
        if not result:
            raise RuntimeError("DEFAULT_POLICY_INSTRUCTIONS not found in config.sh - please check your configuration")
        return result
    
    @property
    def default_policy_file(self) -> str:
        """Get the default policy file path"""
        return self.get('DEFAULT_POLICY_FILE', 'data/v5 Freya POL-11 Access Control.docx')
    
    @property
    def default_output_name(self) -> str:
        """Get the default output name"""
        return self.get('DEFAULT_OUTPUT_NAME', 'policy_tracked_changes_with_comments')
    
    def reload(self):
        """Reload configuration from file"""
        self._config_cache.clear()
        self._load_config()


# Global configuration instance
_config = None

def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_policy_instructions_path() -> str:
    """Convenience function to get policy instructions path"""
    return get_config().policy_instructions_path


def get_default_policy_file() -> str:
    """Convenience function to get default policy file"""
    return get_config().default_policy_file


def get_default_output_name() -> str:
    """Convenience function to get default output name"""
    return get_config().default_output_name


if __name__ == "__main__":
    # Test the configuration loading
    config = get_config()
    print("Configuration loaded successfully:")
    print(f"  Policy Instructions: {config.policy_instructions_path}")
    print(f"  Default Policy File: {config.default_policy_file}")
    print(f"  Default Output Name: {config.default_output_name}")
