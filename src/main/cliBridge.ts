import { ipcMain } from 'electron';
import { spawn } from 'child_process';
import * as path from 'path';
import isDev from 'electron-is-dev';

// Note: Subtitle API-related IPC handlers have been removed in the simplified version

// Get the path to the CLI executable
const getCliPath = () => {
  if (isDev) {
    return path.join(process.cwd(), 'target/debug/media_manager_cli.exe');
  }
  return path.join(process.resourcesPath, 'bin/media_manager_cli.exe');
};

// Execute CLI command and return JSON response
const executeCliCommand = async (args: string[]): Promise<any> => {
  return new Promise((resolve, reject) => {
    const cliProcess = spawn(getCliPath(), args);
    let stdout = '';
    let stderr = '';

    cliProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    cliProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    cliProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (error) {
          reject(new Error(`Failed to parse CLI output: ${stdout}`));
        }
      } else {
        reject(new Error(`CLI command failed: ${stderr}`));
      }
    });

    cliProcess.on('error', (error) => {
      reject(new Error(`Failed to start CLI process: ${error.message}`));
    });
  });
};

// Set up IPC handlers
export const setupCliHandlers = () => {
  // Get CLI status
  ipcMain.on('status', async (event) => {
    try {
      const result = await executeCliCommand(['status']);
      event.reply('status-result', result);
    } catch (error) {
      console.error('Status command failed:', error);
      event.reply('status-error', {
        message: error instanceof Error ? error.message : 'Failed to get CLI status',
        details: error
      });
      event.reply('status-result', null);
    }
  });

  // Scan directory
  ipcMain.on('scan', async (event, { directory }) => {
    try {
      const result = await executeCliCommand(['scan', directory]);
      event.reply('scan-result', result);
    } catch (error) {
      console.error('Scan command failed:', error);
      event.reply('scan-error', {
        message: error instanceof Error ? error.message : 'Failed to scan directory',
        details: error
      });
      event.reply('scan-result', { files: [] });
    }
  });

  // Rename file
  ipcMain.on('rename', async (event, { file, template, dryRun }) => {
    try {
      const args = ['rename', file, template];
      if (dryRun) {
        args.push('--dry-run');
      }
      const result = await executeCliCommand(args);
      event.reply('rename-result', result);
    } catch (error) {
      console.error('Rename command failed:', error);
      event.reply('rename-error', {
        message: error instanceof Error ? error.message : 'Failed to rename file',
        details: error
      });
      event.reply('rename-result', null);
    }
  });

  // Preview staged changes
  ipcMain.on('preview', async (event) => {
    try {
      const result = await executeCliCommand(['preview']);
      event.reply('preview-result', result);
    } catch (error) {
      console.error('Preview command failed:', error);
      event.reply('preview-error', {
        message: error instanceof Error ? error.message : 'Failed to preview changes',
        details: error
      });
      event.reply('preview-result', null);
    }
  });

  // Commit staged changes
  ipcMain.on('commit', async (event) => {
    try {
      const result = await executeCliCommand(['commit']);
      event.reply('commit-result', result);
    } catch (error) {
      console.error('Commit command failed:', error);
      event.reply('commit-error', {
        message: error instanceof Error ? error.message : 'Failed to commit changes',
        details: error
      });
      event.reply('commit-result', null);
    }
  });

  // Undo last batch
  ipcMain.on('undo', async (event) => {
    try {
      const result = await executeCliCommand(['undo']);
      event.reply('undo-result', result);
    } catch (error) {
      console.error('Undo command failed:', error);
      event.reply('undo-error', {
        message: error instanceof Error ? error.message : 'Failed to undo changes',
        details: error
      });
      event.reply('undo-result', null);
    }
  });
};
