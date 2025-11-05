"""
Metadata panel for displaying video file information.
Populated on-demand when file is selected.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QGroupBox
)
import os
from datetime import datetime


class MetadataPanel(QWidget):
    """Panel for displaying video metadata."""

    def __init__(self, parent=None):
        """
        Initialize metadata panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Scroll area for metadata
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Content widget
        content = QWidget()
        content_layout = QVBoxLayout()

        # Thumbnail display
        thumbnail_group = QGroupBox("Thumbnail")
        thumbnail_layout = QVBoxLayout()
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setMinimumSize(320, 180)
        self.thumbnail_label.setStyleSheet("border: 1px solid #ccc; background: #000;")
        thumbnail_layout.addWidget(self.thumbnail_label)
        thumbnail_group.setLayout(thumbnail_layout)
        content_layout.addWidget(thumbnail_group)

        # File information
        file_info_group = QGroupBox("File Information")
        file_info_layout = QGridLayout()

        row = 0
        self.labels = {}

        # Filename
        file_info_layout.addWidget(QLabel("<b>Filename:</b>"), row, 0)
        self.labels['filename'] = QLabel("-")
        self.labels['filename'].setWordWrap(True)
        file_info_layout.addWidget(self.labels['filename'], row, 1)
        row += 1

        # Path
        file_info_layout.addWidget(QLabel("<b>Path:</b>"), row, 0)
        self.labels['path'] = QLabel("-")
        self.labels['path'].setWordWrap(True)
        self.labels['path'].setTextInteractionFlags(Qt.TextSelectableByMouse)
        file_info_layout.addWidget(self.labels['path'], row, 1)
        row += 1

        # Size
        file_info_layout.addWidget(QLabel("<b>Size:</b>"), row, 0)
        self.labels['size'] = QLabel("-")
        file_info_layout.addWidget(self.labels['size'], row, 1)
        row += 1

        # Modified time
        file_info_layout.addWidget(QLabel("<b>Modified:</b>"), row, 0)
        self.labels['mtime'] = QLabel("-")
        file_info_layout.addWidget(self.labels['mtime'], row, 1)
        row += 1

        file_info_group.setLayout(file_info_layout)
        content_layout.addWidget(file_info_group)

        # Video information
        video_info_group = QGroupBox("Video Information")
        video_info_layout = QGridLayout()

        row = 0

        # Duration
        video_info_layout.addWidget(QLabel("<b>Duration:</b>"), row, 0)
        self.labels['duration'] = QLabel("-")
        video_info_layout.addWidget(self.labels['duration'], row, 1)
        row += 1

        # Resolution
        video_info_layout.addWidget(QLabel("<b>Resolution:</b>"), row, 0)
        self.labels['resolution'] = QLabel("-")
        video_info_layout.addWidget(self.labels['resolution'], row, 1)
        row += 1

        # Codec
        video_info_layout.addWidget(QLabel("<b>Codec:</b>"), row, 0)
        self.labels['codec'] = QLabel("-")
        video_info_layout.addWidget(self.labels['codec'], row, 1)
        row += 1

        # Format
        video_info_layout.addWidget(QLabel("<b>Format:</b>"), row, 0)
        self.labels['format'] = QLabel("-")
        video_info_layout.addWidget(self.labels['format'], row, 1)
        row += 1

        video_info_group.setLayout(video_info_layout)
        content_layout.addWidget(video_info_group)

        # Cache information
        cache_info_group = QGroupBox("Cache Information")
        cache_info_layout = QGridLayout()

        row = 0

        # Cached status
        cache_info_layout.addWidget(QLabel("<b>Metadata Cached:</b>"), row, 0)
        self.labels['cached'] = QLabel("-")
        cache_info_layout.addWidget(self.labels['cached'], row, 1)
        row += 1

        # Scan time
        cache_info_layout.addWidget(QLabel("<b>Last Scanned:</b>"), row, 0)
        self.labels['scan_time'] = QLabel("-")
        cache_info_layout.addWidget(self.labels['scan_time'], row, 1)
        row += 1

        cache_info_group.setLayout(cache_info_layout)
        content_layout.addWidget(cache_info_group)

        # Add stretch at bottom
        content_layout.addStretch()

        content.setLayout(content_layout)
        scroll.setWidget(content)

        layout.addWidget(scroll)
        self.setLayout(layout)

    def display_metadata(self, file_data: dict) -> None:
        """
        Display metadata for file.

        Args:
            file_data: File metadata dictionary from database
        """
        if not file_data:
            self.clear()
            return

        # Filename
        self.labels['filename'].setText(os.path.basename(file_data['path']))

        # Path
        self.labels['path'].setText(file_data['path'])

        # Size
        size_str = self._format_size(file_data.get('size', 0))
        self.labels['size'].setText(size_str)

        # Modified time
        mtime = file_data.get('mtime')
        if mtime:
            dt = datetime.fromtimestamp(mtime)
            self.labels['mtime'].setText(dt.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            self.labels['mtime'].setText('-')

        # Duration
        duration = file_data.get('duration')
        if duration:
            self.labels['duration'].setText(self._format_duration(duration))
        else:
            self.labels['duration'].setText('-')

        # Resolution
        self.labels['resolution'].setText(file_data.get('resolution', '-'))

        # Codec
        self.labels['codec'].setText(file_data.get('codec', '-'))

        # Format
        _, ext = os.path.splitext(file_data['path'])
        self.labels['format'].setText(ext.upper()[1:] if ext else '-')

        # Cached status
        has_metadata = bool(file_data.get('duration'))
        self.labels['cached'].setText('Yes' if has_metadata else 'No')

        # Scan time
        scan_time = file_data.get('scan_time')
        if scan_time:
            dt = datetime.fromtimestamp(scan_time)
            self.labels['scan_time'].setText(dt.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            self.labels['scan_time'].setText('-')

        # Thumbnail
        thumbnail = file_data.get('thumbnail')
        if thumbnail:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumbnail):
                # Scale to fit label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.thumbnail_label.width() - 20,
                    self.thumbnail_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
            else:
                self.thumbnail_label.setText("Thumbnail load error")
        else:
            self.thumbnail_label.setText("No thumbnail")

    def clear(self) -> None:
        """Clear all metadata fields."""
        for label in self.labels.values():
            label.setText("-")
        self.thumbnail_label.clear()
        self.thumbnail_label.setText("No file selected")

    @staticmethod
    def _format_size(size: int) -> str:
        """
        Format file size for display.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        if size is None or size == 0:
            return '0 B'

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    @staticmethod
    def _format_duration(duration: float) -> str:
        """
        Format duration for display.

        Args:
            duration: Duration in seconds

        Returns:
            Formatted duration string
        """
        if duration is None or duration <= 0:
            return '-'

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
