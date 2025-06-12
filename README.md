<<<<<<< HEAD
# Media-Manager
=======
# Granular Media Manager

A local-first media organization tool with a Rust CLI backend and an Electron-based GUI frontend.

## Current Status

**✅ Working Features:**
- Media file scanning with FFprobe metadata extraction
- Embedded subtitle stream detection and display
- Basic file renaming operations (staging, preview, commit, undo)
- Electron GUI with file explorer and media preview
- Local-first architecture (no external API dependencies)

**🔄 In Progress:**
- Enhanced subtitle display in GUI
- Improved file operations workflow

## Features

- **Media Scanning**: Recursive directory scanning with FFprobe metadata extraction
- **Subtitle Detection**: Automatic detection of embedded subtitle streams
- **File Renaming**: Pattern-based renaming with staging workflow
- **Electron GUI**: Modern interface with file explorer and media preview
- **Local-First**: No external API dependencies, works entirely offline

## Development Setup

### Prerequisites

- Rust (latest stable)
- Node.js (v16 or later)
- FFmpeg (for media metadata extraction)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/media-manager.git
cd media-manager
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Build Rust components:
```bash
cargo build
```

### Development

Run the development server:
```bash
npm run dev
```

Build for production:
```bash
npm run build
```

## Testing

### Running Tests

Run Rust tests:
```bash
cargo test
```

Run GUI tests:
```bash
npm test
```

### Test Coverage

- CLI command functionality
- JSON output format validation
- Basic error handling

## Usage

### CLI Commands

```bash
# Check system status
media_manager_cli status

# Scan directory for media files
media_manager_cli scan /path/to/media

# Rename a file
media_manager_cli rename "movie.mp4" "{filename} [{resolution}]"

# Preview staged changes
media_manager_cli preview

# Apply staged changes
media_manager_cli commit

# Undo last batch
media_manager_cli undo
```

### GUI Usage

1. Launch the application
2. Use "Browse" or drag-and-drop to select a media directory
3. Click on files to view metadata and subtitle information
4. Use the rename panel to modify filenames
5. Preview and commit changes

## Project Structure

```
media_manager_core/      # Core Rust library
├── src/
│   ├── config.rs       # Configuration system
│   ├── subtitles.rs    # Subtitle management (simplified)
│   ├── media_file.rs   # Media file handling
│   ├── metadata.rs     # FFprobe metadata extraction
│   └── ...
media_manager_cli/      # CLI interface
├── src/
│   └── main.rs        # CLI entry point
└── tests/             # CLI tests
src/                   # Electron/React GUI
├── main/             # Electron main process
├── renderer/         # React components
│   ├── components/   # UI components
│   └── styles/       # CSS modules
└── __tests__/       # GUI tests
```

## Architecture

- **Rust Backend**: Core media processing and file operations
- **Electron Frontend**: Modern GUI built with React
- **IPC Bridge**: Communication between GUI and CLI
- **FFprobe Integration**: Media metadata extraction
- **Local Storage**: Configuration and undo data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License
>>>>>>> 7a48c74 (Initial commit: Media Manager application with Rust backend and Electron frontend)
