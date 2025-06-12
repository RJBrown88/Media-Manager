# Media Manager Build Guide

This guide provides detailed instructions for building and troubleshooting the Media Manager application.

## Prerequisites

1. **Node.js** (v16 or higher)
2. **Rust** (latest stable version)
3. **npm** or **yarn**
4. **Windows Build Tools** (for Windows users)

## Build Process

### 1. Install Dependencies

```bash
npm install
```

### 2. Build the Application

The build process consists of several steps:

```bash
# Full build (Rust CLI + Electron app)
npm run build

# Or build components separately:
npm run build:rust      # Build Rust CLI
npm run build:main      # Build Electron main process
npm run build:renderer  # Build Electron renderer process
```

### 3. Verify Build

After building, verify all files are created correctly:

```bash
npm run verify-build
```

Expected output structure:
```
dist/
├── main.js          # Main process bundle
├── preload.js       # Preload script
└── renderer/
    ├── index.html   # Renderer HTML
    └── main.js      # Renderer JavaScript bundle

target/release/
└── media_manager_cli.exe  # Rust CLI executable
```

### 4. Package the Application

To create a distributable package:

```bash
# For Windows
npm run package:win

# For all platforms
npm run package
```

## Development Mode

For development with hot-reload:

```bash
npm run dev
```

This will:
1. Start webpack in watch mode for main process
2. Start webpack dev server for renderer process
3. Launch Electron when ready

## Troubleshooting

### Issue: "Failed to load application" in production

**Symptoms:**
- Application shows error page instead of UI
- Console shows "Could not find renderer HTML file"

**Solutions:**

1. **Check build output:**
   ```bash
   npm run verify-build
   ```

2. **Rebuild from clean state:**
   ```bash
   npm run rebuild
   ```

3. **Enable debug mode:**
   ```bash
   # Windows
   set DEBUG_PROD=true && npm start
   
   # macOS/Linux
   DEBUG_PROD=true npm start
   ```

4. **Check console logs:**
   - The enhanced main.ts now logs all paths it attempts
   - Look for "Found renderer HTML at:" message
   - Check the debug information shown in the error page

### Issue: "Preload script not found"

**Symptoms:**
- Console error about missing preload.js
- IPC communication not working

**Solutions:**

1. Ensure webpack builds the preload script:
   - Check webpack.main.config.js has preload entry
   - Verify dist/preload.js exists after build

2. Check the preload path in main.ts matches the build output

### Issue: Missing Rust CLI

**Symptoms:**
- Build verification fails for media_manager_cli.exe
- CLI commands not working in the app

**Solutions:**

1. Build Rust CLI separately:
   ```bash
   cargo build --release
   ```

2. Ensure Rust is installed and in PATH:
   ```bash
   rustc --version
   cargo --version
   ```

### Issue: IPC Channel Errors

**Symptoms:**
- "Channel not allowed" errors
- Features not responding to clicks

**Solutions:**

1. Verify all channels are whitelisted in preload.ts
2. Check that App.tsx listeners match preload channels
3. Ensure error channels are included for all operations

## Build Configuration Files

### webpack.main.config.js
- Builds main process and preload script
- Entry points: main.ts and preload.ts
- Output: dist/main.js and dist/preload.js

### webpack.renderer.config.js
- Builds renderer process
- Entry point: src/renderer/index.tsx
- Output: dist/renderer/
- Includes HtmlWebpackPlugin for index.html

### package.json
- Build scripts and dependencies
- Electron Builder configuration
- Extra resources configuration for Rust CLI

## Production Path Resolution

The application uses a multi-path resolution strategy in production:

1. Standard webpack output structure
2. Electron-builder packed app structure
3. Development build paths
4. Absolute path fallback

The main.ts file logs all attempted paths for debugging.

## Environment Variables

- `NODE_ENV`: Set to 'production' or 'development'
- `DEBUG_PROD`: Set to 'true' to enable DevTools in production

## Clean Build Steps

If you encounter persistent issues:

```bash
# 1. Clean all build artifacts
npm run clean

# 2. Clear npm cache
npm cache clean --force

# 3. Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# 4. Rebuild everything
npm run build

# 5. Verify build
npm run verify-build
```

## Additional Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Webpack Documentation](https://webpack.js.org/concepts/)
- [Rust Book](https://doc.rust-lang.org/book/)
