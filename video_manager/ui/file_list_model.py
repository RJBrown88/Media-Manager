"""
Virtual scrolling model for efficient large file list display.
Uses QAbstractTableModel with lazy loading.
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QPixmap, QIcon
from typing import List, Optional
import os


class FileListModel(QAbstractTableModel):
    """Table model for video file list with virtual scrolling."""

    # Column definitions
    COL_NAME = 0
    COL_SIZE = 1
    COL_DURATION = 2
    COL_RESOLUTION = 3
    COL_CODEC = 4
    COL_CACHED = 5

    HEADERS = ['Name', 'Size', 'Duration', 'Resolution', 'Codec', 'Cached']

    def __init__(self, database, parent=None):
        """
        Initialize file list model.

        Args:
            database: Database instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self.db = database
        self.files = []
        self.page_size = 50
        self.current_page = 0
        self.total_files = 0
        self._thumbnail_cache = {}

    def load_files(self, directory: str = None) -> None:
        """
        Load files from database.

        Args:
            directory: Optional directory to filter by
        """
        self.beginResetModel()

        if directory:
            self.files = self.db.get_files_by_directory(directory)
        else:
            self.files = self.db.get_files()

        self.total_files = len(self.files)
        self.current_page = 0
        self._thumbnail_cache.clear()

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        """Get number of rows."""
        if parent.isValid():
            return 0
        return len(self.files)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Get number of columns."""
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """
        Get data for cell.

        Args:
            index: Cell index
            role: Data role

        Returns:
            Cell data
        """
        if not index.isValid() or index.row() >= len(self.files):
            return QVariant()

        file_data = self.files[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == self.COL_NAME:
                return os.path.basename(file_data['path'])
            elif col == self.COL_SIZE:
                return self._format_size(file_data['size'])
            elif col == self.COL_DURATION:
                return self._format_duration(file_data.get('duration'))
            elif col == self.COL_RESOLUTION:
                return file_data.get('resolution', 'Unknown')
            elif col == self.COL_CODEC:
                return file_data.get('codec', 'Unknown')
            elif col == self.COL_CACHED:
                return 'Yes' if file_data.get('thumbnail') else 'No'

        elif role == Qt.ToolTipRole:
            if col == self.COL_NAME:
                return file_data['path']

        elif role == Qt.DecorationRole:
            if col == self.COL_NAME:
                # Return thumbnail icon if available
                path = file_data['path']
                if path in self._thumbnail_cache:
                    return self._thumbnail_cache[path]
                elif file_data.get('thumbnail'):
                    # Load thumbnail from database
                    pixmap = QPixmap()
                    if pixmap.loadFromData(file_data['thumbnail']):
                        icon = QIcon(pixmap)
                        self._thumbnail_cache[path] = icon
                        return icon

        elif role == Qt.UserRole:
            # Return full file data for custom use
            return file_data

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        """
        Get header data.

        Args:
            section: Column/row index
            orientation: Horizontal or vertical
            role: Data role

        Returns:
            Header data
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return QVariant()

    def get_file_at_row(self, row: int) -> Optional[dict]:
        """
        Get file data at row.

        Args:
            row: Row index

        Returns:
            File data dictionary or None
        """
        if 0 <= row < len(self.files):
            return self.files[row]
        return None

    def get_file_path(self, row: int) -> Optional[str]:
        """
        Get file path at row.

        Args:
            row: Row index

        Returns:
            File path or None
        """
        file_data = self.get_file_at_row(row)
        return file_data['path'] if file_data else None

    def update_file(self, path: str) -> None:
        """
        Update file in model.

        Args:
            path: File path to update
        """
        # Find file in list
        for i, file_data in enumerate(self.files):
            if file_data['path'] == path:
                # Reload from database
                updated_data = self.db.get_file(path)
                if updated_data:
                    self.files[i] = updated_data
                    # Emit data changed
                    top_left = self.index(i, 0)
                    bottom_right = self.index(i, self.columnCount() - 1)
                    self.dataChanged.emit(top_left, bottom_right)
                    # Clear thumbnail cache for this file
                    if path in self._thumbnail_cache:
                        del self._thumbnail_cache[path]
                break

    def remove_file(self, path: str) -> None:
        """
        Remove file from model.

        Args:
            path: File path to remove
        """
        for i, file_data in enumerate(self.files):
            if file_data['path'] == path:
                self.beginRemoveRows(QModelIndex(), i, i)
                del self.files[i]
                self.endRemoveRows()
                if path in self._thumbnail_cache:
                    del self._thumbnail_cache[path]
                break

    def clear(self) -> None:
        """Clear all files from model."""
        self.beginResetModel()
        self.files = []
        self._thumbnail_cache.clear()
        self.endResetModel()

    def sort(self, column: int, order=Qt.AscendingOrder) -> None:
        """
        Sort files by column.

        Args:
            column: Column to sort by
            order: Sort order
        """
        self.layoutAboutToBeChanged.emit()

        reverse = (order == Qt.DescendingOrder)

        if column == self.COL_NAME:
            self.files.sort(key=lambda f: os.path.basename(f['path']), reverse=reverse)
        elif column == self.COL_SIZE:
            self.files.sort(key=lambda f: f.get('size', 0), reverse=reverse)
        elif column == self.COL_DURATION:
            self.files.sort(key=lambda f: f.get('duration', 0) or 0, reverse=reverse)
        elif column == self.COL_RESOLUTION:
            self.files.sort(key=lambda f: f.get('resolution', ''), reverse=reverse)
        elif column == self.COL_CODEC:
            self.files.sort(key=lambda f: f.get('codec', ''), reverse=reverse)
        elif column == self.COL_CACHED:
            self.files.sort(key=lambda f: bool(f.get('thumbnail')), reverse=reverse)

        self.layoutChanged.emit()

    @staticmethod
    def _format_size(size: int) -> str:
        """
        Format file size for display.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        if size is None:
            return 'Unknown'

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @staticmethod
    def _format_duration(duration: float) -> str:
        """
        Format duration for display.

        Args:
            duration: Duration in seconds

        Returns:
            Formatted duration string (HH:MM:SS)
        """
        if duration is None or duration <= 0:
            return 'Unknown'

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def refresh_thumbnails(self) -> None:
        """Refresh all thumbnails from database."""
        self._thumbnail_cache.clear()
        if self.files:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self.files) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right)
