"""
Main window for Video Manager application.
Integrates file list, preview, metadata panel, and operations queue.
"""

import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTableView, QPushButton, QLineEdit,
    QLabel, QFileDialog, QMessageBox, QMenuBar,
    QMenu, QAction, QStatusBar, QProgressBar, QToolBar
)

from .file_list_model import FileListModel
from .video_preview import VideoPreviewWidget
from .metadata_panel import MetadataPanel
from .operations_queue import OperationsQueueWidget
from .settings_dialog import SettingsDialog


class ScanThread(QThread):
    """Background thread for scanning directories."""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(object)

    def __init__(self, scanner, directory, generate_thumbnails=False):
        super().__init__()
        self.scanner = scanner
        self.directory = directory
        self.generate_thumbnails = generate_thumbnails

    def run(self):
        result = self.scanner.scan_directory(
            self.directory,
            progress_callback=self.progress.emit,
            generate_thumbnails=self.generate_thumbnails
        )
        self.finished.emit(result)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config, database, cache_manager, metadata_extractor,
                 thumbnail_generator, file_scanner, file_operations, batch_operations):
        """
        Initialize main window.

        Args:
            config: Config instance
            database: Database instance
            cache_manager: CacheManager instance
            metadata_extractor: MetadataExtractor instance
            thumbnail_generator: ThumbnailGenerator instance
            file_scanner: FileScanner instance
            file_operations: FileOperations instance
            batch_operations: BatchOperations instance
        """
        super().__init__()
        self.config = config
        self.db = database
        self.cache_manager = cache_manager
        self.metadata_extractor = metadata_extractor
        self.thumbnail_generator = thumbnail_generator
        self.file_scanner = file_scanner
        self.file_operations = file_operations
        self.batch_operations = batch_operations

        self.current_directory = None
        self.scan_thread = None

        self.setWindowTitle("Video Manager")
        self.resize(1400, 900)

        self.init_ui()
        self.restore_geometry()

    def init_ui(self) -> None:
        """Initialize UI components."""
        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directory:"))

        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Enter UNC path (e.g., \\\\server\\share\\videos)")
        dir_layout.addWidget(self.dir_edit)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_button)

        scan_button = QPushButton("Scan")
        scan_button.clicked.connect(self.scan_directory)
        dir_layout.addWidget(scan_button)

        main_layout.addLayout(dir_layout)

        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel: File list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        # File list
        self.file_model = FileListModel(self.db)
        self.file_table = QTableView()
        self.file_table.setModel(self.file_model)
        self.file_table.setSortingEnabled(True)
        self.file_table.setSelectionBehavior(QTableView.SelectRows)
        self.file_table.setSelectionMode(QTableView.SingleSelection)
        self.file_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.file_table.doubleClicked.connect(self.on_file_double_clicked)

        # Resize columns
        self.file_table.setColumnWidth(0, 300)  # Name
        self.file_table.setColumnWidth(1, 100)  # Size
        self.file_table.setColumnWidth(2, 100)  # Duration

        left_layout.addWidget(self.file_table)

        # File operations buttons
        ops_layout = QHBoxLayout()

        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self.rename_selected)
        ops_layout.addWidget(rename_button)

        move_button = QPushButton("Move")
        move_button.clicked.connect(self.move_selected)
        ops_layout.addWidget(move_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_selected)
        ops_layout.addWidget(delete_button)

        ops_layout.addStretch()

        generate_thumb_button = QPushButton("Generate Thumbnail")
        generate_thumb_button.clicked.connect(self.generate_thumbnail_for_selected)
        ops_layout.addWidget(generate_thumb_button)

        left_layout.addLayout(ops_layout)

        left_panel.setLayout(left_layout)
        main_splitter.addWidget(left_panel)

        # Right panel: Preview and metadata
        right_splitter = QSplitter(Qt.Vertical)

        # Video preview
        self.preview_widget = VideoPreviewWidget()
        self.preview_widget.errorOccurred.connect(self.on_preview_error)
        right_splitter.addWidget(self.preview_widget)

        # Metadata panel
        self.metadata_panel = MetadataPanel()
        right_splitter.addWidget(self.metadata_panel)

        # Operations queue
        self.operations_queue = OperationsQueueWidget()
        right_splitter.addWidget(self.operations_queue)

        right_splitter.setSizes([400, 300, 200])

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([700, 700])

        main_layout.addWidget(main_splitter)

        central_widget.setLayout(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.update_status()

    def create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        scan_action = QAction("Scan Directory...", self)
        scan_action.triggered.connect(self.scan_directory)
        file_menu.addAction(scan_action)

        rescan_action = QAction("Rescan Directory", self)
        rescan_action.triggered.connect(self.rescan_directory)
        file_menu.addAction(rescan_action)

        file_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Cache menu
        cache_menu = menubar.addMenu("Cache")

        cache_stats_action = QAction("Cache Statistics...", self)
        cache_stats_action.triggered.connect(self.show_cache_stats)
        cache_menu.addAction(cache_stats_action)

        prune_cache_action = QAction("Prune Cache", self)
        prune_cache_action.triggered.connect(self.prune_cache)
        cache_menu.addAction(prune_cache_action)

        clear_cache_action = QAction("Clear Cache...", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        cache_menu.addAction(clear_cache_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self) -> None:
        """Create toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_file_list)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        cancel_scan_action = QAction("Cancel Scan", self)
        cancel_scan_action.triggered.connect(self.cancel_scan)
        toolbar.addAction(cancel_scan_action)

    def browse_directory(self) -> None:
        """Browse for directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Video Directory",
            self.dir_edit.text()
        )
        if directory:
            self.dir_edit.setText(directory)

    def scan_directory(self) -> None:
        """Scan selected directory."""
        directory = self.dir_edit.text()

        if not directory:
            QMessageBox.warning(self, "No Directory", "Please select a directory to scan.")
            return

        if not os.path.exists(directory):
            QMessageBox.warning(self, "Invalid Directory", "The selected directory does not exist.")
            return

        # Ask about thumbnail generation
        reply = QMessageBox.question(
            self,
            'Generate Thumbnails',
            'Do you want to generate thumbnails during scan? (This will take longer)',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        generate_thumbnails = (reply == QMessageBox.Yes)

        self.current_directory = directory
        self.config.add_recent_directory(directory)

        # Start scan in background thread
        self.scan_thread = ScanThread(
            self.file_scanner,
            directory,
            generate_thumbnails
        )
        self.scan_thread.progress.connect(self.on_scan_progress)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()

        self.progress_bar.setVisible(True)
        self.status_bar.showMessage("Scanning directory...")

    def rescan_directory(self) -> None:
        """Rescan current directory."""
        if not self.current_directory:
            QMessageBox.warning(self, "No Directory", "No directory to rescan.")
            return

        result = self.file_scanner.rescan_directory(self.current_directory)
        self.file_model.load_files(self.current_directory)
        self.update_status()

        QMessageBox.information(
            self,
            "Rescan Complete",
            f"Rescan completed.\nFiles found: {result.files_found}\nFiles updated: {result.files_processed}"
        )

    def cancel_scan(self) -> None:
        """Cancel ongoing scan."""
        self.file_scanner.cancel_scan()
        if self.scan_thread:
            self.scan_thread.wait()

    def on_scan_progress(self, found: int, processed: int) -> None:
        """
        Handle scan progress updates.

        Args:
            found: Number of files found
            processed: Number of files processed
        """
        if found > 0:
            progress = int((processed / found) * 100)
            self.progress_bar.setValue(progress)
        self.status_bar.showMessage(f"Scanning: {processed}/{found} files processed")

    def on_scan_finished(self, result) -> None:
        """
        Handle scan completion.

        Args:
            result: ScanResult object
        """
        self.progress_bar.setVisible(False)

        if result.cancelled:
            self.status_bar.showMessage("Scan cancelled")
        elif result.errors:
            self.status_bar.showMessage(f"Scan completed with {len(result.errors)} errors")
        else:
            self.status_bar.showMessage(f"Scan completed: {result.files_found} files found")

        # Reload file list
        self.file_model.load_files(self.current_directory)
        self.update_status()

    def refresh_file_list(self) -> None:
        """Refresh file list from database."""
        if self.current_directory:
            self.file_model.load_files(self.current_directory)
            self.update_status()

    def on_selection_changed(self) -> None:
        """Handle file selection change."""
        indexes = self.file_table.selectedIndexes()
        if not indexes:
            self.metadata_panel.clear()
            self.preview_widget.release_resources()
            return

        row = indexes[0].row()
        file_data = self.file_model.get_file_at_row(row)

        if file_data:
            self.metadata_panel.display_metadata(file_data)

    def on_file_double_clicked(self, index) -> None:
        """Handle file double-click (preview)."""
        file_data = self.file_model.get_file_at_row(index.row())
        if file_data:
            self.preview_widget.load_video(file_data['path'])

    def on_preview_error(self, error_message: str) -> None:
        """
        Handle video preview errors (codec issues, format not supported).
        Offers fallback to external player to complete workflow.
        """
        import subprocess
        import platform

        # Get current file being previewed
        current_file = self.preview_widget.current_file
        if not current_file:
            return

        # Build user-friendly error message
        msg = (
            f"Video preview failed:\n\n{error_message}\n\n"
            "This usually means:\n"
            "• Video codec not supported by Windows Media Foundation\n"
            "• Missing system codecs (H.265/HEVC, MKV, etc.)\n\n"
            "Would you like to open this video in an external player\n"
            "to verify its contents?"
        )

        reply = QMessageBox.question(
            self,
            "Preview Failed - External Player?",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Try to open with default system player
            try:
                if platform.system() == 'Windows':
                    os.startfile(current_file)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', current_file])
                else:  # Linux
                    subprocess.Popen(['xdg-open', current_file])

                self.status_bar.showMessage(
                    f"Opened in external player: {os.path.basename(current_file)}",
                    5000
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not open external player:\n{e}\n\n"
                    "Please install VLC or another video player."
                )

    def rename_selected(self) -> None:
        """Rename selected file."""
        from PyQt5.QtWidgets import QInputDialog

        indexes = self.file_table.selectedIndexes()
        if not indexes:
            return

        file_data = self.file_model.get_file_at_row(indexes[0].row())
        if not file_data:
            return

        old_name = os.path.basename(file_data['path'])
        new_name, ok = QInputDialog.getText(
            self,
            "Rename File",
            "New filename:",
            text=old_name
        )

        if ok and new_name and new_name != old_name:
            success, error = self.file_operations.rename_file(
                file_data['path'],
                new_name
            )

            if success:
                self.file_model.update_file(file_data['path'])
                self.refresh_file_list()
                QMessageBox.information(self, "Success", "File renamed successfully.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to rename file:\n{error}")

    def move_selected(self) -> None:
        """Move selected file."""
        indexes = self.file_table.selectedIndexes()
        if not indexes:
            return

        file_data = self.file_model.get_file_at_row(indexes[0].row())
        if not file_data:
            return

        dest_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Directory"
        )

        if dest_dir:
            success, error = self.file_operations.move_file(
                file_data['path'],
                dest_dir
            )

            if success:
                self.file_model.remove_file(file_data['path'])
                QMessageBox.information(self, "Success", "File moved successfully.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to move file:\n{error}")

    def delete_selected(self) -> None:
        """Delete selected file."""
        indexes = self.file_table.selectedIndexes()
        if not indexes:
            return

        file_data = self.file_model.get_file_at_row(indexes[0].row())
        if not file_data:
            return

        reply = QMessageBox.question(
            self,
            'Delete File',
            f'Are you sure you want to delete:\n{os.path.basename(file_data["path"])}?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, error = self.file_operations.delete_file(file_data['path'])

            if success:
                self.file_model.remove_file(file_data['path'])
                QMessageBox.information(self, "Success", "File deleted successfully.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete file:\n{error}")

    def generate_thumbnail_for_selected(self) -> None:
        """Generate thumbnail for selected file."""
        indexes = self.file_table.selectedIndexes()
        if not indexes:
            return

        file_data = self.file_model.get_file_at_row(indexes[0].row())
        if not file_data:
            return

        # Generate thumbnail
        thumbnail = self.thumbnail_generator.generate_thumbnail(file_data['path'])

        if thumbnail:
            self.cache_manager.add_thumbnail(file_data['path'], thumbnail)
            self.file_model.update_file(file_data['path'])
            self.metadata_panel.display_metadata(self.db.get_file(file_data['path']))
            QMessageBox.information(self, "Success", "Thumbnail generated successfully.")
        else:
            QMessageBox.warning(self, "Failed", "Failed to generate thumbnail.")

    def show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            # Settings saved
            self.update_status()

    def show_cache_stats(self) -> None:
        """Show cache statistics."""
        stats = self.cache_manager.get_cache_stats()

        message = f"""Cache Statistics:

Total Size: {stats['total_size_mb']:.2f} MB / {stats['max_size_mb']:.2f} MB
Usage: {stats['usage_percent']:.1f}%
Thumbnail Count: {stats['file_count']} / {stats['max_count']}
"""
        QMessageBox.information(self, "Cache Statistics", message)

    def prune_cache(self) -> None:
        """Prune cache."""
        result = self.cache_manager.prune_cache()

        message = f"""Cache Pruned:

Thumbnails Removed: {result['thumbnails_removed']}
Space Freed: {(result['size_freed'] / (1024**2)):.2f} MB
Size Before: {(result['size_before'] / (1024**2)):.2f} MB
Size After: {(result['size_after'] / (1024**2)):.2f} MB
"""
        QMessageBox.information(self, "Cache Pruned", message)

    def clear_cache(self) -> None:
        """Clear entire cache."""
        reply = QMessageBox.question(
            self,
            'Clear Cache',
            'Are you sure you want to clear the entire cache?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.cache_manager.clear_cache()
            self.file_model.refresh_thumbnails()
            QMessageBox.information(self, "Success", "Cache cleared successfully.")
            self.update_status()

    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Video Manager",
            """Video Manager v1.0

A PyQt5 application for managing large video collections over network shares.

Features:
- Smart metadata caching
- On-demand thumbnail generation
- Direct network streaming
- Batch operations with undo
- Memory-efficient virtual scrolling
"""
        )

    def update_status(self) -> None:
        """Update status bar with current statistics."""
        file_count = self.file_model.rowCount()
        cache_stats = self.cache_manager.get_cache_stats()

        status_text = f"Files: {file_count} | Cache: {cache_stats['total_size_mb']:.1f} MB ({cache_stats['usage_percent']:.1f}%)"
        self.status_bar.showMessage(status_text)

    def restore_geometry(self) -> None:
        """Restore window geometry from config."""
        geometry = self.config.get('window_geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def save_geometry(self) -> None:
        """Save window geometry to config."""
        self.config.set('window_geometry', self.saveGeometry())

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_geometry()
        self.preview_widget.release_resources()
        event.accept()
