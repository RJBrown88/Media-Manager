#!/usr/bin/env python3
"""
Build script for Video Manager executable.
Creates a standalone Windows .exe file using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def check_platform():
    """Check if running on Windows."""
    current_platform = platform.system()

    if current_platform != 'Windows':
        print("=" * 60)
        print("WARNING: Platform Mismatch!")
        print("=" * 60)
        print(f"Current platform: {current_platform}")
        print(f"Required platform: Windows")
        print()
        print("PyInstaller cannot cross-compile!")
        print("Building on non-Windows will NOT produce a Windows .exe")
        print()
        print("Options:")
        print("1. Run this build on a Windows machine")
        print("2. Use GitHub Actions (see BUILD.md)")
        print("3. Continue anyway (will produce non-Windows binary)")
        print("=" * 60)
        print()

        response = input("Continue anyway? (yes/no): ").lower()
        if response not in ('yes', 'y'):
            print("Build cancelled.")
            return False

    return True


def clean_build_dirs():
    """Remove old build artifacts."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)

    # Clean .spec cache
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d))


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'PyInstaller>=5.0.0'])

    try:
        from PyQt5.QtCore import PYQT_VERSION_STR
        print(f"✓ PyQt5 {PYQT_VERSION_STR}")
    except ImportError:
        print("✗ PyQt5 not found. Please install requirements.txt")
        return False
    except AttributeError:
        # Fallback if version string not available
        print("✓ PyQt5 (version unknown)")
        pass

    try:
        import PIL
        print(f"✓ Pillow {PIL.__version__}")
    except ImportError:
        print("✗ Pillow not found. Please install requirements.txt")
        return False

    return True


def build_executable():
    """Build the executable using PyInstaller."""
    print("\nBuilding executable...")
    print("This may take a few minutes...\n")

    # Run PyInstaller with spec file
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--clean',
        '--noconfirm',
        'video_manager.spec'
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n✗ Build failed!")
        return False

    return True


def check_output():
    """Check if the executable was created successfully."""
    exe_path = Path('dist/VideoManager.exe')

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ Build successful!")
        print(f"✓ Executable created: {exe_path}")
        print(f"✓ Size: {size_mb:.2f} MB")
        return True
    else:
        print("\n✗ Executable not found in dist/")
        return False


def create_distribution():
    """Create a distribution folder with the executable and necessary files."""
    print("\nCreating distribution package...")

    dist_dir = Path('distribution')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Copy executable
    shutil.copy('dist/VideoManager.exe', dist_dir / 'VideoManager.exe')

    # Create README for distribution
    readme_content = """# Video Manager - Windows Executable

## Installation

1. **Install FFmpeg**:
   - Download from: https://ffmpeg.org/download.html
   - Extract to a folder (e.g., C:\\ffmpeg)
   - Add ffmpeg\\bin to your PATH environment variable
   - Verify: Open CMD and run `ffmpeg -version`

2. **Run Video Manager**:
   - Double-click `VideoManager.exe`
   - No Python installation required!

## First Use

1. Enter a UNC path or browse to a video directory
   Example: \\\\server\\share\\videos

2. Click "Scan" to index your videos

3. Double-click files to preview

4. Use File menu → Settings to adjust cache and network options

## System Requirements

- Windows 7 or later
- FFmpeg (required for video processing)
- Network access to video shares
- 4GB RAM minimum (8GB recommended)
- 5-25GB free disk space for cache

## Troubleshooting

**"FFmpeg not found"**:
- Install FFmpeg and add to PATH
- Restart the application

**"Access denied" on UNC path**:
- Verify network credentials
- Try mapping the network drive

**Application won't start**:
- Check Windows Defender/Antivirus (may block first run)
- Right-click → "Run as administrator" if needed

## Support

For issues: https://github.com/yourusername/video-manager/issues
Documentation: See full README.md in source repository

## Version

Video Manager v1.0.0
Built with PyQt5 and Python
"""

    with open(dist_dir / 'README.txt', 'w') as f:
        f.write(readme_content)

    print(f"✓ Distribution package created in: {dist_dir}/")
    print(f"  - VideoManager.exe")
    print(f"  - README.txt")

    return True


def main():
    """Main build process."""
    print("=" * 60)
    print("Video Manager - Build Script")
    print("=" * 60)

    # Step 0: Check platform
    if not check_platform():
        return 1

    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n✗ Please install dependencies first:")
        print("  pip install -r requirements.txt")
        return 1

    # Step 2: Clean old builds
    print("\nCleaning old build artifacts...")
    clean_build_dirs()

    # Step 3: Build executable
    if not build_executable():
        return 1

    # Step 4: Check output
    if not check_output():
        return 1

    # Step 5: Create distribution package
    create_distribution()

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test the executable: distribution/VideoManager.exe")
    print("2. Ensure FFmpeg is installed on target system")
    print("3. Distribute the 'distribution' folder to users")
    print("\nNote: FFmpeg must be installed separately on the target system.")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
