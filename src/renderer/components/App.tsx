import React, { useEffect, useState } from 'react';
import FileExplorer from './FileExplorer';
import RenamePanel from './RenamePanel';
import MediaPreview from './MediaPreview';
import StatusPanel from './StatusPanel';
import '../styles/App.css';

// Browser-compatible path utilities
const getBasename = (filePath: string) => filePath.split(/[/\\]/).pop() || '';
const getExtname = (filePath: string) => {
  const match = filePath.match(/\.[^.]*$/);
  return match ? match[0] : '';
};
const joinPath = (...parts: string[]) => parts.join('/').replace(/\/+/g, '/');

interface CliStatus {
  version: string;
  platform: string;
  ffprobe: string;
  lastOperation?: {
    type: 'scan' | 'rename' | 'preview' | 'commit' | 'undo';
    timestamp: string;
    success: boolean;
  };
}

interface StatusError {
  message: string;
  details: any;
}

interface SubtitleInfo {
  language: string;
  path: string;
  validated: boolean;
}

interface SubtitleStream {
  index: number;
  language?: string;
  title?: string;
  codec: string;
}

interface MediaFile {
  path: string;
  metadata: {
    resolution: string;
    duration: string;
    codec: string;
    subtitle_streams?: SubtitleStream[];
  };
}

const App: React.FC = () => {
  const [status, setStatus] = useState<CliStatus | null>(null);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<StatusError | undefined>();
  const [isSearchingSubtitles, setIsSearchingSubtitles] = useState(false);

  useEffect(() => {
    console.log('App component mounted');
    
    // Check CLI status on startup
    try {
      console.log('Sending status command...');
      window.api.send('status', {});
    } catch (err) {
      console.error('Failed to send status command:', err);
      setError({
        message: 'Failed to communicate with backend',
        details: err
      });
      setIsLoading(false);
    }
    
    const handleStatus = (response: CliStatus) => {
      console.log('Status response received:', response);
      setStatus(response);
      setIsLoading(false);
      setError(undefined);
    };

    const handleError = (err: StatusError) => {
      console.error('Error received:', err);
      setError(err);
      setIsLoading(false);
    };

    // Set up listeners
    window.api.receive('status-result', handleStatus);
    window.api.receive('status-error', handleError);
    window.api.receive('scan-error', handleError);
    window.api.receive('rename-error', handleError);
    window.api.receive('preview-error', handleError);
    window.api.receive('commit-error', handleError);
    window.api.receive('undo-error', handleError);
    window.api.receive('subtitle-search-error', handleError);
    window.api.receive('subtitle-download-error', handleError);
    window.api.receive('subtitle-validate-error', handleError);

    return () => {
      window.api.removeAllListeners('status-result');
      window.api.removeAllListeners('status-error');
      window.api.removeAllListeners('scan-error');
      window.api.removeAllListeners('rename-error');
      window.api.removeAllListeners('preview-error');
      window.api.removeAllListeners('commit-error');
      window.api.removeAllListeners('undo-error');
      window.api.removeAllListeners('subtitle-search-error');
      window.api.removeAllListeners('subtitle-download-error');
      window.api.removeAllListeners('subtitle-validate-error');
    };
  }, []);

  // These methods are no longer needed with the simplified subtitle approach
  // They're kept as placeholders but not used in the UI
  const handleSubtitleSearch = async () => {
    // Open browser to OpenSubtitles instead of API integration
    if (!selectedFile) return;
    const filename = getBasename(selectedFile.path);
    const searchUrl = `https://www.opensubtitles.org/en/search/sublanguageid-all/moviename-${encodeURIComponent(filename)}`;
    window.open(searchUrl, '_blank');
  };

  const handleSubtitleDownload = async (lang: string) => {
    // No longer implemented - users download directly from OpenSubtitles
    console.log(`Download for ${lang} would happen via browser`);
  };

  const handleSubtitleValidate = async (path: string) => {
    // No longer implemented - validation happens locally
    console.log(`Validation for ${path} would happen locally`);
  };

  const handleFileScan = (directory: string) => {
    setError(undefined);
    window.api.send('scan', { directory });
    
    const handleScanResult = (response: { files: MediaFile[] }) => {
      setFiles(response.files);
      if (status) {
        setStatus({
          ...status,
          lastOperation: {
            type: 'scan',
            timestamp: new Date().toISOString(),
            success: true
          }
        });
      }
    };

    window.api.receive('scan-result', handleScanResult);
  };

  const handleFileSelect = (file: MediaFile) => {
    setSelectedFile(file);
  };

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        backgroundColor: '#f0f0f0'
      }}>
        Loading Media Manager...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        padding: '20px',
        color: '#ff4444',
        backgroundColor: '#ffeeee',
        border: '1px solid #ffcccc',
        margin: '20px',
        borderRadius: '4px'
      }}>
        <h3>Error</h3>
        <p>{error.message}</p>
        <pre>{JSON.stringify(error.details, null, 2)}</pre>
        <button onClick={() => setError(undefined)}>Dismiss</button>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="app-header">
        <StatusPanel 
          status={status} 
          error={error}
          onDismissError={() => setError(undefined)}
        />
      </div>
      <div className="app-main">
        <div className="app-sidebar">
          <FileExplorer 
            files={files} 
            onScan={handleFileScan}
            onFileSelect={handleFileSelect}
          />
        </div>
        <div className="app-content">
          {selectedFile && (
            <>
              <MediaPreview 
                file={selectedFile}
              />
              <RenamePanel file={selectedFile} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
