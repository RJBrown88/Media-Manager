import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './components/App';

// Import global styles
import './styles/App.css';
import './styles/FileExplorer.css';
import './styles/RenamePanel.css';
import './styles/MediaPreview.css';
import './styles/StatusPanel.css';

const container = document.getElementById('root');
if (!container) {
  throw new Error('Failed to find root element');
}

const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
