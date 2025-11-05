# Video Manager

A PyQt5-based video file manager optimized for managing large video collections on Windows network shares (UNC paths). Features smart caching, on-demand thumbnail generation, direct network streaming, and efficient batch operations.

## Features

### Smart Caching
- **Metadata-only caching**: Stores file metadata in SQLite database without copying video files
- **LRU thumbnail cache**: Automatically manages thumbnail cache with configurable size limits
- **Automatic pruning**: Keeps cache size under control with intelligent eviction
- **Fast database**: SQLite with WAL mode for concurrent access

### Network Optimization
- **Direct streaming**: Videos stream directly from network shares without local copies
- **Minimal data transfer**: Reads only file headers for metadata extraction
- **Parallel operations**: Configurable thread pool for metadata extraction
- **Bandwidth limiting**: Optional bandwidth throttling for file operations
- **UNC path support**: Full support for Windows UNC paths (\\\\server\\share\\videos)

### Video Management
- **Progressive scanning**: Displays files immediately, enriches metadata asynchronously
- **On-demand thumbnails**: Generates thumbnails only when needed
- **Direct preview**: Stream videos directly from network without buffering entire file
- **Metadata extraction**: Extracts duration, resolution, codec using FFmpeg
- **Large file support**: Handles files from 100MB to 15GB efficiently

### File Operations
- **Smart rename**: Renames files on server without local copy
- **Efficient move**: Uses server-side rename when possible (same share)
- **Streaming copy**: Copies large files in chunks with progress reporting
- **Batch operations**: Process multiple files with dry-run preview
- **Undo support**: Reverse operations for rename and move

### User Interface
- **Virtual scrolling**: Efficiently displays thousands of files
- **Sortable columns**: Sort by name, size, duration, resolution, codec
- **Metadata panel**: Shows detailed file information and thumbnails
- **Video preview**: Built-in player with playback controls
- **Operations queue**: Monitor ongoing operations with progress and ETA
- **Settings dialog**: Adjust cache, network, and UI settings

## System Requirements

### Required
- **OS**: Windows 7 or later (designed for Windows UNC path access)
- **Python**: 3.8 or later
- **FFmpeg**: For video metadata extraction and thumbnail generation
- **Network**: Access to network shares (SMB/CIFS)

### Recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 5-25GB for cache (configurable)
- **Network**: Gigabit Ethernet for smooth video streaming

## Installation

### 1. Install Python
Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

### 2. Install FFmpeg
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add FFmpeg bin directory to PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System Variables", select "Path" and click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - Click OK on all dialogs

4. Verify installation:
   ```bash
   ffmpeg -version
   ffprobe -version
   ```

### 3. Install Video Manager

#### Option A: Install from source
```bash
# Clone repository
git clone https://github.com/yourusername/video-manager.git
cd video-manager

# Install dependencies
pip install -r requirements.txt

# Run application
python run.py
```

#### Option B: Install as package
```bash
# Install from source
pip install .

# Run application
video-manager
```

#### Option C: Windows Executable (No Python Required)

For Windows users who don't want to install Python:

1. Download the pre-built executable from Releases
2. Extract `VideoManager.exe`
3. Install FFmpeg (see step 2 above)
4. Run `VideoManager.exe`

**Building the executable yourself:**
```bash
# On Windows with Python installed
build.bat

# Or manually
python build.py

# Executable will be in: distribution/VideoManager.exe
```

See [BUILD_WINDOWS.md](BUILD_WINDOWS.md) for detailed build instructions.

## Configuration

### First Launch
On first launch, Video Manager creates a configuration file at:
```
%LOCALAPPDATA%\VideoManager\config.json
```

### Default Settings
- **Cache directory**: `%LOCALAPPDATA%\VideoManager\cache`
- **Max cache size**: 5 GB
- **Thumbnail quality**: 80%
- **Max thumbnails**: 500
- **Network timeout**: 30 seconds
- **Chunk size**: 64 MB
- **Bandwidth limit**: Unlimited

### Adjusting Settings
1. Open application
2. Go to File → Settings
3. Adjust settings in Cache, Network, and Interface tabs
4. Click Save

## Usage Guide

### Scanning a Directory

1. **Enter UNC Path**:
   ```
   \\server\share\videos
   ```
   Or click "Browse..." to select directory

2. **Click "Scan"**:
   - Choose whether to generate thumbnails during scan
   - Files appear immediately, metadata loads asynchronously
   - Progress shown in status bar

3. **Wait for Completion**:
   - Initial scan adds files to database
   - Background threads extract metadata
   - Cache is automatically managed

### Viewing Files

- **File List**: Shows all videos with metadata
- **Sort**: Click column headers to sort
- **Select**: Click file to view metadata
- **Preview**: Double-click file to stream video

### File Operations

#### Rename
1. Select file
2. Click "Rename"
3. Enter new name
4. Confirm

#### Move
1. Select file
2. Click "Move"
3. Choose destination directory
4. Operation executes with progress indicator

#### Delete
1. Select file
2. Click "Delete"
3. Confirm deletion

### Batch Operations

1. Select multiple files (Ctrl+Click or Shift+Click)
2. Choose operation (Rename, Move, Copy)
3. Review dry-run results
4. Confirm execution
5. Monitor in Operations Queue

