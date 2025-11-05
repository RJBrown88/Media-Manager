"""
Video metadata extractor using FFmpeg/FFprobe.
Optimized for network access with minimal data transfer.
"""

import json
import os
import subprocess
from typing import Dict, Optional
import struct


class MetadataExtractor:
    """Extract video metadata efficiently from network files."""

    # Common video file extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts', '.m2ts'
    }

    def __init__(self, config: dict):
        """
        Initialize metadata extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.timeout = config.get('network_timeout', 30)
        self.header_read_size = config.get('header_read_size', 10 * 1024 * 1024)

    @staticmethod
    def is_video_file(path: str) -> bool:
        """
        Check if file is a video based on extension.

        Args:
            path: File path

        Returns:
            True if file appears to be a video
        """
        _, ext = os.path.splitext(path)
        return ext.lower() in MetadataExtractor.VIDEO_EXTENSIONS

    def extract_metadata(self, path: str, deep_scan: bool = False) -> Optional[Dict]:
        """
        Extract video metadata using FFprobe.

        Args:
            path: File path (can be UNC path)
            deep_scan: If True, perform full scan; if False, quick header scan

        Returns:
            Dictionary with metadata or None if extraction failed
        """
        if not self.is_video_file(path):
            return None

        try:
            # Use FFprobe to extract metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
            ]

            # For quick scan, limit analysis
            if not deep_scan:
                cmd.extend([
                    '-analyzeduration', '5000000',  # 5 seconds
                    '-probesize', str(self.header_read_size),
                ])

            cmd.append(path)

            # Run FFprobe with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                return None

            # Parse JSON output
            data = json.loads(result.stdout)

            return self._parse_ffprobe_output(data, path)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError,
                json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Failed to extract metadata from {path}: {e}")
            return None

    def _parse_ffprobe_output(self, data: dict, path: str) -> Dict:
        """
        Parse FFprobe output into simplified metadata.

        Args:
            data: FFprobe JSON output
            path: File path

        Returns:
            Simplified metadata dictionary
        """
        metadata = {
            'path': path,
            'size': 0,
            'duration': None,
            'resolution': None,
            'width': None,
            'height': None,
            'codec': None,
            'bitrate': None,
            'framerate': None,
            'audio_codec': None,
            'audio_channels': None,
            'format': None,
        }

        # Extract format information
        if 'format' in data:
            fmt = data['format']
            metadata['size'] = int(fmt.get('size', 0))
            metadata['duration'] = float(fmt.get('duration', 0))
            metadata['bitrate'] = int(fmt.get('bit_rate', 0)) if 'bit_rate' in fmt else None
            metadata['format'] = fmt.get('format_name', '')

        # Extract video stream information
        if 'streams' in data:
            for stream in data['streams']:
                if stream.get('codec_type') == 'video':
                    metadata['codec'] = stream.get('codec_name')
                    metadata['width'] = stream.get('width')
                    metadata['height'] = stream.get('height')

                    if metadata['width'] and metadata['height']:
                        metadata['resolution'] = f"{metadata['width']}x{metadata['height']}"

                    # Get framerate
                    fps = stream.get('r_frame_rate', '0/1')
                    if '/' in fps:
                        num, den = fps.split('/')
                        if int(den) > 0:
                            metadata['framerate'] = float(num) / float(den)

                elif stream.get('codec_type') == 'audio':
                    if not metadata['audio_codec']:  # Take first audio stream
                        metadata['audio_codec'] = stream.get('codec_name')
                        metadata['audio_channels'] = stream.get('channels')

        return metadata

    def quick_metadata(self, path: str) -> Optional[Dict]:
        """
        Extract basic metadata quickly (header only).

        Args:
            path: File path

        Returns:
            Basic metadata or None
        """
        return self.extract_metadata(path, deep_scan=False)

    def deep_metadata(self, path: str) -> Optional[Dict]:
        """
        Extract full metadata with deep scan.

        Args:
            path: File path

        Returns:
            Full metadata or None
        """
        return self.extract_metadata(path, deep_scan=True)

    def extract_keyframe_position(self, path: str, position: float = 0.3) -> Optional[float]:
        """
        Find nearest keyframe position for thumbnail extraction.

        Args:
            path: File path
            position: Relative position (0.0-1.0)

        Returns:
            Timestamp of nearest keyframe or None
        """
        try:
            # First get duration
            metadata = self.quick_metadata(path)
            if not metadata or not metadata['duration']:
                return None

            target_time = metadata['duration'] * position

            # Find keyframes around target time
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-select_streams', 'v:0',
                '-show_entries', 'packet=pts_time,flags',
                '-of', 'csv=print_section=0',
                '-read_intervals', f'{max(0, target_time-5)}%{target_time+5}',
                path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                return target_time  # Fallback to target time

            # Parse output to find nearest keyframe
            keyframes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        pts_time, flags = parts
                        if 'K' in flags:  # Keyframe flag
                            try:
                                keyframes.append(float(pts_time))
                            except ValueError:
                                pass

            # Find nearest keyframe to target
            if keyframes:
                nearest = min(keyframes, key=lambda x: abs(x - target_time))
                return nearest

            return target_time

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Failed to find keyframe position: {e}")
            return None

    def validate_file(self, path: str) -> bool:
        """
        Validate that file is a readable video.

        Args:
            path: File path

        Returns:
            True if file is valid video
        """
        metadata = self.quick_metadata(path)
        return metadata is not None and metadata.get('duration', 0) > 0
