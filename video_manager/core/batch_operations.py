"""
Batch operations with dry-run and undo capabilities.
Processes multiple file operations sequentially with logging.
"""

import time
from queue import Queue
from typing import Callable, List, Optional, Tuple

from .database import Database
from .file_operations import FileOperations, FileOperation


class BatchOperation:
    """Represents a batch of file operations."""

    def __init__(self, operations: List[FileOperation]):
        self.operations = operations
        self.current_index = 0
        self.status = 'pending'
        self.start_time = None
        self.end_time = None
        self.completed_operations = []
        self.failed_operations = []
        self.dry_run_results = []

    def get_total_size(self) -> int:
        """Get total size of all operations."""
        return sum(op.total_bytes for op in self.operations)

    def get_progress(self) -> float:
        """Get overall progress as percentage."""
        if not self.operations:
            return 100.0
        return (len(self.completed_operations) / len(self.operations)) * 100

    def get_eta(self) -> float:
        """Get estimated time to completion."""
        if not self.start_time or not self.completed_operations:
            return 0.0

        elapsed = time.time() - self.start_time
        avg_time_per_op = elapsed / len(self.completed_operations)
        remaining_ops = len(self.operations) - len(self.completed_operations)
        return avg_time_per_op * remaining_ops


class BatchOperations:
    """Batch operations manager with dry-run and undo support."""

    def __init__(self, file_operations: FileOperations, database: Database, config: dict):
        """
        Initialize batch operations manager.

        Args:
            file_operations: FileOperations instance
            database: Database instance
            config: Configuration dictionary
        """
        self.file_ops = file_operations
        self.db = database
        self.config = config
        self._cancel_flag = False
        self._pause_flag = False

    def dry_run(self, operations: List[FileOperation]) -> List[dict]:
        """
        Perform dry run of operations (validation only).

        Args:
            operations: List of FileOperation instances

        Returns:
            List of dry run results
        """
        results = []

        for op in operations:
            result = {
                'operation': op.operation_type,
                'source': op.source,
                'destination': op.destination,
                'valid': True,
                'warnings': [],
                'errors': [],
                'estimated_time': 0.0,
                'size': 0,
            }

            # Validate source exists
            try:
                import os
                if not os.path.exists(op.source):
                    result['valid'] = False
                    result['errors'].append('Source file does not exist')
                else:
                    result['size'] = os.path.getsize(op.source)
                    result['estimated_time'] = self.file_ops.estimate_operation_time(
                        op.source, op.operation_type
                    )

                # Validate destination if applicable
                if op.destination:
                    if op.operation_type in ('move', 'copy'):
                        valid, error = self.file_ops.validate_destination(op.destination)
                        if not valid:
                            result['valid'] = False
                            result['errors'].append(error)

                        # Check if file already exists at destination
                        dest_file = os.path.join(op.destination, os.path.basename(op.source))
                        if os.path.exists(dest_file):
                            result['warnings'].append('File already exists at destination')

                    elif op.operation_type == 'rename':
                        # Check if target name already exists
                        if os.path.exists(op.destination):
                            result['warnings'].append('Target filename already exists')

                # Check available space for copy operations
                if op.operation_type == 'copy' and result['valid']:
                    try:
                        stat = os.statvfs(op.destination) if hasattr(os, 'statvfs') else None
                        if stat:
                            available_space = stat.f_bavail * stat.f_frsize
                            if result['size'] > available_space:
                                result['valid'] = False
                                result['errors'].append('Insufficient space at destination')
                    except:
                        result['warnings'].append('Could not check available space')

            except Exception as e:
                result['valid'] = False
                result['errors'].append(str(e))

            results.append(result)

        return results

    def execute_batch(self, operations: List[FileOperation],
                     progress_callback: Callable = None) -> BatchOperation:
        """
        Execute batch operations sequentially.

        Args:
            operations: List of FileOperation instances
            progress_callback: Optional callback(completed, total, current_op)

        Returns:
            BatchOperation result
        """
        batch = BatchOperation(operations)
        batch.status = 'running'
        batch.start_time = time.time()
        self._cancel_flag = False

        for i, op in enumerate(operations):
            if self._cancel_flag:
                batch.status = 'cancelled'
                break

            # Wait if paused
            while self._pause_flag and not self._cancel_flag:
                time.sleep(0.1)

            # Update progress
            batch.current_index = i
            if progress_callback:
                progress_callback(i, len(operations), op)

            # Execute operation
            success, error = self._execute_operation(op, progress_callback)

            if success:
                batch.completed_operations.append(op)
            else:
                op.error = error
                batch.failed_operations.append(op)

        batch.end_time = time.time()
        if batch.status == 'running':
            batch.status = 'completed'

        return batch

    def _execute_operation(self, operation: FileOperation,
                          progress_callback: Callable = None) -> Tuple[bool, Optional[str]]:
        """
        Execute single operation.

        Args:
            operation: FileOperation instance
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, error_message)
        """
        operation.start_time = time.time()
        operation.status = 'running'

        try:
            if operation.operation_type == 'rename':
                success, error = self.file_ops.rename_file(
                    operation.source,
                    os.path.basename(operation.destination)
                )

            elif operation.operation_type == 'move':
                success, error = self.file_ops.move_file(
                    operation.source,
                    operation.destination,
                    progress_callback
                )

            elif operation.operation_type == 'copy':
                success, error = self.file_ops.copy_file(
                    operation.source,
                    operation.destination,
                    progress_callback
                )

            elif operation.operation_type == 'delete':
                success, error = self.file_ops.delete_file(operation.source)

            else:
                success = False
                error = f"Unknown operation type: {operation.operation_type}"

            operation.end_time = time.time()
            operation.status = 'completed' if success else 'failed'
            operation.error = error

            return success, error

        except Exception as e:
            operation.end_time = time.time()
            operation.status = 'failed'
            operation.error = str(e)
            return False, str(e)

    def generate_undo_operations(self, batch: BatchOperation) -> List[FileOperation]:
        """
        Generate undo operations for completed batch.

        Args:
            batch: Completed BatchOperation

        Returns:
            List of FileOperation instances to undo
        """
        undo_ops = []

        # Reverse order for undo
        for op in reversed(batch.completed_operations):
            if op.operation_type == 'rename':
                # Undo rename: rename back to original
                undo_op = FileOperation('rename', op.destination, op.source)
                undo_ops.append(undo_op)

            elif op.operation_type == 'move':
                # Undo move: move back to original location
                undo_op = FileOperation(
                    'move',
                    os.path.join(op.destination, os.path.basename(op.source)),
                    os.path.dirname(op.source)
                )
                undo_ops.append(undo_op)

            elif op.operation_type == 'copy':
                # Undo copy: delete the copy
                undo_op = FileOperation(
                    'delete',
                    os.path.join(op.destination, os.path.basename(op.source))
                )
                undo_ops.append(undo_op)

            # Note: delete operations cannot be undone without backup

        return undo_ops

    def create_rename_batch(self, files: List[str], name_pattern: str) -> List[FileOperation]:
        """
        Create batch rename operations.

        Args:
            files: List of file paths
            name_pattern: Pattern for new names (can use {i}, {name}, {ext})

        Returns:
            List of FileOperation instances
        """
        import os
        operations = []

        for i, file_path in enumerate(files):
            directory = os.path.dirname(file_path)
            old_name = os.path.basename(file_path)
            name_without_ext, ext = os.path.splitext(old_name)

            # Format new name
            new_name = name_pattern.format(
                i=i + 1,
                name=name_without_ext,
                ext=ext[1:] if ext else ''
            )

            # Ensure extension is preserved if not in pattern
            if not new_name.endswith(ext):
                new_name += ext

            new_path = os.path.join(directory, new_name)
            operations.append(FileOperation('rename', file_path, new_path))

        return operations

    def create_move_batch(self, files: List[str], destination_dir: str) -> List[FileOperation]:
        """
        Create batch move operations.

        Args:
            files: List of file paths
            destination_dir: Destination directory

        Returns:
            List of FileOperation instances
        """
        return [FileOperation('move', f, destination_dir) for f in files]

    def create_copy_batch(self, files: List[str], destination_dir: str) -> List[FileOperation]:
        """
        Create batch copy operations.

        Args:
            files: List of file paths
            destination_dir: Destination directory

        Returns:
            List of FileOperation instances
        """
        return [FileOperation('copy', f, destination_dir) for f in files]

    def cancel(self) -> None:
        """Cancel ongoing batch operation."""
        self._cancel_flag = True

    def pause(self) -> None:
        """Pause ongoing batch operation."""
        self._pause_flag = True

    def resume(self) -> None:
        """Resume paused batch operation."""
        self._pause_flag = False

    def get_summary(self, batch: BatchOperation) -> dict:
        """
        Get summary of batch operation.

        Args:
            batch: BatchOperation instance

        Returns:
            Summary dictionary
        """
        return {
            'total_operations': len(batch.operations),
            'completed': len(batch.completed_operations),
            'failed': len(batch.failed_operations),
            'progress': batch.get_progress(),
            'status': batch.status,
            'duration': batch.end_time - batch.start_time if batch.end_time else 0,
            'total_size': batch.get_total_size(),
        }
