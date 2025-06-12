import { ipcRenderer } from 'electron';

// Since contextIsolation is false, we can directly expose to window
declare global {
  interface Window {
    api: {
      send: (channel: string, data: any) => void;
      receive: (channel: string, func: (...args: any[]) => void) => void;
      removeAllListeners: (channel: string) => void;
    };
  }
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
window.api = {
  send: (channel: string, data: any) => {
    // whitelist channels
    const validChannels = ['scan', 'rename', 'preview', 'commit', 'undo', 'status'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  receive: (channel: string, func: (...args: any[]) => void) => {
    const validChannels = [
      'scan-result', 'rename-result', 'preview-result', 'commit-result', 'undo-result', 'status-result',
      'status-error', 'scan-error', 'rename-error', 'preview-error', 'commit-error', 'undo-error',
      'subtitle-search-error', 'subtitle-download-error', 'subtitle-validate-error'
    ];
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender` 
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  },
  removeAllListeners: (channel: string) => {
    const validChannels = [
      'scan-result', 'rename-result', 'preview-result', 'commit-result', 'undo-result', 'status-result',
      'status-error', 'scan-error', 'rename-error', 'preview-error', 'commit-error', 'undo-error',
      'subtitle-search-error', 'subtitle-download-error', 'subtitle-validate-error'
    ];
    if (validChannels.includes(channel)) {
      ipcRenderer.removeAllListeners(channel);
    }
  }
};
