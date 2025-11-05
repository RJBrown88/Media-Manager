"""
File operations module with UNC path optimization.
Handles rename, move, copy operations efficiently over network.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Callable, Optional, Tuple

from .database import Database


class FileOperation:
    """Represents a file operation."""

    def __init__(self, operation_type: str, source: str, destination: str = None):
        self.operation_type = operation_type
        self.source = source
        self.destination = destination
        self.status = 'pending'
        self.error = None
        self.bytes_processed = 0
        self.total_bytes = 0
        self.start_time = None
        self.end_time = None

    def get_progress(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_processed / self.total_bytes) * 100

    def get_speed(self) -> float:
        """Get transfer speed in bytes/second."""
        if not self.start_time:
            return 0.0
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.bytes_processed / elapsed

    def get_eta(self) -> float:
        """Get estimated time to completion in seconds."""
        speed = self.get_speed()
        if speed == 0:
            return 0.0
        remaining = self.total_bytes - self.bytes_processed
        return remaining / speed


class FileOperations:
    """File operations manager with network optimization."""

    def __init__(self, database: Database, config: dict):
        """
        Initialize file operations manager.

        Args:
            database: Database instance
            config: Configuration dictionary
        """
        self.db = database
        self.config = config
        self.chunk_size = config.get('chunk_size', 64 * 1024 * 1024)
        self.bandwidth_limit = config.get('bandwidth_limit', 0)  # 0 = unlimited

    def rename_file(self, source: str, new_name: str) -> Tuple[bool, Optional[str]]:
        """
        Rename file on server (no local copy).

        Args:
            source: Source file path
            new_name: New filename (not full path)

        Returns:
            Tuple of (success, error_message)
        """
        operation_id = self.db.log_operation('rename', source)

        try:
            # Construct destination path
            directory = os.path.dirname(source)
            destination = os.path.join(directory, new_name)

            # Perform rename
            os.rename(source, destination)

            # Update database
            file_data = self.db.get_file(source)
            if file_data:
                self.db.remove_file(source)
                self.db.add_file(
                    path=destination,
                    size=file_data['size'],
                    duration=file_data['duration'],
                    resolution=file_data['resolution'],
                    codec=file_data['codec'],
                    mtime=file_data['mtime'],
                    thumbnail=file_data['thumbnail']
                )

            self.db.update_operation_status(operation_id, 'completed')
            return True, None

        except Exception as e:
            error_msg = str(e)
            self.db.update_operation_status(operation_id, 'failed', error_msg)
            return False, error_msg

    def move_file(self, source: str, destination_dir: str,
                 progress_callback: Callable = None) -> Tuple[bool, Optional[str]]:
        """
        Move file to destination directory.

        Args:
            source: Source file path
            destination_dir: Destination directory
            progress_callback: Optional callback(bytes_processed, total_bytes)

        Returns:
            Tuple of (success, error_message)
        """
        operation_id = self.db.log_operation('move', source, destination_dir)

        try:
            # Get filename
            filename = os.path.basename(source)
            destination = os.path.join(destination_dir, filename)

            # Check if source and destination are on same share
            source_drive = os.path.splitdrive(source)[0]
            dest_drive = os.path.splitdrive(destination)[0]

            if source_drive == dest_drive:
                # Same share - use rename (fast)
                os.rename(source, destination)
            else:
                # Different share - need to copy and delete
                file_size = os.path.getsize(source)
                self._copy_file_chunked(source, destination, file_size, progress_callback)
                os.remove(source)

            # Update database
            file_data = self.db.get_file(source)
            if file_data:
                self.db.remove_file(source)
                self.db.add_file(
                    path=destination,
                    size=file_data['size'],
                    duration=file_data['duration'],
                    resolution=file_data['resolution'],
                    codec=file_data['codec'],
                    mtime=int(time.time()),
                    thumbnail=file_data['thumbnail']
                )

            self.db.update_operation_status(operation_id, 'completed')
            return True, None

        except Exception as e:
            error_msg = str(e)
            self.db.update_operation_status(operation_id, 'failed', error_msg)
            return False, error_msg

    def copy_file(self, source: str, destination_dir: str,
                 progress_callback: Callable = None) -> Tuple[bool, Optional[str]]:
        """
        Copy file to destination directory.

        Args:
            source: Source file path
            destination_dir: Destination directory
            progress_callback: Optional callback(bytes_processed, total_bytes)

        Returns:
            Tuple of (success, error_message)
        """
        operation_id = self.db.log_operation('copy', source, destination_dir)

        try:
            # Get filename
            filename = os.path.basename(source)
            destination = os.path.join(destination_dir, filename)

            # Get file size
            file_size = os.path.getsize(source)

            # Copy file in chunks
            self._copy_file_chunked(source, destination, file_size, progress_callback)

            # Add destination to database
            file_data = self.db.get_file(source)
            if file_data:
                self.db.add_file(
                    path=destination,
                    size=file_data['size'],
                    duration=file_data['duration'],
                    resolution=file_data['resolution'],
                    codec=file_data['codec'],
                    mtime=int(time.time()),
                    thumbnail=file_data['thumbnail']
                )

            self.db.update_operation_status(operation_id, 'completed')
            return True, None

        except Exception as e:
            error_msg = str(e)
            self.db.update_operation_status(operation_id, 'failed', error_msg)
            return False, error_msg

    def delete_file(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete file.

        Args:
            path: File path

        Returns:
            Tuple of (success, error_message)
        """
        operation_id = self.db.log_operation('delete', path)

        try:
            os.remove(path)
            self.db.remove_file(path)
            self.db.update_operation_status(operation_id, 'completed')
            return True, None

        except Exception as e:
            error_msg = str(e)
            self.db.update_operation_status(operation_id, 'failed', error_msg)
            return False, error_msg

    def _copy_file_chunked(self, source: str, destination: str,
                          file_size: int, progress_callback: Callable = None) -> None:
        """
        Copy file in chunks with progress reporting.

        Args:
            source: Source file path
            destination: Destination file path
            file_size: Total file size
            progress_callback: Optional callback(bytes_processed, total_bytes)
        """
        bytes_copied = 0
        start_time = time.time()

        with open(source, 'rb') as src:
            with open(destination, 'wb') as dst:
                while True:
                    # Apply bandwidth limiting if configured
                    if self.bandwidth_limit > 0:
                        elapsed = time.time() - start_time
                        expected_bytes = self.bandwidth_limit * 1024 * 1024 * elapsed
                        if bytes_copied > expected_bytes:
                            sleep_time = (bytes_copied - expected_bytes) / (self.bandwidth_limit * 1024 * 1024)
                            time.sleep(sleep_time)

                    # Read and write chunk
                    chunk = src.read(self.chunk_size)
                    if not chunk:
                        break

                    dst.write(chunk)
                    bytes_copied += len(chunk)

                    # Report progress
                    if progress_callback:
                        progress_callback(bytes_copied, file_size)

    def get_operation_size(self, operation: FileOperation) -> int:
        """
        Get total size for operation.

        Args:
            operation: FileOperation instance

        Returns:
            Size in bytes
        """
        try:
            if operation.operation_type in ('move', 'copy'):
                return os.path.getsize(operation.source)
            return 0
        except OSError:
            return 0

    def validate_destination(self, destination: str) -> Tuple[bool, Optional[str]]:
        """
        Validate destination directory.

        Args:
            destination: Destination directory path

        Returns:
            Tuple of (valid, error_message)
        """
        if not os.path.exists(destination):
            return False, "Destination directory does not exist"

        if not os.path.isdir(destination):
            return False, "Destination is not a directory"

        if not os.access(destination, os.W_OK):
            return False, "No write permission for destination"

        return True, None

    def estimate_operation_time(self, source: str, operation_type: str) -> float:
        """
        Estimate operation time based on file size and network speed.

        Args:
            source: Source file path
            operation_type: Type of operation

        Returns:
            Estimated time in seconds
        """
        try:
            file_size = os.path.getsize(source)

            if operation_type == 'rename':
                return 1.0  # Rename is typically fast

            # Estimate based on bandwidth limit or assume 100 MB/s
            speed = self.bandwidth_limit if self.bandwidth_limit > 0 else 100
            return file_size / (speed * 1024 * 1024)

        except OSError:
            return 0.0

    def can_fast_move(self, source: str, destination_dir: str) -> bool:
        """
        Check if fast move (rename) is possible.

        Args:
            source: Source file path
            destination_dir: Destination directory

        Returns:
            True if fast move is possible (same drive/share)
        """
        source_drive = os.path.splitdrive(source)[0]
        dest_drive = os.path.splitdrive(destination_dir)[0]
        return source_drive == dest_drive
