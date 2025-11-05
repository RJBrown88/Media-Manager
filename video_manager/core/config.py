"""
Configuration management for Video Manager application.
Handles user settings and application defaults.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager with persistent storage."""

    DEFAULT_CONFIG = {
        'cache_dir': os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~/.local/share')), 'VideoManager', 'cache'),
        'max_cache_size': 5 * 1024 * 1024 * 1024,  # 5GB in bytes
        'thumbnail_quality': 80,
        'thumbnail_max_count': 500,
        'thumbnail_resolution': (426, 240),  # 240p width for 16:9
        'network_timeout': 30,  # seconds
        'chunk_size': 64 * 1024 * 1024,  # 64MB
        'max_parallel_metadata': 3,
        'max_parallel_ops': 1,
        'bandwidth_limit': 0,  # 0 = unlimited, otherwise MB/s
        'max_thumbnails_in_memory': 10,
        'files_per_page': 50,
        'scan_batch_size': 50,
        'deep_scan_threshold': 5 * 1024 * 1024 * 1024,  # 5GB
        'header_read_size': 10 * 1024 * 1024,  # 10MB
        'cache_prune_threshold': 4 * 1024 * 1024 * 1024,  # 4GB
        'recent_directories': [],
        'window_geometry': None,
    }

    def __init__(self, config_file: str = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            config_dir = os.path.join(
                os.getenv('LOCALAPPDATA', os.path.expanduser('~/.config')),
                'VideoManager'
            )
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'config.json')

        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load config: {e}")
                # Continue with defaults

        # Ensure cache directory exists
        os.makedirs(self.config['cache_dir'], exist_ok=True)

    def save(self) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value and save.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save()

    def add_recent_directory(self, directory: str) -> None:
        """
        Add directory to recent directories list.

        Args:
            directory: Directory path to add
        """
        recent = self.config['recent_directories']
        if directory in recent:
            recent.remove(directory)
        recent.insert(0, directory)
        # Keep only last 10
        self.config['recent_directories'] = recent[:10]
        self.save()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
