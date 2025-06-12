# Media Manager Migration Plan

## Phase 3: Subtitle Integration - Simplification

### Migration Goals

1. **Remove API Integration Complexity**
   - Replace API-dependent implementation with local-first approach
   - Eliminate API key management
   - Remove network calls and associated error handling
   - Simplify test infrastructure

2. **Focus on Core Value**
   - Detect and display embedded subtitle streams
   - Provide direct access to OpenSubtitles website when needed
   - Maintain existing scan/rename/preview workflow
   - Keep Video.js integration for media preview

### Migration Steps

#### 1. Remove API Integration Code

- **subtitles.rs**
  - Remove OpenSubtitles API client code
  - Remove download, search, and validation functionality
  - Replace with simple SubtitleStream structure
  - Remove test mode and mocking infrastructure

- **config.rs**
  - Remove API key management
  - Simplify Config struct
  - Remove validation and persistence for API keys

- **CLI Commands**
  - Remove subtitle search/download/validate commands
  - Remove API key configuration commands
  - Simplify status command to remove API key reporting

- **Test Infrastructure**
  - Remove TestHarness complexity
  - Delete API-dependent tests
  - Remove environment variable management for API testing

#### 2. Extend Scan Phase

- **metadata.rs**
  - Add SubtitleStream struct to store subtitle metadata
  - Extend MediaMetadata to include subtitle_streams field
  - Update ffprobe parsing to extract subtitle stream information

- **media_file.rs**
  - Ensure MediaFile properly includes subtitle metadata

- **scanner.rs**
  - Update scan_directory to include subtitle stream detection
  - Ensure subtitle metadata is properly populated during scanning

#### 3. Update GUI Integration

- **MediaPreview.tsx**
  - Replace API-dependent subtitle controls with embedded subtitle display
  - Add "Find more subtitles" button that opens browser to OpenSubtitles
  - Update interface to show language information in user-friendly format
  - Extract IMDB ID from filename patterns when possible

- **cliBridge.ts**
  - Remove API-related IPC handlers
  - Keep existing scan/rename/preview/commit operations

### Migration Benefits

1. **Reduced Complexity**
   - Fewer dependencies
   - No external API calls
   - Simpler error handling
   - Less test infrastructure

2. **Improved Reliability**
   - Local-first approach
   - No rate limits or API availability concerns
   - Fewer points of failure
   - More predictable behavior

3. **Better User Experience**
   - Immediate subtitle information
   - Direct access to OpenSubtitles when needed
   - Consistent UI
   - Faster media scanning

4. **Easier Maintenance**
   - Simpler code structure
   - Reduced test complexity
   - More focused functionality
   - Fewer moving parts

### Migration Risks and Mitigations

1. **Loss of Automatic Subtitle Download**
   - **Mitigation**: Provide direct link to OpenSubtitles for manual download
   - **Benefit**: Eliminates API key management and rate limit concerns

2. **Reduced Subtitle Metadata**
   - **Mitigation**: Focus on essential information (language, codec)
   - **Benefit**: Simpler UI with focus on what users care about most

3. **Test Infrastructure Changes**
   - **Mitigation**: Simplify tests to focus on core functionality
   - **Benefit**: More reliable test suite with fewer dependencies

### Post-Migration Verification

1. **Core Functionality**
   - Verify scan correctly identifies subtitle streams
   - Ensure MediaPreview displays subtitle information
   - Confirm "Find more subtitles" button works correctly
   - Test Video.js player with embedded subtitles

2. **Removed Functionality**
   - Confirm API-dependent code is completely removed
   - Verify no API key management remains
   - Ensure tests don't depend on removed functionality
   - Check for any lingering references to API integration

### Future Considerations

While this migration simplifies the subtitle handling, future enhancements could include:

1. Local subtitle file management (without API dependency)
2. Better subtitle format detection and compatibility
3. Enhanced metadata extraction from embedded subtitles
4. Improved IMDB ID detection for more accurate OpenSubtitles linking

These enhancements would maintain the simplified, local-first approach while adding value for users.
