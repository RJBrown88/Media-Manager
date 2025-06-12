import React from 'react';
import { render, screen } from '@testing-library/react';
import MediaPreview from '../MediaPreview';
import videojs from 'video.js';

// Create mock implementation of video.js
const mockDispose = jest.fn();
const mockPlayer = {
  dispose: mockDispose
};

// Mock video.js module with all required static methods
jest.mock('video.js', () => {
  const mockVideojs = jest.fn(() => mockPlayer);
  
  // Add required static methods
  Object.assign(mockVideojs, {
    // Mock required static methods
    getPlayers: () => ({}),
    getPlayer: () => null,
    getAllPlayers: () => [],
    registerComponent: jest.fn(),
    registerPlugin: jest.fn(),
    // Add mock tracking properties
    mockDispose,
    mockClear: jest.fn(),
    mockReset: jest.fn(),
    mockImplementation: jest.fn()
  });

  return mockVideojs;
});

// Mock video.js CSS import
jest.mock('video.js/dist/video-js.css', () => ({}));

const mockFile = {
  path: '/test/path/video1.mp4',
  metadata: {
    resolution: '1920x1080',
    duration: '1:30:00',
    codec: 'H.264',
    subtitle_streams: [
      {
        index: 0,
        language: 'eng',
        title: 'English',
        codec: 'subrip'
      },
      {
        index: 1,
        language: 'spa',
        title: 'Spanish',
        codec: 'subrip'
      }
    ]
  }
};

describe('MediaPreview Component', () => {
  // Get the mocked videojs instance
  const videojsMock = videojs as jest.Mock & typeof videojs & { mockDispose: jest.Mock };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders file metadata correctly', () => {
    render(<MediaPreview file={mockFile} />);

    expect(screen.getByText('File Details')).toBeInTheDocument();
    expect(screen.getByText('Path:')).toBeInTheDocument();
    expect(screen.getByText(mockFile.path)).toBeInTheDocument();
    expect(screen.getByText('Resolution:')).toBeInTheDocument();
    expect(screen.getByText(mockFile.metadata.resolution)).toBeInTheDocument();
    expect(screen.getByText('Duration:')).toBeInTheDocument();
    expect(screen.getByText(mockFile.metadata.duration)).toBeInTheDocument();
    expect(screen.getByText('Codec:')).toBeInTheDocument();
    expect(screen.getByText(mockFile.metadata.codec)).toBeInTheDocument();
  });

  it('initializes video.js player with correct options', () => {
    render(<MediaPreview file={mockFile} />);
    
    expect(videojs).toHaveBeenCalledWith(
      expect.any(HTMLVideoElement),
      {
        controls: true,
        fluid: true,
        sources: [{
          src: `file://${mockFile.path}`,
          type: 'video/mp4'
        }]
      }
    );
  });

  it('disposes video.js player on unmount', () => {
    const { unmount } = render(<MediaPreview file={mockFile} />);
    unmount();
    expect(videojsMock.mockDispose).toHaveBeenCalled();
  });

  it('renders video element with correct classes', () => {
    render(<MediaPreview file={mockFile} />);
    
    const videoElement = document.querySelector('video');
    expect(videoElement).toHaveClass('video-js', 'vjs-theme-dark');
  });

  it('updates player when file prop changes', () => {
    const { rerender } = render(<MediaPreview file={mockFile} />);
    
    // First render should initialize player
    expect(videojs).toHaveBeenCalledTimes(1);
    expect(videojs).toHaveBeenLastCalledWith(
      expect.any(HTMLVideoElement),
      {
        controls: true,
        fluid: true,
        sources: [{
          src: `file://${mockFile.path}`,
          type: 'video/mp4'
        }]
      }
    );

    // Dispose should be called when updating
    const newFile = {
      ...mockFile,
      path: '/test/path/video2.mp4'
    };

    rerender(<MediaPreview file={newFile} />);
    
    // Old player should be disposed
    expect(videojsMock.mockDispose).toHaveBeenCalled();
    
    // New player should be initialized
    expect(videojs).toHaveBeenCalledTimes(2);
    expect(videojs).toHaveBeenLastCalledWith(
      expect.any(HTMLVideoElement),
      {
        controls: true,
        fluid: true,
        sources: [{
          src: `file://${newFile.path}`,
          type: 'video/mp4'
        }]
      }
    );
  });

  it('handles missing video ref gracefully', () => {
    // Mock useRef to return null
    const originalUseRef = React.useRef;
    const mockUseRef = jest.fn(() => ({ current: null }));
    React.useRef = mockUseRef;

    render(<MediaPreview file={mockFile} />);
    expect(videojs).not.toHaveBeenCalled();

    // Restore original useRef
    React.useRef = originalUseRef;
  });

  it('renders subtitle information', () => {
    render(<MediaPreview file={mockFile} />);
    
    expect(screen.getByText('Subtitles')).toBeInTheDocument();
    expect(screen.getByText(/eng, spa/)).toBeInTheDocument();
  });

  it('renders find more subtitles button', () => {
    render(<MediaPreview file={mockFile} />);
    
    expect(screen.getByText('Find more subtitles')).toBeInTheDocument();
  });
});
