# Media Manager Project Context

## Current Implementation Status

### ✅ Completed Features

1. **Simplified Subtitle Integration**
   - Removed OpenSubtitles API dependencies
   - Local subtitle stream detection via FFprobe
   - Basic IMDB ID extraction from filenames
   - Simple OpenSubtitles URL generation

2. **Core Infrastructure**
   - Rust workspace with core library and CLI
   - Electron/React GUI with proper IPC bridge
   - FFprobe integration for media metadata
   - JSON-based CLI output for GUI integration

3. **GUI Components**
   - Enhanced subtitle display in MediaPreview
   - File explorer with subtitle summary
   - Status panel with system information
   - Dark mode support and responsive design

4. **Simplified Testing**
   - Removed overengineered TestHarness
   - Basic CLI command tests
   - JSON output validation
   - Simple, maintainable test structure

### 🔄 Current Focus

**End-to-End File Scanning with Subtitle Detection**

The primary goal is to get the complete file scanning workflow working:

1. **CLI Scan Command**: Returns proper JSON with subtitle data
2. **GUI Integration**: Displays subtitle information from scan results
3. **Real Metadata Extraction**: FFprobe integration working correctly
4. **Data Flow**: Complete pipeline from CLI to GUI display

### 🎯 Next Steps

1. **Verify Data Flow**: Ensure CLI scan output matches GUI expectations
2. **Test with Real Files**: Validate subtitle detection with actual media files
3. **Improve Error Handling**: Better handling of FFprobe failures
4. **Enhance GUI**: Polish subtitle display and user experience

## Architecture Overview

### Simplified Approach Benefits

- **No External Dependencies**: Works entirely offline
- **Faster Performance**: No API calls or network delays
- **Reliable**: No rate limits or service availability issues
- **Maintainable**: Simpler codebase with fewer moving parts

### Data Flow

```
Media Files → FFprobe → MediaMetadata → CLI JSON → GUI Display
```

1. **Scan Phase**: FFprobe extracts metadata including subtitle streams
2. **CLI Output**: JSON format with subtitle information
3. **GUI Display**: Enhanced subtitle information display
4. **User Actions**: "Find More" button opens OpenSubtitles in browser

### Core Components

- **media_manager_core**: Core library with metadata extraction
- **media_manager_cli**: Command-line interface with JSON output
- **Electron GUI**: React-based interface with subtitle display
- **IPC Bridge**: Communication between GUI and CLI

## Development Philosophy

- **Local-First**: All processing happens locally
- **Simple & Reliable**: Minimal dependencies, maximum reliability
- **User-Focused**: Direct access to external services when needed
- **Maintainable**: Clean, well-tested code structure

## Future Enhancements

### Phase 4: Extended Functionality

1. **Batch Operations**: Pattern-based renaming for multiple files
2. **Duplicate Detection**: Identify potential duplicate media files
3. **Enhanced Metadata**: Additional media information extraction
4. **Performance Optimization**: Faster scanning and processing

### Benefits of Current Approach

- **Immediate Value**: Users get subtitle information instantly
- **No Setup Required**: Works out of the box
- **Consistent Experience**: Reliable performance regardless of network
- **Easy Maintenance**: Fewer dependencies and simpler code