### Generating Thumbnails

**For Single File**:
1. Select file
2. Click "Generate Thumbnail"
3. Thumbnail appears in metadata panel

**For All Files**:
1. Rescan directory with thumbnail generation enabled
2. Or generate individually as needed

### Managing Cache

**View Statistics**:
- Cache → Cache Statistics

**Prune Cache**:
- Cache → Prune Cache
- Removes oldest thumbnails to meet size limits

**Clear Cache**:
- Cache → Clear Cache
- Removes all cached thumbnails and metadata

## Performance Tips

### For Large Collections (>10,000 files)

1. **Increase cache size**: 10-25 GB for better thumbnail caching
2. **Disable thumbnail generation during scan**: Generate on-demand instead
3. **Use filters**: Scan subdirectories separately
4. **Adjust parallel threads**: 2-3 threads for better performance

### For Slow Networks

1. **Reduce network timeout**: Lower to 15-20 seconds
2. **Decrease chunk size**: 32 MB for better responsiveness
3. **Enable bandwidth limiting**: Prevent network saturation
4. **Skip deep scans**: Disable for files >5GB

### For Limited Storage

1. **Reduce max cache size**: 1-2 GB minimum
2. **Lower thumbnail quality**: 60-70%
3. **Decrease max thumbnails**: 100-200
4. **Enable automatic pruning**: Set threshold to 80% of max

## Architecture

### Components

```
video_manager/
├── core/                      # Core functionality
│   ├── config.py             # Configuration management
│   ├── database.py           # SQLite database with WAL mode
│   ├── cache_manager.py      # LRU cache with size monitoring
│   ├── metadata_extractor.py # FFmpeg-based metadata extraction
│   ├── thumbnail_generator.py # On-demand thumbnail generation
│   ├── file_scanner.py       # Progressive directory scanning
│   ├── file_operations.py    # Network-optimized file operations
│   └── batch_operations.py   # Batch processing with undo
├── ui/                        # User interface
│   ├── main_window.py        # Main application window
│   ├── file_list_model.py    # Virtual scrolling table model
│   ├── video_preview.py      # QMediaPlayer-based preview
│   ├── metadata_panel.py     # File information display
│   ├── operations_queue.py   # Operations monitoring
│   └── settings_dialog.py    # Settings configuration
└── utils/                     # Utility functions
```

### Data Flow

1. **Scan**: File scanner lists directory → Adds basic info to database
2. **Enrich**: Background threads extract metadata → Updates database
3. **Display**: Virtual scrolling loads visible rows → Shows in UI
4. **Preview**: Direct stream from network → QMediaPlayer
5. **Thumbnail**: On-demand generation → Cached in database

### Cache Strategy

- **Metadata**: Always cached (file path, size, duration, resolution, codec)
- **Thumbnails**: LRU cache with configurable limit
- **Video data**: Never cached (streams directly)

## Troubleshooting

### FFmpeg not found
**Error**: "FFmpeg not found" or thumbnail generation fails

**Solution**:
1. Verify FFmpeg installation: `ffmpeg -version`
2. Check PATH environment variable
3. Restart application after installing FFmpeg

### Network access denied
**Error**: "Access denied" when accessing UNC path

**Solution**:
1. Verify network credentials
2. Map network drive and use drive letter
3. Check firewall settings
4. Ensure SMB/CIFS is enabled

### Slow scanning
**Issue**: Directory scan takes too long

**Solution**:
1. Disable thumbnail generation during scan
2. Reduce parallel metadata threads
3. Increase network timeout
4. Scan subdirectories separately

### High memory usage
**Issue**: Application uses too much RAM

**Solution**:
1. Reduce "Thumbnails in Memory" setting
2. Lower "Files Per Page" setting
3. Clear cache regularly
4. Close video preview when not in use

### Database locked
**Error**: "Database is locked"

**Solution**:
1. Close other instances of application
2. Delete `.db-wal` and `.db-shm` files in cache directory
3. Restart application

## Known Limitations

1. **Windows only**: Designed for Windows UNC paths
2. **FFmpeg required**: External dependency for video processing
3. **No streaming preview on some codecs**: Some proprietary codecs may not stream
4. **Large thumbnails**: >15GB files may timeout during thumbnail generation
5. **No multi-user**: Database not designed for concurrent multi-user access

## Future Enhancements

- [ ] Video tagging and categories
- [ ] Advanced search and filtering
- [ ] Duplicate detection
- [ ] Multi-format export (CSV, JSON)
- [ ] Playlist creation
- [ ] Network bandwidth monitoring
- [ ] Cloud storage support (OneDrive, Google Drive)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/yourusername/video-manager/issues)
- Documentation: See this README

## Credits

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Video processing by [FFmpeg](https://ffmpeg.org/)
- Image processing by [Pillow](https://python-pillow.org/)

## Changelog

### Version 1.0.0 (2025-11-05)
- Initial release
- Smart caching with LRU eviction
- Network-optimized operations
- Progressive scanning
- On-demand thumbnail generation
- Direct video streaming
- Batch operations with undo
- Virtual scrolling for large datasets
