"""
SQLite database management for video metadata caching.
Uses WAL mode for concurrent access and stores only metadata (no file content).
"""

import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Database:
    """SQLite database manager for video metadata."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS files (
        path TEXT PRIMARY KEY,
        size INTEGER,
        duration REAL,
        resolution TEXT,
        codec TEXT,
        mtime INTEGER,
        scan_time INTEGER,
        thumbnail BLOB
    );

    CREATE INDEX IF NOT EXISTS idx_mtime ON files(mtime);
    CREATE INDEX IF NOT EXISTS idx_scan_time ON files(scan_time);

    CREATE TABLE IF NOT EXISTS cache_stats (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        total_size INTEGER DEFAULT 0,
        file_count INTEGER DEFAULT 0,
        last_prune INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS operation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        operation_type TEXT,
        source_path TEXT,
        dest_path TEXT,
        status TEXT,
        error_message TEXT
    );
    """

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self) -> None:
        """Initialize database with schema and WAL mode."""
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

        # Create schema
        self.conn.executescript(self.SCHEMA)

        # Initialize cache stats if not exists
        self.conn.execute("""
            INSERT OR IGNORE INTO cache_stats (id, total_size, file_count, last_prune)
            VALUES (1, 0, 0, 0)
        """)
        self.conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def add_file(self, path: str, size: int, duration: float = None,
                 resolution: str = None, codec: str = None, mtime: int = None,
                 thumbnail: bytes = None) -> None:
        """
        Add or update file metadata.

        Args:
            path: File path
            size: File size in bytes
            duration: Video duration in seconds
            resolution: Video resolution (e.g., "1920x1080")
            codec: Video codec
            mtime: File modification time (Unix timestamp)
            thumbnail: Thumbnail image as JPEG bytes
        """
        scan_time = int(time.time())

        self.conn.execute("""
            INSERT OR REPLACE INTO files
            (path, size, duration, resolution, codec, mtime, scan_time, thumbnail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (path, size, duration, resolution, codec, mtime, scan_time, thumbnail))
        self.conn.commit()

    def get_file(self, path: str) -> Optional[Dict]:
        """
        Get file metadata.

        Args:
            path: File path

        Returns:
            Dictionary of file metadata or None if not found
        """
        cursor = self.conn.execute("SELECT * FROM files WHERE path = ?", (path,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_files(self, limit: int = None, offset: int = 0,
                  order_by: str = 'path') -> List[Dict]:
        """
        Get multiple files with pagination.

        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip
            order_by: Column to order by

        Returns:
            List of file metadata dictionaries
        """
        query = f"SELECT * FROM files ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_files_by_directory(self, directory: str) -> List[Dict]:
        """
        Get all files in a directory.

        Args:
            directory: Directory path

        Returns:
            List of file metadata dictionaries
        """
        # Normalize path for comparison
        directory = directory.replace('/', '\\') if '\\' in directory else directory
        if not directory.endswith(('\\', '/')):
            directory += '\\'

        cursor = self.conn.execute(
            "SELECT * FROM files WHERE path LIKE ? ORDER BY path",
            (f"{directory}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_thumbnail(self, path: str, thumbnail: bytes) -> None:
        """
        Update file thumbnail.

        Args:
            path: File path
            thumbnail: Thumbnail image as JPEG bytes
        """
        self.conn.execute(
            "UPDATE files SET thumbnail = ? WHERE path = ?",
            (thumbnail, path)
        )
        self.conn.commit()

    def remove_file(self, path: str) -> None:
        """
        Remove file from database.

        Args:
            path: File path
        """
        self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
        self.conn.commit()

    def get_thumbnail(self, path: str) -> Optional[bytes]:
        """
        Get file thumbnail.

        Args:
            path: File path

        Returns:
            Thumbnail JPEG bytes or None
        """
        cursor = self.conn.execute(
            "SELECT thumbnail FROM files WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()
        return row['thumbnail'] if row else None

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cursor = self.conn.execute("SELECT * FROM cache_stats WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else {}

    def update_cache_stats(self) -> None:
        """Update cache statistics by scanning all thumbnails."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(LENGTH(thumbnail)), 0) as total_size
            FROM files WHERE thumbnail IS NOT NULL
        """)
        row = cursor.fetchone()

        self.conn.execute("""
            UPDATE cache_stats
            SET total_size = ?, file_count = ?
            WHERE id = 1
        """, (row['total_size'], row['count']))
        self.conn.commit()

    def prune_old_thumbnails(self, max_count: int) -> int:
        """
        Remove oldest thumbnails to maintain max count.

        Args:
            max_count: Maximum number of thumbnails to keep

        Returns:
            Number of thumbnails removed
        """
        # Get thumbnails sorted by scan_time (LRU)
        cursor = self.conn.execute("""
            SELECT path FROM files
            WHERE thumbnail IS NOT NULL
            ORDER BY scan_time ASC
        """)
        all_thumbs = [row['path'] for row in cursor.fetchall()]

        if len(all_thumbs) <= max_count:
            return 0

        # Remove oldest thumbnails
        to_remove = all_thumbs[:-max_count]
        self.conn.executemany(
            "UPDATE files SET thumbnail = NULL WHERE path = ?",
            [(path,) for path in to_remove]
        )
        self.conn.execute(
            "UPDATE cache_stats SET last_prune = ? WHERE id = 1",
            (int(time.time()),)
        )
        self.conn.commit()

        return len(to_remove)

    def log_operation(self, operation_type: str, source_path: str,
                     dest_path: str = None, status: str = 'pending',
                     error_message: str = None) -> int:
        """
        Log a file operation.

        Args:
            operation_type: Type of operation (rename, move, copy, delete)
            source_path: Source file path
            dest_path: Destination path (for rename/move/copy)
            status: Operation status
            error_message: Error message if failed

        Returns:
            Operation log ID
        """
        cursor = self.conn.execute("""
            INSERT INTO operation_log
            (timestamp, operation_type, source_path, dest_path, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (int(time.time()), operation_type, source_path, dest_path,
              status, error_message))
        self.conn.commit()
        return cursor.lastrowid

    def update_operation_status(self, operation_id: int, status: str,
                               error_message: str = None) -> None:
        """
        Update operation status.

        Args:
            operation_id: Operation log ID
            status: New status
            error_message: Error message if failed
        """
        self.conn.execute("""
            UPDATE operation_log
            SET status = ?, error_message = ?
            WHERE id = ?
        """, (status, error_message, operation_id))
        self.conn.commit()

    def get_recent_operations(self, limit: int = 100) -> List[Dict]:
        """
        Get recent operations.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of operation dictionaries
        """
        cursor = self.conn.execute("""
            SELECT * FROM operation_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def clear_cache(self) -> None:
        """Clear all cached metadata and thumbnails."""
        self.conn.execute("DELETE FROM files")
        self.conn.execute("""
            UPDATE cache_stats
            SET total_size = 0, file_count = 0, last_prune = 0
            WHERE id = 1
        """)
        self.conn.commit()

    def vacuum(self) -> None:
        """Reclaim unused space in database."""
        self.conn.execute("VACUUM")
