# Building Video Manager Executable

This guide explains how to build Video Manager into a standalone Windows executable (.exe) that can be distributed without requiring Python installation.

## Prerequisites

### Required Software
1. **Python 3.8 or later**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure "Add Python to PATH" is checked during installation

2. **Git** (if building from source)
   - Download from [git-scm.com](https://git-scm.com/)

3. **Visual C++ Redistributable** (usually already installed on Windows)
   - Download from [Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

### Python Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

This installs:
- PyQt5 >= 5.15.0
- Pillow >= 9.0.0
- PyInstaller >= 5.0.0

## Build Methods

### Method 1: Automated Build (Recommended)

#### On Windows:
Simply run the batch script:
```bash
build.bat
```

#### On Linux/Mac:
Run the Python build script:
```bash
python build.py
```

The build script will:
1. Check dependencies
2. Clean old build artifacts
3. Compile the executable using PyInstaller
4. Create a distribution package

### Method 2: Manual Build

If you prefer to build manually:

```bash
# Clean old builds
rmdir /s /q build dist

# Build with PyInstaller
python -m PyInstaller --clean --noconfirm video_manager.spec

# The executable will be in: dist/VideoManager.exe
```

## Build Configuration

The build is configured in `video_manager.spec`:

- **Single-file executable**: All dependencies bundled
- **No console window**: GUI-only application
- **UPX compression**: Reduces file size
- **Hidden imports**: Ensures all PyQt5 modules included

### Customization Options

Edit `video_manager.spec` to customize:

**Add an application icon:**
```python
exe = EXE(
    ...
    icon='path/to/icon.ico',  # Your icon file
)
```

**Enable console for debugging:**
```python
exe = EXE(
    ...
    console=True,  # Shows console output
)
```

**Create directory distribution instead of single file:**
```python
exe = EXE(
    ...
)
# Remove the single-file bundling to create a directory
```

## Build Output

### Successful Build
```
distribution/
├── VideoManager.exe    # Standalone executable (~80-150 MB)
└── README.txt          # User instructions
```

### Build Artifacts
```
build/                  # Temporary build files (can be deleted)
dist/                   # PyInstaller output (can be deleted after copying)
video_manager.spec      # Build configuration
```

## Distribution

### What to Distribute

**Minimum (for users with FFmpeg installed):**
- `VideoManager.exe`

**Recommended:**
- `distribution/VideoManager.exe`
- `distribution/README.txt`
- Instructions for installing FFmpeg

**Complete Package:**
You can bundle FFmpeg (if license permits):
```
VideoManager/
├── VideoManager.exe
├── ffmpeg.exe
├── ffprobe.exe
└── README.txt
```

### User Requirements

Users need:
1. Windows 7 or later
2. FFmpeg installed and in PATH
3. 4GB RAM minimum (8GB recommended)
4. 5-25GB disk space for cache

## Testing the Executable

### Basic Test
```bash
# From distribution folder
VideoManager.exe
```

### Test Checklist
- [ ] Application launches without errors
- [ ] Can browse and select directories
- [ ] Can scan directory and list files
- [ ] Can display file metadata
- [ ] Can generate thumbnails
- [ ] Can preview videos (requires FFmpeg)
- [ ] Settings dialog opens and saves
- [ ] File operations work (rename, move, delete)

## Troubleshooting

### "Failed to execute script"
**Cause**: Missing Python dependencies or corrupted build
**Solution**:
- Rebuild with `--clean` flag
- Check all dependencies are installed
- Try building with `console=True` to see error messages

### Large File Size (>200 MB)
**Cause**: Unnecessary packages included
**Solution**:
- Add more packages to `excludes` in spec file
- Check for numpy, pandas, matplotlib being included

### "DLL load failed"
**Cause**: Missing Visual C++ Redistributable
**Solution**: Install VC++ Redistributable on target system

### Missing Modules at Runtime
**Cause**: Hidden imports not specified
**Solution**: Add to `hiddenimports` in spec file:
```python
hiddenimports=[
    'your.missing.module',
]
```

### Antivirus False Positives
**Cause**: PyInstaller executables sometimes trigger AV
**Solution**:
- Code sign the executable
- Submit to antivirus vendors as false positive
- Users can add exception

## Advanced Options

### Optimize File Size

1. **UPX Compression** (already enabled):
   - Download UPX from [upx.github.io](https://upx.github.io/)
   - Place `upx.exe` in PATH or PyInstaller directory

2. **Exclude unnecessary modules**:
   ```python
   excludes=[
       'matplotlib',
       'numpy',
       'pandas',
       'scipy',
       'tkinter',
   ]
   ```

3. **Strip debug symbols**:
   ```python
   strip=True,
   ```

### Create Multiple Versions

Build different configurations:

**Debug version** (with console):
```bash
python -m PyInstaller --clean video_manager_debug.spec
```

**Portable version** (directory-based):
```bash
python -m PyInstaller --clean --onedir video_manager.spec
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Windows Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Build executable
        run: python build.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: VideoManager-Windows
          path: distribution/
```

## Code Signing (Optional)

To avoid Windows SmartScreen warnings:

1. Obtain a code signing certificate
2. Sign the executable:
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com VideoManager.exe
   ```

## Performance Notes

- **Build time**: 2-5 minutes on average hardware
- **Executable size**: 80-150 MB (depending on compression)
- **First run**: May be slower due to unpacking (single-file mode)
- **Runtime performance**: Same as Python script

## Support

For build issues:
- Check PyInstaller documentation: [pyinstaller.org](https://pyinstaller.org/)
- Search existing issues: [PyInstaller GitHub](https://github.com/pyinstaller/pyinstaller/issues)
- File project-specific issues on GitHub

## Version Information

- PyInstaller: 5.0.0+
- Python: 3.8-3.11 (tested)
- PyQt5: 5.15.0+
- Target OS: Windows 7+

## License

The compiled executable includes:
- Video Manager code (MIT License)
- PyQt5 (GPL/Commercial)
- Python runtime
- Other dependencies (see requirements.txt)

Ensure compliance with all licenses when distributing.
