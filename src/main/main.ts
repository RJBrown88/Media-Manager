import { app, BrowserWindow } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import isDev from 'electron-is-dev';
import { setupCliHandlers } from './cliBridge';

let mainWindow: BrowserWindow | null = null;

// Helper function to find the renderer HTML file
function findRendererHtml(): string | null {
  const possiblePaths = [
    // Standard webpack output structure
    path.join(__dirname, '../renderer/index.html'),
    path.join(__dirname, 'renderer/index.html'),
    // Electron-builder packed app structure
    path.join(process.resourcesPath, 'app/dist/renderer/index.html'),
    path.join(process.resourcesPath, 'dist/renderer/index.html'),
    // Development build
    path.join(__dirname, '../../dist/renderer/index.html'),
    // Absolute path as last resort
    path.resolve('./dist/renderer/index.html')
  ];

  console.log('Searching for renderer HTML file...');
  console.log('__dirname:', __dirname);
  console.log('process.resourcesPath:', process.resourcesPath);
  console.log('app.getAppPath():', app.getAppPath());

  for (const htmlPath of possiblePaths) {
    console.log(`Checking: ${htmlPath}`);
    if (fs.existsSync(htmlPath)) {
      console.log(`Found renderer HTML at: ${htmlPath}`);
      return htmlPath;
    }
  }

  console.error('Could not find renderer HTML file in any of the expected locations');
  return null;
}

function createWindow() {
  console.log('Creating main window...');
  console.log('isDev:', isDev);
  
  // Ensure preload script path is correct
  const preloadPath = isDev 
    ? path.join(__dirname, 'preload.js')
    : path.join(__dirname, 'preload.js');
    
  console.log('Preload script path:', preloadPath);
  
  if (!fs.existsSync(preloadPath)) {
    console.error('Preload script not found at:', preloadPath);
  }

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath
    }
  });

  // Load the app
  if (isDev) {
    console.log('Loading development server at http://localhost:3000');
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    const htmlPath = findRendererHtml();
    
    if (htmlPath) {
      console.log('Loading production HTML from:', htmlPath);
      mainWindow.loadFile(htmlPath).catch(error => {
        console.error('Failed to load HTML file:', error);
        // Show error in the window
        mainWindow?.webContents.executeJavaScript(`
          document.body.innerHTML = '<div style="padding: 20px; font-family: sans-serif;">
            <h1>Failed to load application</h1>
            <p>Error: ${error.message}</p>
            <p>Attempted path: ${htmlPath}</p>
            <p>Please check the console for more details.</p>
          </div>';
        `);
      });
    } else {
      // Show error page if no HTML file found
      console.error('No HTML file found, showing error page');
      mainWindow.loadURL(`data:text/html,
        <html>
          <body style="padding: 20px; font-family: sans-serif;">
            <h1>Failed to load application</h1>
            <p>Could not find the renderer HTML file.</p>
            <p>Please ensure the application was built correctly.</p>
            <details>
              <summary>Debug Information</summary>
              <pre>
__dirname: ${__dirname}
resourcesPath: ${process.resourcesPath}
appPath: ${app.getAppPath()}
              </pre>
            </details>
          </body>
        </html>
      `);
    }
    
    // Open DevTools in production for debugging
    if (process.env.DEBUG_PROD === 'true') {
      mainWindow.webContents.openDevTools();
    }
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Log when the window is ready
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Window finished loading');
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Window failed to load:', errorCode, errorDescription);
  });
}

app.whenReady().then(() => {
  createWindow();
  setupCliHandlers();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
