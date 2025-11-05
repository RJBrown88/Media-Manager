# Quick Windows Build Guide

## TL;DR - Build Executable

### For Windows Users:

**Easy Method:**
1. Open Command Prompt or PowerShell
2. Navigate to project directory
3. Run: `build.bat`
4. Executable will be in `distribution/VideoManager.exe`

**Manual Method:**
```cmd
pip install -r requirements.txt
python build.py
```

## Build Requirements

- Windows 7 or later
- Python 3.8+
- 2GB free RAM
- 500MB free disk space for build

## What Gets Built

### Single Executable
- **Name**: `VideoManager.exe`
- **Size**: ~80-150 MB (compressed)
- **Type**: Standalone (no Python required to run)
- **Contains**: Python runtime + PyQt5 + All dependencies

### Runtime Requirements for Users
- Windows 7+
- FFmpeg (must be installed separately)
- 4GB RAM
- Network access (for UNC paths)

## Building from Different Environments

### On Windows (Native)
```batch
# Install dependencies
pip install -r requirements.txt

# Build executable
build.bat

# Test
cd distribution
VideoManager.exe
```

### On Linux/Mac (Cross-compile - NOT RECOMMENDED)
Cross-compiling Windows executables from Linux is complex and unreliable.

**Options:**
1. Use a Windows VM
2. Use GitHub Actions (see BUILD.md)
3. Use Wine + PyInstaller (advanced, often problematic)

**Best Practice**: Build on Windows for Windows.

## Common Issues

### Build fails with "No module named 'PyQt5'"
**Solution**: `pip install PyQt5`

### "PyInstaller not found"
**Solution**: `pip install PyInstaller>=5.0.0`

### Executable won't run on other computers
**Possible causes**:
- Target PC missing Visual C++ Redistributable
- Antivirus blocking (add exception)
- Windows SmartScreen (click "More info" → "Run anyway")

### "FFmpeg not found" when running executable
**Expected behavior**: Users must install FFmpeg separately
**Solution**: Include FFmpeg installation instructions with distribution

## Distribution Checklist

Before distributing to users:

- [ ] Test executable on clean Windows system
- [ ] Verify all features work
- [ ] Include README.txt with FFmpeg instructions
- [ ] Test on target Windows version (7/10/11)
- [ ] Check file size is reasonable (<200 MB)
- [ ] Scan with antivirus to check for false positives
- [ ] Consider code signing (reduces Windows warnings)

## Build Outputs Explained

```
project/
├── build/                   # Temporary build files (delete after)
├── dist/                    # Raw PyInstaller output
│   └── VideoManager.exe    # The compiled executable
├── distribution/            # Ready-to-distribute package
│   ├── VideoManager.exe    # Executable (copy of above)
│   └── README.txt          # User instructions
└── video_manager.spec      # Build configuration
```

**What to distribute**: The `distribution/` folder

## FFmpeg Bundling (Optional)

If you want to bundle FFmpeg with your distribution:

1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract `ffmpeg.exe` and `ffprobe.exe`
3. Create distribution package:
   ```
   VideoManager/
   ├── VideoManager.exe
   ├── ffmpeg/
   │   ├── ffmpeg.exe
   │   └── ffprobe.exe
   └── README.txt
   ```
4. Update README to reference local FFmpeg

**Note**: Check FFmpeg license compliance for redistribution.

## GitHub Actions Build (Automated)

For automated builds on every release:

1. Create `.github/workflows/build.yml`
2. Configure as shown in BUILD.md
3. Tag a release: `git tag v1.0.0 && git push --tags`
4. GitHub builds and uploads executable automatically

## Performance

- **Build time**: 2-5 minutes (first build may take longer)
- **Executable size**: 80-150 MB depending on options
- **First launch**: Slightly slower (unpacking), then normal speed
- **Memory usage**: Same as Python version

## Updating the Executable

When you update the code:

1. Make your changes
2. Test with Python: `python run.py`
3. Rebuild: `python build.py`
4. Test new executable
5. Distribute updated version

## Version Information in Executable

To add version info (shows in Windows properties):

1. Create `version.txt`:
   ```
   VSVersionInfo(
     ffi=FixedFileInfo(
       filevers=(1, 0, 0, 0),
       prodvers=(1, 0, 0, 0),
       mask=0x3f,
       flags=0x0,
       OS=0x40004,
       fileType=0x1,
       subtype=0x0,
       date=(0, 0)
     ),
     kids=[
       StringFileInfo([
         StringTable('040904B0', [
           StringStruct('CompanyName', 'Your Company'),
           StringStruct('FileDescription', 'Video Manager'),
           StringStruct('FileVersion', '1.0.0.0'),
           StringStruct('ProductName', 'Video Manager'),
           StringStruct('ProductVersion', '1.0.0.0'),
         ])
       ]),
       VarFileInfo([VarStruct('Translation', [1033, 1200])])
     ]
   )
   ```

2. Reference in spec file:
   ```python
   exe = EXE(
       ...
       version='version.txt',
   )
   ```

## Need Help?

- **Build issues**: See BUILD.md for detailed troubleshooting
- **PyInstaller docs**: https://pyinstaller.org/
- **Project issues**: GitHub Issues

## Quick Commands Reference

```batch
# Install dependencies
pip install -r requirements.txt

# Clean build
rmdir /s /q build dist

# Build
python build.py

# Manual build
python -m PyInstaller video_manager.spec

# Test
dist\VideoManager.exe

# Create distribution
# (done automatically by build.py)
```

---

**Note**: This executable is for Windows only. For Linux/Mac, users should run the Python version directly.
