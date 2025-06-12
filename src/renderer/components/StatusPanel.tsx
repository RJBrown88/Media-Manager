import React from 'react';
import '../styles/StatusPanel.css';

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

interface StatusPanelProps {
  status: CliStatus | null;
  error?: StatusError;
  onDismissError?: () => void;
}

const StatusPanel: React.FC<StatusPanelProps> = ({ status, error, onDismissError }) => {
  if (!status) {
    return (
      <div className="status-panel status-panel-error">
        <span className="status-icon">⚠️</span>
        <span>Failed to connect to CLI</span>
        {error && (
          <div className="status-error">
            <p>{error.message}</p>
            <button onClick={onDismissError} className="dismiss-error">
              Dismiss
            </button>
          </div>
        )}
      </div>
    );
  }

  const isFFprobeAvailable = status.ffprobe === 'ok';

  return (
    <div className={`status-panel ${isFFprobeAvailable ? 'status-panel-ok' : 'status-panel-warning'}`}>
      <div className="status-panel-content">
        <div className="status-item">
          <label>CLI Version:</label>
          <span>{status.version}</span>
        </div>
        
        <div className="status-item">
          <label>Platform:</label>
          <span>{status.platform}</span>
        </div>
        
        <div className="status-item">
          <label>FFprobe:</label>
          <span className={isFFprobeAvailable ? 'status-ok' : 'status-warning'}>
            {isFFprobeAvailable ? (
              <>
                <span className="status-icon">✓</span>
                Available
              </>
            ) : (
              <>
                <span className="status-icon">⚠️</span>
                Not Found
              </>
            )}
          </span>
        </div>

        {status.lastOperation && (
          <div className="status-item">
            <label>Last Operation:</label>
            <span className={status.lastOperation.success ? 'status-ok' : 'status-error'}>
              {status.lastOperation.type} - {status.lastOperation.success ? 'Success' : 'Failed'}
              <br />
              <small>{new Date(status.lastOperation.timestamp).toLocaleString()}</small>
            </span>
          </div>
        )}
      </div>

      {!isFFprobeAvailable && (
        <div className="status-message warning">
          Please install FFmpeg to enable media file analysis
        </div>
      )}

      {error && (
        <div className="status-error">
          <p>{error.message}</p>
          <button onClick={onDismissError} className="dismiss-error">
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default StatusPanel;
