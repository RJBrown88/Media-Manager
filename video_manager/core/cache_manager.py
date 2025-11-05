"""
Smart cache manager with LRU eviction and size monitoring.
Manages thumbnail cache and enforces size limits.
"""

import os
import shutil
from typing import Optional

from .database import Database


class CacheManager:
    """Manages cache with automatic pruning and size limits."""

    def __init__(self, database: Database, config: dict):
        """
        Initialize cache manager.

        Args:
            database: Database instance
            config: Configuration dictionary
        """
        self.db = database
        self.config = config
        self.cache_dir = config.get('cache_dir')
        self.max_cache_size = config.get('max_cache_size', 5 * 1024**3)
        self.max_thumbnail_count = config.get('thumbnail_max_count', 500)
        self.prune_threshold = config.get('cache_prune_threshold', 4 * 1024**3)

        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_size(self) -> int:
        """
        Get current total cache size.

        Returns:
            Cache size in bytes
        """
        stats = self.db.get_cache_stats()
        return stats.get('total_size', 0)

    def get_thumbnail_count(self) -> int:
        """
        Get current number of cached thumbnails.

        Returns:
            Number of thumbnails
        """
        stats = self.db.get_cache_stats()
        return stats.get('file_count', 0)

    def should_prune(self) -> bool:
        """
        Check if cache should be pruned.

        Returns:
            True if cache size exceeds prune threshold
        """
        cache_size = self.get_cache_size()
        return cache_size >= self.prune_threshold

    def prune_cache(self) -> dict:
        """
        Prune cache to maintain size limits.

        Returns:
            Dictionary with pruning statistics
        """
        start_size = self.get_cache_size()
        start_count = self.get_thumbnail_count()

        # Prune by count first (LRU)
        removed_count = self.db.prune_old_thumbnails(self.max_thumbnail_count)

        # Update statistics
        self.db.update_cache_stats()

        end_size = self.get_cache_size()
        end_count = self.get_thumbnail_count()

        return {
            'thumbnails_removed': removed_count,
            'size_before': start_size,
            'size_after': end_size,
            'size_freed': start_size - end_size,
            'count_before': start_count,
            'count_after': end_count,
        }

    def add_thumbnail(self, path: str, thumbnail_data: bytes) -> bool:
        """
        Add thumbnail to cache with automatic pruning.

        Args:
            path: File path
            thumbnail_data: Thumbnail JPEG bytes

        Returns:
            True if thumbnail was added
        """
        # Check if we need to prune before adding
        if self.should_prune():
            self.prune_cache()

        # Add thumbnail to database
        self.db.update_thumbnail(path, thumbnail_data)

        # Update cache stats
        self.db.update_cache_stats()

        return True

    def get_thumbnail(self, path: str) -> Optional[bytes]:
        """
        Get thumbnail from cache.

        Args:
            path: File path

        Returns:
            Thumbnail JPEG bytes or None
        """
        return self.db.get_thumbnail(path)

    def remove_thumbnail(self, path: str) -> None:
        """
        Remove thumbnail from cache.

        Args:
            path: File path
        """
        self.db.update_thumbnail(path, None)
        self.db.update_cache_stats()

    def clear_cache(self) -> None:
        """Clear entire cache."""
        self.db.clear_cache()

        # Also clean up any temporary files in cache directory
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith('.tmp'):
                    try:
                        os.remove(os.path.join(root, file))
                    except OSError:
                        pass

    def get_cache_stats(self) -> dict:
        """
        Get detailed cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = self.db.get_cache_stats()
        cache_size = stats.get('total_size', 0)
        file_count = stats.get('file_count', 0)

        return {
            'total_size': cache_size,
            'total_size_mb': cache_size / (1024**2),
            'file_count': file_count,
            'max_size': self.max_cache_size,
            'max_size_mb': self.max_cache_size / (1024**2),
            'max_count': self.max_thumbnail_count,
            'usage_percent': (cache_size / self.max_cache_size * 100) if self.max_cache_size > 0 else 0,
            'last_prune': stats.get('last_prune', 0),
        }

    def optimize_database(self) -> None:
        """Optimize database by vacuuming."""
        self.db.vacuum()

    def get_temp_file_path(self, filename: str) -> str:
        """
        Get path for temporary file in cache directory.

        Args:
            filename: Temporary filename

        Returns:
            Full path to temporary file
        """
        return os.path.join(self.cache_dir, f"{filename}.tmp")

    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files in cache directory.

        Returns:
            Number of files cleaned up
        """
        count = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith('.tmp'):
                    try:
                        os.remove(os.path.join(root, file))
                        count += 1
                    except OSError:
                        pass
        return count
