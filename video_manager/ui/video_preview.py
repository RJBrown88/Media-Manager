"""
Video preview widget with QMediaPlayer streaming.
Streams directly from network without local copy.
"""

from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider,
    QLabel, QStyle
)


class VideoPreviewWidget(QWidget):
    """Video preview widget with playback controls."""

    # Signals
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Initialize video preview widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_file = None
        self.init_ui()

        # Diagnostic: Check available media services
        self._check_media_services()

    def init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        layout.addWidget(self.video_widget)

        # Media player
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Connect signals
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.error.connect(self.on_error)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)

        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)

        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)

        layout.addLayout(controls_layout)

        # Status label
        self.status_label = QLabel("No video loaded")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_video(self, file_path: str) -> None:
        """
        Load video from file path (can be UNC path).

        Args:
            file_path: Path to video file
        """
        self.current_file = file_path

        # Stop current playback
        self.media_player.stop()

        # Set media content
        # For Windows UNC paths, QUrl.fromLocalFile handles them properly
        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)
        self.media_player.setMedia(content)

        # Update status
        import os
        filename = os.path.basename(file_path)
        self.status_label.setText(f"Loading: {filename}")

        # Start playing
        self.media_player.play()

    def toggle_playback(self) -> None:
        """Toggle between play and pause."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop(self) -> None:
        """Stop playback."""
        self.media_player.stop()

    def set_position(self, position: int) -> None:
        """
        Set playback position.

        Args:
            position: Position in milliseconds
        """
        self.media_player.setPosition(position)

    def on_state_changed(self, state: QMediaPlayer.State) -> None:
        """
        Handle media player state changes.

        Args:
            state: New player state
        """
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            if self.current_file:
                import os
                self.status_label.setText(f"Playing: {os.path.basename(self.current_file)}")
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            if state == QMediaPlayer.PausedState:
                self.status_label.setText("Paused")
            elif state == QMediaPlayer.StoppedState:
                self.status_label.setText("Stopped")

    def on_position_changed(self, position: int) -> None:
        """
        Handle playback position changes.

        Args:
            position: Current position in milliseconds
        """
        # Update slider
        self.position_slider.setValue(position)

        # Update time label
        current_time = self._format_time(position)
        total_time = self._format_time(self.media_player.duration())
        self.time_label.setText(f"{current_time} / {total_time}")

    def on_duration_changed(self, duration: int) -> None:
        """
        Handle duration changes.

        Args:
            duration: Video duration in milliseconds
        """
        self.position_slider.setRange(0, duration)

    def on_error(self, error: QMediaPlayer.Error) -> None:
        """
        Handle media player errors.

        Args:
            error: Error code
        """
        error_string = self.media_player.errorString()

        # Map error codes to descriptions
        error_messages = {
            QMediaPlayer.NoError: "No error",
            QMediaPlayer.ResourceError: "Resource error - file cannot be opened or read",
            QMediaPlayer.FormatError: "Format error - unsupported format or codec",
            QMediaPlayer.NetworkError: "Network error",
            QMediaPlayer.AccessDeniedError: "Access denied",
            QMediaPlayer.ServiceMissingError: "Media service missing - Qt multimedia plugins not found",
        }

        error_desc = error_messages.get(error, f"Unknown error ({error})")
        full_message = f"{error_desc}"
        if error_string:
            full_message += f": {error_string}"

        self.status_label.setText(f"Error: {full_message}")
        self.errorOccurred.emit(full_message)

        # Log to console for debugging
        print(f"QMediaPlayer Error: {error} - {error_desc}")
        if error_string:
            print(f"  Detail: {error_string}")
        print(f"  File: {self.current_file}")

    def seek_to_keyframe(self, position: float) -> None:
        """
        Seek to relative position (0.0-1.0).

        Args:
            position: Relative position
        """
        duration = self.media_player.duration()
        if duration > 0:
            target_position = int(duration * position)
            self.media_player.setPosition(target_position)

    def release_resources(self) -> None:
        """Release media player resources."""
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        self.current_file = None
        self.status_label.setText("No video loaded")

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        """
        Format time in milliseconds to MM:SS or HH:MM:SS.

        Args:
            milliseconds: Time in milliseconds

        Returns:
            Formatted time string
        """
        if milliseconds <= 0:
            return "00:00"

        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def get_current_position(self) -> int:
        """Get current playback position in milliseconds."""
        return self.media_player.position()

    def get_duration(self) -> int:
        """Get video duration in milliseconds."""
        return self.media_player.duration()

    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.media_player.state() == QMediaPlayer.PlayingState

    def set_volume(self, volume: int) -> None:
        """
        Set playback volume.

        Args:
            volume: Volume level (0-100)
        """
        self.media_player.setVolume(volume)

    def get_volume(self) -> int:
        """Get current volume level."""
        return self.media_player.volume()

    def _check_media_services(self) -> None:
        """
        Diagnostic check for available media services.
        Logs information that helps diagnose playback issues.
        """
        try:
            from PyQt5.QtMultimedia import QMediaService
            print("=== Qt Multimedia Diagnostics ===")
            print(f"QMediaPlayer availability: {QMediaPlayer.hasSupport('video/mp4')}")
            print(f"Media player service: {self.media_player.service() is not None}")

            # Check if we're in a frozen executable
            import sys
            if getattr(sys, 'frozen', False):
                print("Running as frozen executable")
                print(f"  Executable path: {sys.executable}")
                print(f"  _MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
            else:
                print("Running from source")

            print("================================")
        except Exception as e:
            print(f"Error checking media services: {e}")
