# Video Playback Issues and Solutions

## Issue: Videos Don't Play Despite FFmpeg Installed

### Quick Answer

**QMediaPlayer does NOT use FFmpeg for playback.**

QMediaPlayer uses Windows Media Foundation, which has limited codec support. This is a common issue with PyQt5 on Windows.

---

## Understanding the Problem

### The Architecture

```
Video Manager has TWO separate video systems:

1. VIDEO PREVIEW (QMediaPlayer)
   ├── Uses: Windows Media Foundation
   ├── Does NOT use FFmpeg
   ├── Limited codec support
   └── Depends on system codecs

2. METADATA/THUMBNAILS (subprocess + FFmpeg)
   ├── Uses: FFmpeg via subprocess
   ├── Works if FFmpeg is in PATH
   ├── Full codec support
   └── Independent of QMediaPlayer
```

### Why This Matters

- **FFmpeg installed** ✓ → Thumbnails and metadata work
- **FFmpeg installed** ✗ → Video playback does NOT work
- **Video playback** depends on Qt multimedia plugins + Windows codecs

---

## Root Causes

### Cause 1: Missing Qt Multimedia Plugins (Most Common)

**Problem:**
PyInstaller doesn't automatically bundle Qt multimedia service plugins.

**Symptoms:**
- Error: "Media service missing - Qt multimedia plugins not found"
- Videos don't play
- No error message, just nothing happens

**Fix:**
Update `video_manager.spec` to include Qt plugins (✅ Fixed in latest commit)

---

### Cause 2: Unsupported Video Codec

**Problem:**
Windows Media Foundation doesn't support all codecs out of the box.

**Unsupported by default:**
- H.265 / HEVC
- VP9
- AV1
- Some MKV container formats
- FLAC audio in MP4

**Supported by default:**
- H.264 / AVC in MP4
- H.264 in MOV
- MPEG-4 in AVI
- WMV

**Fix:**
Install K-Lite Codec Pack or LAV Filters on Windows

---

### Cause 3: File Path Issues

**Problem:**
UNC paths might not work with QMediaPlayer.

**Example:**
```python
# May not work:
\\server\share\video.mp4

# Might work better:
Mapped drive: Z:\video.mp4
```

**Fix:**
Try mapping network drive, or copy file locally for testing

---

## Diagnostic Steps

### Step 1: Check Error Message

Run the rebuilt .exe and try to play a video. Look at the status label:

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| "Media service missing" | Qt plugins not bundled | Rebuild with updated spec file |
| "Format error - unsupported format" | Codec not supported | Install K-Lite Codec Pack |
| "Resource error" | File cannot be opened | Check file path, permissions |
| "Access denied" | Permission issue | Check network credentials |
| Nothing happens | Various | Check console output |

### Step 2: Test Different Video Files

Try these test files to isolate the issue:

```
1. Simple H.264 MP4 (most compatible)
   - If this works: Codec issue with original files
   - If this fails: Qt plugin issue

2. Local file (C:\test.mp4)
   - If this works: Network path issue
   - If this fails: Codec or Qt issue

3. Windows sample video
   - Location: C:\Windows\Media\*.mp4
   - If this works: Your files have unsupported codec
```

### Step 3: Check Console Output

The updated code prints diagnostic information:

```
=== Qt Multimedia Diagnostics ===
QMediaPlayer availability: True/False
Media player service: True/False
Running as frozen executable
  Executable path: C:\...\VideoManager.exe
  _MEIPASS: C:\Users\...\AppData\Local\Temp\_MEI...
================================
```

**If you see:**
- `Media player service: False` → Qt plugins not found
- `QMediaPlayer availability: False` → Qt multimedia not available

---

## Solutions

### Solution 1: Rebuild with Updated Spec File (Recommended)

**Status:** ✅ Fixed in latest commit

The spec file now includes:
- Qt mediaservice plugins
- Qt platform plugins
- Proper plugin directory structure

**Steps:**
```cmd
git pull origin claude/pyqt5-video-manager-unc-011CUpUA9xnPqHnJ8obPGVoD
rmdir /s /q build dist
build.bat
```

**Expected size increase:** ~10-20 MB (plugin DLLs added)

---

### Solution 2: Install System Codecs (User Side)

If videos still don't play after rebuild:

