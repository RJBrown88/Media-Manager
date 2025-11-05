#!/usr/bin/env python3
"""
Simple run script for Video Manager application.

IMPORTANT: This is the entry point for both:
- Running from source: python run.py
- Frozen executable: PyInstaller uses this as entry point

The if __name__ == '__main__' guard is CRITICAL to prevent
infinite process spawning in frozen executables.
"""

import multiprocessing

if __name__ == '__main__':
    # CRITICAL: Must be called before any imports that might use multiprocessing
    # This prevents infinite spawning in frozen executables (PyInstaller)
    multiprocessing.freeze_support()

    from video_manager.__main__ import main
    main()
