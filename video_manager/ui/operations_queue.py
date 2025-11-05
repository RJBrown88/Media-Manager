"""
Operations queue widget for displaying ongoing file operations.
Shows progress, ETA, and allows pause/cancel.
"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QScrollArea, QFrame
)


class OperationWidget(QWidget):
    """Widget for displaying single operation."""

    # Signals
    cancelRequested = pyqtSignal()
    pauseRequested = pyqtSignal()
    resumeRequested = pyqtSignal()

    def __init__(self, operation, parent=None):
        """
        Initialize operation widget.

        Args:
            operation: FileOperation instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.operation = operation
        self.paused = False
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Operation description
        import os
        filename = os.path.basename(self.operation.source)
        op_text = f"{self.operation.operation_type.capitalize()}: {filename}"
        self.label = QLabel(op_text)
        layout.addWidget(self.label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # Status and controls layout
        controls_layout = QHBoxLayout()

        # Status label
        self.status_label = QLabel("Pending...")
        controls_layout.addWidget(self.status_label)

        controls_layout.addStretch()

        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        controls_layout.addWidget(self.cancel_button)

        layout.addLayout(controls_layout)

        # Frame border
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    def update_progress(self) -> None:
        """Update progress display."""
        progress = self.operation.get_progress()
        self.progress_bar.setValue(int(progress))

        # Update status
        if self.operation.status == 'completed':
            self.status_label.setText("Completed")
            self.progress_bar.setValue(100)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif self.operation.status == 'failed':
            self.status_label.setText(f"Failed: {self.operation.error}")
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif self.operation.status == 'running':
            speed = self.operation.get_speed()
            eta = self.operation.get_eta()

            if speed > 0:
                speed_mb = speed / (1024 * 1024)
                self.status_label.setText(f"{progress:.1f}% - {speed_mb:.2f} MB/s - ETA: {self._format_time(eta)}")
            else:
                self.status_label.setText(f"{progress:.1f}%")

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self.paused:
            self.pause_button.setText("Pause")
            self.paused = False
            self.resumeRequested.emit()
        else:
            self.pause_button.setText("Resume")
            self.paused = True
            self.pauseRequested.emit()

    def cancel(self) -> None:
        """Request cancellation."""
        self.cancelRequested.emit()
        self.status_label.setText("Cancelling...")
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Format time in seconds.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        if seconds <= 0:
            return "0s"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


class OperationsQueueWidget(QWidget):
    """Widget for managing operations queue."""

    def __init__(self, parent=None):
        """
        Initialize operations queue widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.operation_widgets = []
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all)
        self.update_timer.start(500)  # Update every 500ms
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("<b>Operations Queue</b>")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Clear completed button
        self.clear_button = QPushButton("Clear Completed")
        self.clear_button.clicked.connect(self.clear_completed)
        header_layout.addWidget(self.clear_button)

        layout.addLayout(header_layout)

        # Scroll area for operations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Container for operation widgets
        self.operations_container = QWidget()
        self.operations_layout = QVBoxLayout()
        self.operations_layout.addStretch()
        self.operations_container.setLayout(self.operations_layout)

        scroll.setWidget(self.operations_container)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def add_operation(self, operation) -> OperationWidget:
        """
        Add operation to queue.

        Args:
            operation: FileOperation instance

        Returns:
            OperationWidget instance
        """
        widget = OperationWidget(operation)
        self.operation_widgets.append(widget)

        # Insert before stretch
        self.operations_layout.insertWidget(
            self.operations_layout.count() - 1,
            widget
        )

        return widget

    def remove_operation(self, widget: OperationWidget) -> None:
        """
        Remove operation widget.

        Args:
            widget: OperationWidget to remove
        """
        if widget in self.operation_widgets:
            self.operation_widgets.remove(widget)
            self.operations_layout.removeWidget(widget)
            widget.deleteLater()

    def clear_completed(self) -> None:
        """Remove all completed operations from display."""
        to_remove = []
        for widget in self.operation_widgets:
            if widget.operation.status in ('completed', 'failed'):
                to_remove.append(widget)

        for widget in to_remove:
            self.remove_operation(widget)

    def update_all(self) -> None:
        """Update all operation widgets."""
        for widget in self.operation_widgets:
            widget.update_progress()

    def get_active_count(self) -> int:
        """Get number of active operations."""
        return sum(1 for w in self.operation_widgets
                  if w.operation.status not in ('completed', 'failed'))

    def clear_all(self) -> None:
        """Remove all operations from display."""
        for widget in list(self.operation_widgets):
            self.remove_operation(widget)
