# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Video Manager application.
Builds a single-file Windows executable with all dependencies.
"""

import os
import sys

block_cipher = None

# Collect Qt multimedia plugins (CRITICAL for video playback)
qt_multimedia_binaries = []
qt_platform_binaries = []

try:
    from PyQt5.QtCore import QLibraryInfo

    # Get Qt plugin path
    if hasattr(QLibraryInfo, 'location'):
        # PyQt5 < 5.15
        qt_plugin_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    else:
        # PyQt5 >= 5.15
        qt_plugin_path = QLibraryInfo.path(QLibraryInfo.PluginsPath)

    print(f"Qt plugin path: {qt_plugin_path}")

    # Collect multimedia plugins (dsengine.dll, wmfengine.dll)
    multimedia_plugins = os.path.join(qt_plugin_path, 'mediaservice')
    if os.path.exists(multimedia_plugins):
        print(f"Found multimedia plugins directory: {multimedia_plugins}")
        for file in os.listdir(multimedia_plugins):
            if file.endswith(('.dll', '.so', '.dylib')):
                src = os.path.join(multimedia_plugins, file)
                dest = 'PyQt5/Qt5/plugins/mediaservice'
                qt_multimedia_binaries.append((src, dest))
                print(f"  Bundling: {file} -> {dest}")
    else:
        print(f"WARNING: Multimedia plugins directory not found: {multimedia_plugins}")

    # Collect audio plugins
    audio_plugins = os.path.join(qt_plugin_path, 'audio')
    if os.path.exists(audio_plugins):
        print(f"Found audio plugins directory: {audio_plugins}")
        for file in os.listdir(audio_plugins):
            if file.endswith(('.dll', '.so', '.dylib')):
                src = os.path.join(audio_plugins, file)
                dest = 'PyQt5/Qt5/plugins/audio'
                qt_multimedia_binaries.append((src, dest))
                print(f"  Bundling: {file} -> {dest}")

    # Collect platform plugins (qwindows.dll for Windows)
    platform_plugins = os.path.join(qt_plugin_path, 'platforms')
    if os.path.exists(platform_plugins):
        print(f"Found platform plugins directory: {platform_plugins}")
        for file in os.listdir(platform_plugins):
            if file.endswith(('.dll', '.so', '.dylib')):
                src = os.path.join(platform_plugins, file)
                dest = 'PyQt5/Qt5/plugins/platforms'
                qt_platform_binaries.append((src, dest))
                print(f"  Bundling: {file} -> {dest}")

    print(f"Total multimedia/audio plugins collected: {len(qt_multimedia_binaries)}")
    print(f"Total platform plugins collected: {len(qt_platform_binaries)}")

except Exception as e:
    print(f"ERROR: Could not collect Qt plugins: {e}")
    print("This will result in video playback failures!")
    import traceback
    traceback.print_exc()

# Combine all Qt binaries
all_qt_binaries = qt_multimedia_binaries + qt_platform_binaries

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=all_qt_binaries,
    datas=[
        # Add any data files here if needed
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtNetwork',  # Required for network streaming (UNC paths)
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
    upx_exclude=[
        'qwindows.dll',
        'dsengine.dll',
        'wmfengine.dll',
        'qtmedia_audioengine.dll',
        'qtaudio_windows.dll',
        'Qt5Multimedia.dll',
        'Qt5MultimediaWidgets.dll',
        'Qt5Network.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI only)
                    # Note: To see diagnostic output, run from cmd: VideoManager.exe
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'path/to/icon.ico'
    version_file=None,
)
