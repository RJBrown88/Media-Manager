"""
Progressive file scanner with async metadata enrichment.
Optimized for network shares with cancellation support.
"""

import os
import threading
import time
from queue import Queue, Empty
from typing import Callable, List, Optional

from .database import Database
from .metadata_extractor import MetadataExtractor
from .thumbnail_generator import ThumbnailGenerator


class ScanResult:
    """Result of a file scan operation."""

    def __init__(self):
        self.files_found = 0
        self.files_processed = 0
        self.errors = []
        self.cancelled = False
        self.completed = False
        self.start_time = time.time()
        self.end_time = None

    def duration(self) -> float:
        """Get scan duration in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time


class FileScanner:
    """Progressive file scanner with background metadata enrichment."""

    def __init__(self, database: Database, metadata_extractor: MetadataExtractor,
                 thumbnail_generator: ThumbnailGenerator, config: dict):
        """
        Initialize file scanner.

        Args:
            database: Database instance
            metadata_extractor: MetadataExtractor instance
            thumbnail_generator: ThumbnailGenerator instance
            config: Configuration dictionary
        """
        self.db = database
        self.metadata_extractor = metadata_extractor
        self.thumbnail_generator = thumbnail_generator
        self.config = config

        self.batch_size = config.get('scan_batch_size', 50)
        self.deep_scan_threshold = config.get('deep_scan_threshold', 5 * 1024**3)
        self.max_parallel = config.get('max_parallel_metadata', 3)

        self._cancel_flag = False
        self._pause_flag = False
        self._scan_thread = None
        self._metadata_threads = []
        self._metadata_queue = Queue()

    def scan_directory(self, directory: str,
                      progress_callback: Callable = None,
                      generate_thumbnails: bool = False) -> ScanResult:
        """
        Scan directory progressively.

        Args:
            directory: Directory path to scan
            progress_callback: Optional callback(files_found, files_processed)
            generate_thumbnails: Whether to generate thumbnails during scan

        Returns:
            ScanResult object
        """
        result = ScanResult()
        self._cancel_flag = False

        try:
            # Phase 1: Quick directory listing
            files = self._list_files(directory)
            result.files_found = len(files)

            if progress_callback:
                progress_callback(result.files_found, 0)

            # Phase 2: Add basic file info to database
            for i, file_path in enumerate(files):
                if self._cancel_flag:
                    result.cancelled = True
                    break

                try:
                    stat = os.stat(file_path)
                    self.db.add_file(
                        path=file_path,
                        size=stat.st_size,
                        mtime=int(stat.st_mtime)
                    )
                    result.files_processed += 1

                    # Queue for metadata extraction
                    self._metadata_queue.put((file_path, generate_thumbnails))

                    if progress_callback and i % 10 == 0:
                        progress_callback(result.files_found, result.files_processed)

                except (OSError, IOError) as e:
                    result.errors.append((file_path, str(e)))

            # Phase 3: Start background metadata enrichment
            self._start_metadata_workers(progress_callback)

            if not result.cancelled:
                result.completed = True

        except Exception as e:
            result.errors.append((directory, str(e)))

        result.end_time = time.time()
        return result

    def _list_files(self, directory: str) -> List[str]:
        """
        List all video files in directory.

        Args:
            directory: Directory path

        Returns:
            List of file paths
        """
        video_files = []

        try:
            # Use os.scandir for better performance on network shares
            with os.scandir(directory) as entries:
                for entry in entries:
                    if self._cancel_flag:
                        break

                    try:
                        if entry.is_file() and self.metadata_extractor.is_video_file(entry.name):
                            video_files.append(entry.path)
                    except OSError:
                        # Skip files we can't access
                        pass

        except (OSError, IOError) as e:
            print(f"Error listing directory {directory}: {e}")

        return video_files

    def _start_metadata_workers(self, progress_callback: Callable = None) -> None:
        """
        Start background workers for metadata extraction.

        Args:
            progress_callback: Optional progress callback
        """
        # Clear old threads
        self._metadata_threads = []

        # Start worker threads
        for i in range(self.max_parallel):
            thread = threading.Thread(
                target=self._metadata_worker,
                args=(progress_callback,),
                daemon=True
            )
            thread.start()
            self._metadata_threads.append(thread)

    def _metadata_worker(self, progress_callback: Callable = None) -> None:
        """
        Worker thread for extracting metadata.

        Args:
            progress_callback: Optional progress callback
        """
        while not self._cancel_flag:
            try:
                # Get file from queue with timeout
                file_path, generate_thumb = self._metadata_queue.get(timeout=1)

                # Wait if paused
                while self._pause_flag and not self._cancel_flag:
                    time.sleep(0.1)

                if self._cancel_flag:
                    break

                try:
                    # Extract metadata
                    file_size = self.db.get_file(file_path).get('size', 0)
                    deep_scan = file_size < self.deep_scan_threshold

                    metadata = self.metadata_extractor.extract_metadata(
                        file_path,
                        deep_scan=deep_scan
                    )

                    if metadata:
                        # Update database with metadata
                        self.db.add_file(
                            path=file_path,
                            size=metadata.get('size', 0),
                            duration=metadata.get('duration'),
                            resolution=metadata.get('resolution'),
                            codec=metadata.get('codec'),
                            mtime=os.path.getmtime(file_path)
                        )

                        # Generate thumbnail if requested
                        if generate_thumb:
                            thumbnail = self.thumbnail_generator.generate_thumbnail(file_path)
                            if thumbnail:
                                self.db.update_thumbnail(file_path, thumbnail)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

                self._metadata_queue.task_done()

            except Empty:
                # Queue is empty, exit worker
                break

    def scan_file(self, file_path: str, deep_scan: bool = False,
                 generate_thumbnail: bool = False) -> bool:
        """
        Scan single file and update database.

        Args:
            file_path: Path to file
            deep_scan: Whether to perform deep scan
            generate_thumbnail: Whether to generate thumbnail

        Returns:
            True if successful
        """
        try:
            # Get file info
            stat = os.stat(file_path)

            # Extract metadata
            metadata = self.metadata_extractor.extract_metadata(
                file_path,
                deep_scan=deep_scan
            )

            if not metadata:
                return False

            # Add to database
            self.db.add_file(
                path=file_path,
                size=metadata.get('size', stat.st_size),
                duration=metadata.get('duration'),
                resolution=metadata.get('resolution'),
                codec=metadata.get('codec'),
                mtime=int(stat.st_mtime)
            )

            # Generate thumbnail if requested
            if generate_thumbnail:
                thumbnail = self.thumbnail_generator.generate_thumbnail(file_path)
                if thumbnail:
                    self.db.update_thumbnail(file_path, thumbnail)

            return True

        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
            return False

    def rescan_directory(self, directory: str) -> ScanResult:
        """
        Rescan directory and update changed files.

        Args:
            directory: Directory path

        Returns:
            ScanResult object
        """
        result = ScanResult()
        self._cancel_flag = False

        try:
            # Get current files from database
            db_files = {f['path']: f for f in self.db.get_files_by_directory(directory)}

            # Scan directory
            current_files = set(self._list_files(directory))
            result.files_found = len(current_files)

            # Find new and modified files
            for file_path in current_files:
                if self._cancel_flag:
                    result.cancelled = True
                    break

                try:
                    stat = os.stat(file_path)
                    db_file = db_files.get(file_path)

                    # Check if new or modified
                    if not db_file or db_file['mtime'] != int(stat.st_mtime):
                        self.scan_file(file_path, deep_scan=False, generate_thumbnail=False)

                    result.files_processed += 1

                except (OSError, IOError) as e:
                    result.errors.append((file_path, str(e)))

            # Remove deleted files from database
            for db_path in db_files:
                if db_path not in current_files:
                    self.db.remove_file(db_path)

            if not result.cancelled:
                result.completed = True

        except Exception as e:
            result.errors.append((directory, str(e)))

        result.end_time = time.time()
        return result

    def cancel_scan(self) -> None:
        """Cancel ongoing scan."""
        self._cancel_flag = True

    def pause_scan(self) -> None:
        """Pause ongoing scan."""
        self._pause_flag = True

    def resume_scan(self) -> None:
        """Resume paused scan."""
        self._pause_flag = False

    def is_scanning(self) -> bool:
        """Check if scan is in progress."""
        return any(t.is_alive() for t in self._metadata_threads)

    def wait_for_completion(self, timeout: float = None) -> bool:
        """
        Wait for scan to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if completed, False if timeout
        """
        start = time.time()
        while self.is_scanning():
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.1)
        return True
