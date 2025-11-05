"""
Thumbnail generator with on-demand keyframe extraction.
Optimized for network access with minimal data transfer.
"""

import io
import os
import subprocess
from typing import Optional, Tuple
from PIL import Image


class ThumbnailGenerator:
    """Generate video thumbnails efficiently."""

    def __init__(self, config: dict):
        """
        Initialize thumbnail generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.quality = config.get('thumbnail_quality', 80)
        self.resolution = config.get('thumbnail_resolution', (426, 240))
        self.timeout = config.get('network_timeout', 30)

    def generate_thumbnail(self, video_path: str, timestamp: float = None,
                          keyframe_position: float = 0.3) -> Optional[bytes]:
        """
        Generate thumbnail from video file.

        Args:
            video_path: Path to video file
            timestamp: Specific timestamp to extract (seconds)
            keyframe_position: Relative position for keyframe (0.0-1.0)

        Returns:
            JPEG thumbnail as bytes or None
        """
        try:
            # If no timestamp specified, we'll use a percentage of duration
            if timestamp is None:
                # Use ffprobe to get duration first
                duration_cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ]

                duration_result = subprocess.run(
                    duration_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if duration_result.returncode == 0:
                    try:
                        duration = float(duration_result.stdout.strip())
                        timestamp = duration * keyframe_position
                    except ValueError:
                        timestamp = 0
                else:
                    timestamp = 0

            # Extract frame using FFmpeg
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),  # Seek to position (fast seek)
                '-i', video_path,
                '-vframes', '1',  # Extract single frame
                '-vf', f'scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=decrease',
                '-q:v', str(100 - self.quality),  # Quality (lower is better for FFmpeg)
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg',
                '-'  # Output to stdout
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                return None

            # Process image to ensure it meets size requirements
            thumbnail_data = result.stdout

            # Verify and optimize the thumbnail
            thumbnail_data = self._optimize_thumbnail(thumbnail_data)

            return thumbnail_data

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Failed to generate thumbnail for {video_path}: {e}")
            return None

    def _optimize_thumbnail(self, image_data: bytes) -> bytes:
        """
        Optimize thumbnail size and quality.

        Args:
            image_data: Original image bytes

        Returns:
            Optimized JPEG bytes
        """
        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))

            # Ensure RGB mode
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to target resolution if needed
            if img.size != self.resolution:
                img.thumbnail(self.resolution, Image.Resampling.LANCZOS)

            # Save as optimized JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=self.quality, optimize=True)
            return output.getvalue()

        except Exception as e:
            print(f"Failed to optimize thumbnail: {e}")
            return image_data

    def generate_thumbnail_at_keyframe(self, video_path: str,
                                      keyframe_timestamp: float) -> Optional[bytes]:
        """
        Generate thumbnail at specific keyframe.

        Args:
            video_path: Path to video file
            keyframe_timestamp: Timestamp of keyframe

        Returns:
            JPEG thumbnail as bytes or None
        """
        return self.generate_thumbnail(video_path, timestamp=keyframe_timestamp)

    def get_thumbnail_size(self, thumbnail_data: bytes) -> int:
        """
        Get thumbnail size in bytes.

        Args:
            thumbnail_data: Thumbnail JPEG bytes

        Returns:
            Size in bytes
        """
        return len(thumbnail_data) if thumbnail_data else 0

    def validate_thumbnail(self, thumbnail_data: bytes) -> bool:
        """
        Validate thumbnail data.

        Args:
            thumbnail_data: Thumbnail JPEG bytes

        Returns:
            True if valid JPEG
        """
        try:
            img = Image.open(io.BytesIO(thumbnail_data))
            img.verify()
            return True
        except Exception:
            return False

    def generate_multiple_thumbnails(self, video_path: str,
                                    positions: list = None) -> list:
        """
        Generate multiple thumbnails at different positions.

        Args:
            video_path: Path to video file
            positions: List of relative positions (0.0-1.0)

        Returns:
            List of thumbnail bytes
        """
        if positions is None:
            positions = [0.1, 0.3, 0.5, 0.7, 0.9]

        thumbnails = []
        for pos in positions:
            thumb = self.generate_thumbnail(video_path, keyframe_position=pos)
            if thumb:
                thumbnails.append(thumb)

        return thumbnails

    def get_thumbnail_resolution(self, thumbnail_data: bytes) -> Optional[Tuple[int, int]]:
        """
        Get thumbnail resolution.

        Args:
            thumbnail_data: Thumbnail JPEG bytes

        Returns:
            Tuple of (width, height) or None
        """
        try:
            img = Image.open(io.BytesIO(thumbnail_data))
            return img.size
        except Exception:
            return None
