# Media Manager - Installation and Usage Guide

## System Requirements

- **Operating System**: Windows 10 or later
- **Disk Space**: At least 100MB of free disk space
- **Dependencies**: None (all dependencies are bundled with the application)

## Installation

1. **Download the Application**
   - Download the latest release from the releases page
   - The application is distributed as a Windows installer (.exe)

2. **Run the Installer**
   - Double-click the downloaded installer file
   - Follow the on-screen instructions to complete the installation
   - By default, the application will be installed to `C:\Program Files\Media Manager`

3. **First Launch**
   - Launch the application from the Start menu or desktop shortcut
   - On first launch, the application will create necessary configuration files

## Usage Guide

### Basic Workflow

The Media Manager follows a simple workflow:

1. **Scan Media Files**
   - Click the "Scan Directory" button in the File Explorer panel
   - Select a directory containing your media files
   - The application will scan the directory and display all media files

2. **Preview Media Files**
   - Click on any file in the list to preview it
   - The Media Preview panel will show file details and embedded subtitles
   - You can play the media file directly in the application

3. **Rename Files**
   - Select a file to rename
   - Use the Rename Panel to modify the filename
   - Click "Preview" to see the changes before applying
   - Click "Commit" to apply the changes

4. **Undo Operations**
   - If you need to revert changes, use the "Undo" button
   - The application keeps track of all rename operations

### Working with Subtitles

1. **View Embedded Subtitles**
   - Select a media file to view its embedded subtitle streams
   - The Media Preview panel will show all detected subtitle languages

2. **Find Additional Subtitles**
   - Click the "Find more subtitles" button to open OpenSubtitles in your browser
   - The search will be pre-populated with your media file information

### Tips and Tricks

- **Dark Mode**: The application uses a dark theme by default for comfortable viewing
- **File Formats**: Supports common media formats including .mp4, .mkv, .avi, and more
- **Keyboard Shortcuts**:
  - `Ctrl+Z`: Undo the last operation
  - `Ctrl+S`: Save current rename preview
  - `Esc`: Cancel current operation

## Troubleshooting

### Common Issues

1. **Application doesn't start**
   - Ensure your system meets the minimum requirements
   - Try reinstalling the application

2. **Media files not detected**
   - Verify the files are in supported formats
   - Check file permissions

3. **Subtitle streams not showing**
   - Ensure the media file has embedded subtitles
   - Some media files may have subtitles in formats not recognized by ffprobe

### Getting Help

If you encounter any issues not covered in this guide, please:
- Check the project repository for known issues
- Submit a new issue with detailed information about your problem

## Future Updates

The application will be regularly updated with new features. Upcoming features include:
- Batch operations for renaming multiple files with pattern-based rules
- Duplicate media file detection
- Enhanced subtitle management

Stay tuned for these exciting improvements!
