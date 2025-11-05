"""
Main entry point for Video Manager application.
"""

import sys
import os
import multiprocessing
from PyQt5.QtWidgets import QApplication

from .core import (
    Config, Database, CacheManager, MetadataExtractor,
    ThumbnailGenerator, FileScanner, FileOperations, BatchOperations
)
from .ui import MainWindow


def main():
    """Main application entry point."""
    # Note: multiprocessing.freeze_support() is called in run.py
    # before this function is invoked.

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


# REMOVED: if __name__ == '__main__': block
# Reason: In frozen apps (PyInstaller), this module's __name__ can be '__main__'
# causing it to execute during import, leading to infinite spawn loop.
# This module should ONLY be called from run.py, never executed directly.

