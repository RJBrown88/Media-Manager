"""
Settings dialog for configuration management.
Allows user to adjust cache, network, and UI settings.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QLineEdit, QGroupBox,
    QGridLayout, QFileDialog, QTabWidget, QWidget
)


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, config, parent=None):
        """
        Initialize settings dialog.

        Args:
            config: Config instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_settings()

    def init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Tab widget for different setting categories
        tabs = QTabWidget()

        # Cache settings tab
        cache_tab = self.create_cache_tab()
        tabs.addTab(cache_tab, "Cache")

        # Network settings tab
        network_tab = self.create_network_tab()
        tabs.addTab(network_tab, "Network")

        # UI settings tab
        ui_tab = self.create_ui_tab()
        tabs.addTab(ui_tab, "Interface")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def create_cache_tab(self) -> QWidget:
        """Create cache settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Cache directory
        dir_group = QGroupBox("Cache Directory")
        dir_layout = QHBoxLayout()

        self.cache_dir_edit = QLineEdit()
        dir_layout.addWidget(self.cache_dir_edit)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_cache_dir)
        dir_layout.addWidget(browse_button)

        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Cache limits
        limits_group = QGroupBox("Cache Limits")
        limits_layout = QGridLayout()

        row = 0

        # Max cache size
        limits_layout.addWidget(QLabel("Max Cache Size (GB):"), row, 0)
        self.max_cache_size_spin = QSpinBox()
        self.max_cache_size_spin.setRange(1, 100)
        self.max_cache_size_spin.setSuffix(" GB")
        limits_layout.addWidget(self.max_cache_size_spin, row, 1)
        row += 1

        # Thumbnail quality
        limits_layout.addWidget(QLabel("Thumbnail Quality:"), row, 0)
        self.thumbnail_quality_spin = QSpinBox()
        self.thumbnail_quality_spin.setRange(60, 95)
        self.thumbnail_quality_spin.setSuffix(" %")
        limits_layout.addWidget(self.thumbnail_quality_spin, row, 1)
        row += 1

        # Max thumbnail count
        limits_layout.addWidget(QLabel("Max Thumbnails:"), row, 0)
        self.max_thumbnails_spin = QSpinBox()
        self.max_thumbnails_spin.setRange(100, 5000)
        limits_layout.addWidget(self.max_thumbnails_spin, row, 1)
        row += 1

        # Cache prune threshold
        limits_layout.addWidget(QLabel("Prune Threshold (GB):"), row, 0)
        self.prune_threshold_spin = QSpinBox()
        self.prune_threshold_spin.setRange(1, 50)
        self.prune_threshold_spin.setSuffix(" GB")
        limits_layout.addWidget(self.prune_threshold_spin, row, 1)
        row += 1

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_network_tab(self) -> QWidget:
        """Create network settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Network performance
        perf_group = QGroupBox("Network Performance")
        perf_layout = QGridLayout()

        row = 0

        # Network timeout
        perf_layout.addWidget(QLabel("Network Timeout (seconds):"), row, 0)
        self.network_timeout_spin = QSpinBox()
        self.network_timeout_spin.setRange(10, 300)
        self.network_timeout_spin.setSuffix(" s")
        perf_layout.addWidget(self.network_timeout_spin, row, 1)
        row += 1

        # Chunk size
        perf_layout.addWidget(QLabel("Transfer Chunk Size (MB):"), row, 0)
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(1, 256)
        self.chunk_size_spin.setSuffix(" MB")
        perf_layout.addWidget(self.chunk_size_spin, row, 1)
        row += 1

        # Bandwidth limit
        perf_layout.addWidget(QLabel("Bandwidth Limit (MB/s):"), row, 0)
        self.bandwidth_limit_spin = QSpinBox()
        self.bandwidth_limit_spin.setRange(0, 1000)
        self.bandwidth_limit_spin.setSpecialValueText("Unlimited")
        self.bandwidth_limit_spin.setSuffix(" MB/s")
        perf_layout.addWidget(self.bandwidth_limit_spin, row, 1)
        row += 1

        # Max parallel metadata extraction
        perf_layout.addWidget(QLabel("Parallel Metadata Threads:"), row, 0)
        self.max_parallel_spin = QSpinBox()
        self.max_parallel_spin.setRange(1, 10)
        perf_layout.addWidget(self.max_parallel_spin, row, 1)
        row += 1

        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)

        # Scanning
        scan_group = QGroupBox("File Scanning")
        scan_layout = QGridLayout()

        row = 0

        # Scan batch size
        scan_layout.addWidget(QLabel("Scan Batch Size:"), row, 0)
        self.scan_batch_spin = QSpinBox()
        self.scan_batch_spin.setRange(10, 500)
        scan_layout.addWidget(self.scan_batch_spin, row, 1)
        row += 1

        # Deep scan threshold
        scan_layout.addWidget(QLabel("Deep Scan Threshold (GB):"), row, 0)
        self.deep_scan_threshold_spin = QSpinBox()
        self.deep_scan_threshold_spin.setRange(1, 50)
        self.deep_scan_threshold_spin.setSuffix(" GB")
        scan_layout.addWidget(self.deep_scan_threshold_spin, row, 1)
        row += 1

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QGridLayout()

        row = 0

        # Files per page
        display_layout.addWidget(QLabel("Files Per Page:"), row, 0)
        self.files_per_page_spin = QSpinBox()
        self.files_per_page_spin.setRange(10, 500)
        display_layout.addWidget(self.files_per_page_spin, row, 1)
        row += 1

        # Max thumbnails in memory
        display_layout.addWidget(QLabel("Thumbnails in Memory:"), row, 0)
        self.max_thumbnails_memory_spin = QSpinBox()
        self.max_thumbnails_memory_spin.setRange(5, 100)
        display_layout.addWidget(self.max_thumbnails_memory_spin, row, 1)
        row += 1

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def browse_cache_dir(self) -> None:
        """Browse for cache directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Cache Directory",
            self.cache_dir_edit.text()
        )
        if directory:
            self.cache_dir_edit.setText(directory)

    def load_settings(self) -> None:
        """Load settings from config."""
        # Cache settings
        self.cache_dir_edit.setText(self.config.get('cache_dir'))
        self.max_cache_size_spin.setValue(
            self.config.get('max_cache_size') // (1024**3)
        )
        self.thumbnail_quality_spin.setValue(
            self.config.get('thumbnail_quality')
        )
        self.max_thumbnails_spin.setValue(
            self.config.get('thumbnail_max_count')
        )
        self.prune_threshold_spin.setValue(
            self.config.get('cache_prune_threshold') // (1024**3)
        )

        # Network settings
        self.network_timeout_spin.setValue(self.config.get('network_timeout'))
        self.chunk_size_spin.setValue(
            self.config.get('chunk_size') // (1024**2)
        )
        self.bandwidth_limit_spin.setValue(self.config.get('bandwidth_limit'))
        self.max_parallel_spin.setValue(self.config.get('max_parallel_metadata'))
        self.scan_batch_spin.setValue(self.config.get('scan_batch_size'))
        self.deep_scan_threshold_spin.setValue(
            self.config.get('deep_scan_threshold') // (1024**3)
        )

        # UI settings
        self.files_per_page_spin.setValue(self.config.get('files_per_page'))
        self.max_thumbnails_memory_spin.setValue(
            self.config.get('max_thumbnails_in_memory')
        )

    def save_settings(self) -> None:
        """Save settings to config."""
        # Cache settings
        self.config.set('cache_dir', self.cache_dir_edit.text())
        self.config.set(
            'max_cache_size',
            self.max_cache_size_spin.value() * (1024**3)
        )
        self.config.set(
            'thumbnail_quality',
            self.thumbnail_quality_spin.value()
        )
        self.config.set(
            'thumbnail_max_count',
            self.max_thumbnails_spin.value()
        )
        self.config.set(
            'cache_prune_threshold',
            self.prune_threshold_spin.value() * (1024**3)
        )

        # Network settings
        self.config.set('network_timeout', self.network_timeout_spin.value())
        self.config.set(
            'chunk_size',
            self.chunk_size_spin.value() * (1024**2)
        )
        self.config.set('bandwidth_limit', self.bandwidth_limit_spin.value())
        self.config.set(
            'max_parallel_metadata',
            self.max_parallel_spin.value()
        )
        self.config.set('scan_batch_size', self.scan_batch_spin.value())
        self.config.set(
            'deep_scan_threshold',
            self.deep_scan_threshold_spin.value() * (1024**3)
        )

        # UI settings
        self.config.set('files_per_page', self.files_per_page_spin.value())
        self.config.set(
            'max_thumbnails_in_memory',
            self.max_thumbnails_memory_spin.value()
        )

        self.accept()

    def reset_defaults(self) -> None:
        """Reset all settings to defaults."""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            'Reset Settings',
            'Are you sure you want to reset all settings to defaults?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config.reset_to_defaults()
            self.load_settings()
