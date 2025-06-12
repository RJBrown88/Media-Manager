import React, { useState, useEffect } from 'react';
import '../styles/RenamePanel.css';

interface MediaFile {
  path: string;
  metadata: {
    resolution: string;
    duration: string;
    codec: string;
  };
}

interface RenamePanelProps {
  file: MediaFile;
}

const RenamePanel: React.FC<RenamePanelProps> = ({ file }) => {
  const [template, setTemplate] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const [isStaged, setIsStaged] = useState(false);

  useEffect(() => {
    setTemplate('');
    setPreview(null);
    setIsStaged(false);
  }, [file]);

  const handlePreview = () => {
    window.api.send('rename', { 
      file: file.path, 
      template, 
      dryRun: true 
    });

    const handlePreviewResult = (response: { newName: string }) => {
      setPreview(response.newName);
    };

    window.api.receive('rename-result', handlePreviewResult);

    return () => {
      window.api.removeAllListeners('rename-result');
    };
  };

  const handleStage = () => {
    window.api.send('rename', { 
      file: file.path, 
      template, 
      dryRun: false 
    });

    const handleStageResult = () => {
      setIsStaged(true);
    };

    window.api.receive('rename-result', handleStageResult);

    return () => {
      window.api.removeAllListeners('rename-result');
    };
  };

  const handleCommit = () => {
    window.api.send('commit', {});
    setIsStaged(false);
  };

  const handleUndo = () => {
    window.api.send('undo', {});
    setIsStaged(false);
  };

  return (
    <div className="rename-panel">
      <h3>Rename File</h3>
      
      <div className="current-file">
        <strong>Current:</strong> {file.path}
      </div>

      <div className="template-input">
        <label>Template:</label>
        <input
          type="text"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          placeholder="{filename}_{resolution}"
        />
      </div>

      {preview && (
        <div className="preview">
          <strong>Preview:</strong> {preview}
        </div>
      )}

      <div className="template-help">
        <h4>Available Variables:</h4>
        <ul>
          <li>{'{filename}'} - Original filename without extension</li>
          <li>{'{resolution}'} - Video resolution (e.g. 1080p)</li>
          <li>{'{codec}'} - Video codec</li>
          <li>{'{duration}'} - Video duration</li>
        </ul>
      </div>

      <div className="actions">
        <button onClick={handlePreview} disabled={!template}>
          Preview
        </button>
        <button onClick={handleStage} disabled={!template || isStaged}>
          Stage
        </button>
        <button onClick={handleCommit} disabled={!isStaged}>
          Commit
        </button>
        <button onClick={handleUndo} disabled={!isStaged}>
          Undo
        </button>
      </div>
    </div>
  );
};

export default RenamePanel;
