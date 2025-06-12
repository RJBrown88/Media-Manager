import React, { useEffect, useRef } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import '../styles/MediaPreview.css';

// Browser-compatible path utilities
const getBasename = (filePath: string) => filePath.split(/[/\\]/).pop() || '';
const getExtname = (filePath: string) => {
  const match = filePath.match(/\.[^.]*$/);
  return match ? match[0] : '';
};
const joinPath = (...parts: string[]) => parts.join('/').replace(/\/+/g, '/');

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

interface MediaPreviewProps {
  file: MediaFile;
}

const MediaPreview: React.FC<MediaPreviewProps> = ({ file }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<any>(null);

  const openSubtitleSearch = () => {
    const filename = getBasename(file.path);
    // Try to extract IMDB ID from filename (e.g., "Movie.Title.tt1234567.mkv")
    const imdbIdMatch = filename.match(/tt\d{7,8}/i);
    const imdbId = imdbIdMatch ? imdbIdMatch[0] : null;
    
    // Get filename without extension
    const nameWithoutExt = getBasename(file.path).replace(/\.[^/.]+$/, '');
    
    const searchUrl = imdbId 
      ? `https://www.opensubtitles.org/en/search/sublanguageid-all/imdbid-${imdbId}`
      : `https://www.opensubtitles.org/en/search/sublanguageid-all/moviename-${encodeURIComponent(nameWithoutExt)}`;
    
    // Open in default browser
    window.open(searchUrl, '_blank');
  };

  const getSubtitleDisplayName = (stream: SubtitleStream): string => {
    if (stream.language) {
      return stream.language;
    }
    if (stream.title) {
      if (stream.title.toLowerCase().includes('commentary')) {
        return 'Commentary';
      }
      if (stream.title.toLowerCase().includes('forced')) {
        return 'Forced';
      }
      return stream.title;
    }
    return `Track ${stream.index}`;
  };

  const getSubtitleCodecName = (codec: string): string => {
    const codecMap: { [key: string]: string } = {
      'srt': 'SubRip',
      'ass': 'Advanced SubStation Alpha',
      'ssa': 'SubStation Alpha',
      'pgs': 'HDMV PGS',
      'dvb_subtitle': 'DVB Subtitle',
      'hdmv_pgs_subtitle': 'HDMV PGS',
      'subrip': 'SubRip',
      'mov_text': 'QuickTime Text',
      'eia_608': 'EIA-608',
      'cea_608': 'CEA-608',
      'cea_708': 'CEA-708'
    };
    return codecMap[codec.toLowerCase()] || codec;
  };

  useEffect(() => {
    if (!videoRef.current) return;

    // Initialize video.js player
    playerRef.current = videojs(videoRef.current, {
      controls: true,
      fluid: true,
      sources: [{
        src: `file://${file.path}`,
        type: 'video/mp4' // Default to mp4, could be made dynamic based on file extension
      }]
    });

    // Cleanup on unmount
    return () => {
      if (playerRef.current) {
        playerRef.current.dispose();
      }
    };
  }, [file]);

  return (
    <div className="media-preview">
      <div className="video-container">
        <video
          ref={videoRef}
          className="video-js vjs-theme-dark"
        />
      </div>

      <div className="metadata-panel">
        <h3>File Details</h3>
        <table>
          <tbody>
            <tr>
              <td>Path:</td>
              <td className="file-path">{file.path}</td>
            </tr>
            <tr>
              <td>Resolution:</td>
              <td>{file.metadata.resolution}</td>
            </tr>
            <tr>
              <td>Duration:</td>
              <td>{file.metadata.duration}</td>
            </tr>
            <tr>
              <td>Codec:</td>
              <td>{file.metadata.codec}</td>
            </tr>
          </tbody>
        </table>

        <div className="subtitle-info">
          <div className="subtitle-header">
            <h3>Subtitles</h3>
            <button 
              className="find-subtitles-button"
              onClick={openSubtitleSearch}
              title="Search for additional subtitles on OpenSubtitles"
            >
              🔍 Find More
            </button>
          </div>
          
          {file.metadata.subtitle_streams && file.metadata.subtitle_streams.length > 0 ? (
            <div className="subtitle-streams">
              <div className="subtitle-count">
                📄 {file.metadata.subtitle_streams.length} embedded subtitle track{file.metadata.subtitle_streams.length !== 1 ? 's' : ''}
              </div>
              <div className="subtitle-list">
                {file.metadata.subtitle_streams.map((stream, index) => (
                  <div key={index} className="subtitle-stream-item">
                    <div className="subtitle-stream-info">
                      <span className="subtitle-language">
                        {getSubtitleDisplayName(stream)}
                      </span>
                      <span className="subtitle-codec">
                        {getSubtitleCodecName(stream.codec)}
                      </span>
                    </div>
                    <div className="subtitle-stream-details">
                      <span className="subtitle-index">Track {stream.index}</span>
                      {stream.title && (
                        <span className="subtitle-title" title={stream.title}>
                          {stream.title.length > 30 ? `${stream.title.substring(0, 30)}...` : stream.title}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-subtitles">
              <span className="no-subtitles-icon">📄</span>
              <span className="no-subtitles-text">No embedded subtitles found</span>
              <div className="no-subtitles-help">
                This file doesn't contain any subtitle tracks. Click "Find More" to search for external subtitles.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MediaPreview;
