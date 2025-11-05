"""
Main entry point for Video Manager application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

from .core import (
    Config, Database, CacheManager, MetadataExtractor,
    ThumbnailGenerator, FileScanner, FileOperations, BatchOperations
)
from .ui import MainWindow


def main():
    """Main application entry point."""
    # Configure Qt plugin paths for frozen executable (CRITICAL for video playback)
    if getattr(sys, 'frozen', False):
        # PyInstaller extracts to _MEIPASS
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        plugin_path = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'plugins')

        # Tell Qt where to find plugins
        QApplication.addLibraryPath(plugin_path)

        print(f"=== Frozen Executable Mode ===")
        print(f"Plugin path: {plugin_path}")
        print(f"Plugin path exists: {os.path.exists(plugin_path)}")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Video Manager")
    app.setOrganizationName("VideoManager")

    # Initialize configuration
    config = Config()

    # Initialize database
    db_path = os.path.join(config.get('cache_dir'), 'video_manager.db')
    database = Database(db_path)

    # Initialize core components
    cache_manager = CacheManager(database, config.config)
    metadata_extractor = MetadataExtractor(config.config)
    thumbnail_generator = ThumbnailGenerator(config.config)
    file_scanner = FileScanner(
        database,
        metadata_extractor,
        thumbnail_generator,
        config.config
    )
    file_operations = FileOperations(database, config.config)
    batch_operations = BatchOperations(file_operations, database, config.config)

    # Create and show main window
    main_window = MainWindow(
        config,
        database,
        cache_manager,
        metadata_extractor,
        thumbnail_generator,
        file_scanner,
        file_operations,
        batch_operations
    )
    main_window.show()

    # Run application
    exit_code = app.exec_()

    # Cleanup
    database.close()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
