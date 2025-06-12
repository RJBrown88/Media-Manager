import React, { useCallback } from 'react';
import '../styles/FileExplorer.css';

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

interface FileExplorerProps {
  files: MediaFile[];
  onScan: (directory: string) => void;
  onFileSelect: (file: MediaFile) => void;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ files, onScan, onFileSelect }) => {
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const items = Array.from(e.dataTransfer.items);
    const directories = items
      .filter(item => item.kind === 'file')
      .map(item => item.webkitGetAsEntry())
      .filter((entry): entry is FileSystemDirectoryEntry => entry !== null && entry.isDirectory);

    if (directories.length > 0) {
      onScan(directories[0].fullPath);
    }
  }, [onScan]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleBrowse = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true;
    
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files.length > 0) {
        // Use webkitRelativePath to get the directory path
        const directory = target.files[0].webkitRelativePath.split('/')[0];
        onScan(directory);
      }
    };

    input.click();
  }, [onScan]);

  const getSubtitleSummary = (subtitleStreams?: SubtitleStream[]): string => {
    if (!subtitleStreams || subtitleStreams.length === 0) {
      return 'No subs';
    }
    
    const languages = subtitleStreams
      .map(stream => stream.language || 'Unknown')
      .filter((lang, index, arr) => arr.indexOf(lang) === index) // Remove duplicates
      .slice(0, 2); // Show max 2 languages
    
    if (languages.length === 1) {
      return `${subtitleStreams.length} sub (${languages[0]})`;
    } else if (languages.length === 2) {
      return `${subtitleStreams.length} subs (${languages.join(', ')})`;
    } else {
      return `${subtitleStreams.length} subs`;
    }
  };

  return (
    <div className="file-explorer">
      <div className="file-explorer-header">
        <h2>Media Files</h2>
        <button onClick={handleBrowse}>Browse</button>
      </div>

      <div
        className="file-explorer-dropzone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        Drop a folder here or click Browse
      </div>

      <div className="file-list">
        {files.map((file, index) => (
          <div
            key={index}
            className="file-item"
            onClick={() => onFileSelect(file)}
          >
            <div className="file-name">{file.path.split('/').pop()}</div>
            <div className="file-meta">
              <span className="file-resolution">{file.metadata.resolution}</span>
              <span className="file-duration">{file.metadata.duration}</span>
              <span className="file-codec">{file.metadata.codec}</span>
              <span className="file-subtitles">{getSubtitleSummary(file.metadata.subtitle_streams)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileExplorer;