**Install K-Lite Codec Pack:**
1. Download: https://codecguide.com/download_kl.htm
2. Choose "Basic" or "Standard" version
3. Install with default settings
4. Restart Video Manager

**Or install LAV Filters:**
1. Download: https://github.com/Nevcairiel/LAVFilters/releases
2. Install
3. Restart Video Manager

This provides codecs to Windows Media Foundation.

---

### Solution 3: Alternative - Use VLC Backend

**For future consideration:**

Replace QMediaPlayer with python-vlc:
- VLC has built-in codec support
- Works better in frozen executables
- Larger file size (~80 MB VLC plugins)
- More reliable cross-platform

**Requires code changes:**
```python
# Instead of QMediaPlayer
import vlc
instance = vlc.Instance()
player = instance.media_player_new()
```

Not implemented yet, but an option if QMediaPlayer continues to have issues.

---

## Testing the Fix

### After Rebuilding

1. **Check Build Output:**
   ```
   Building executable...
   Warning: Could not collect Qt plugins: ...  ← Should NOT appear
   ```

2. **Check File Size:**
   ```
   Before: ~80-150 MB
   After:  ~100-170 MB (plugins added)
   ```

3. **Test Playback:**
   - Open Video Manager
   - Browse to video file
   - Double-click to preview
   - Watch status label for errors

4. **Check Console Output:**
   ```
   === Qt Multimedia Diagnostics ===
   QMediaPlayer availability: True  ← Should be True
   Media player service: True       ← Should be True
   Running as frozen executable
   ```

---

## Workaround While Troubleshooting

If video preview doesn't work:

**Thumbnails still work:**
- FFmpeg is used for thumbnails
- You can see video preview as thumbnail
- Click "Generate Thumbnail" for preview image

**Metadata still works:**
- Duration, resolution, codec information
- All metadata extraction uses FFmpeg
- Independent of QMediaPlayer

**File operations still work:**
- Rename, move, copy, delete
- Batch operations
- Everything except video playback

---

## Known Limitations

### Windows Media Foundation Limitations

Even with plugins bundled, some formats may never work:

| Format | Likelihood | Solution |
|--------|-----------|----------|
| H.264 MP4 | ✅ Should work | None needed |
| H.265 MP4 | ⚠️ May not work | Install K-Lite |
| MKV | ⚠️ Depends | Install LAV Filters |
| VP9 WebM | ❌ Unlikely | Convert or use VLC backend |
| AV1 | ❌ Very unlikely | Convert or use VLC backend |

### Frozen Executable Limitations

- Plugins must be explicitly included
- PATH environment changes don't affect frozen app
- Qt plugin paths are fixed at build time
- System codec packs may not integrate with Qt

---

## Future Improvements

### Short Term
1. ✅ Bundle Qt multimedia plugins
2. ⏳ Test on clean Windows systems
3. ⏳ Document codec requirements
4. ⏳ Add codec detection/warning

### Long Term
1. Consider VLC backend for universal codec support
2. Add fallback to external player (VLC, MPC-HC)
3. Implement codec verification on startup
4. Bundle minimal codec set with application

---

## Summary

**The Issue:**
- QMediaPlayer uses Windows Media Foundation, NOT FFmpeg
- PyInstaller doesn't bundle Qt multimedia plugins by default
- Limited codec support without additional system codecs

**The Fix Applied:**
- ✅ Updated spec file to bundle Qt plugins
- ✅ Added better error reporting
- ✅ Added diagnostic logging

**Still Required (User Side):**
- May need K-Lite Codec Pack for H.265/HEVC videos
- May need LAV Filters for MKV files
- Basic H.264 MP4 should work without additional codecs

**Next Steps:**
1. Rebuild with updated spec file
2. Test with simple H.264 MP4 file
3. If still not working, share exact error message
4. May need to install system codec pack

---

## Quick Troubleshooting Checklist

- [ ] Rebuilt .exe with latest code
- [ ] File size increased (plugins included)
- [ ] Tested with simple H.264 MP4 file
- [ ] Checked console output for diagnostics
- [ ] Tried local file (not network path)
- [ ] Installed K-Lite Codec Pack (if needed)
- [ ] Checked status label for error message
- [ ] Verified FFmpeg is in PATH (for metadata)

---

*Documentation for video playback issues in PyQt5 frozen executable*
