# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Video Manager application.
Builds a single-file Windows executable with all dependencies.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect Qt multimedia plugins (CRITICAL for video playback)
qt_multimedia_binaries = []
qt_multimedia_datas = []

# Try to find Qt plugins directory
try:
    from PyQt5.QtCore import QLibraryInfo
    qt_plugin_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)

    # Multimedia plugins (needed for QMediaPlayer)
    multimedia_plugins = os.path.join(qt_plugin_path, 'mediaservice')
    if os.path.exists(multimedia_plugins):
        for file in os.listdir(multimedia_plugins):
            if file.endswith('.dll'):
                src = os.path.join(multimedia_plugins, file)
                qt_multimedia_binaries.append((src, 'PyQt5/Qt5/plugins/mediaservice'))

    # Platform plugins (needed for video output)
    platform_plugins = os.path.join(qt_plugin_path, 'platforms')
    if os.path.exists(platform_plugins):
        for file in os.listdir(platform_plugins):
            if file.endswith('.dll'):
                src = os.path.join(platform_plugins, file)
                qt_multimedia_binaries.append((src, 'PyQt5/Qt5/plugins/platforms'))
except Exception as e:
    print(f"Warning: Could not collect Qt plugins: {e}")

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=qt_multimedia_binaries,  # Include Qt plugins
    datas=qt_multimedia_datas,
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.sip',
        'video_manager.core',
        'video_manager.ui',
        'video_manager.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'unittest',
        'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI only)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'path/to/icon.ico'
    version_file=None,
)
