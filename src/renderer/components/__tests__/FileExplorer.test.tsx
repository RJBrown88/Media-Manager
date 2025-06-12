import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileExplorer from '../FileExplorer';

const mockFiles = [
  {
    path: '/test/path/video1.mp4',
    metadata: {
      resolution: '1920x1080',
      duration: '1:30:00',
      codec: 'H.264'
    }
  },
  {
    path: '/test/path/video2.mp4',
    metadata: {
      resolution: '3840x2160',
      duration: '2:00:00',
      codec: 'H.265'
    }
  }
];

describe('FileExplorer Component', () => {
  const mockOnScan = jest.fn();
  const mockOnFileSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <FileExplorer
        files={[]}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );
    expect(screen.getByText('Media Files')).toBeInTheDocument();
    expect(screen.getByText('Drop a folder here or click Browse')).toBeInTheDocument();
  });

  it('displays file list correctly', () => {
    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    expect(screen.getByText('video1.mp4')).toBeInTheDocument();
    expect(screen.getByText('video2.mp4')).toBeInTheDocument();
    expect(screen.getByText('1920x1080')).toBeInTheDocument();
    expect(screen.getByText('H.264')).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const fileItem = screen.getByText('video1.mp4');
    await userEvent.click(fileItem);

    expect(mockOnFileSelect).toHaveBeenCalledWith(mockFiles[0]);
  });

  it('handles drag and drop', () => {
    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const dropzone = screen.getByText('Drop a folder here or click Browse');

    // Create a mock drag event with required properties
    const mockDataTransfer = {
      items: [{
        kind: 'file',
        webkitGetAsEntry: () => ({
          isDirectory: true,
          fullPath: '/test/path'
        })
      }]
    };

    fireEvent.drop(dropzone, {
      preventDefault: () => {},
      stopPropagation: () => {},
      dataTransfer: mockDataTransfer
    });

    expect(mockOnScan).toHaveBeenCalledWith('/test/path');
  });

  it('handles browse button click', async () => {
    // Create a mock file input element
    const mockInput = document.createElement('input');
    mockInput.type = 'file';
    
    // Add webkitdirectory property
    Object.defineProperty(mockInput, 'webkitdirectory', {
      value: true,
      writable: true
    });

    // Track the created input
    let createdInput = mockInput;
    
    // Mock document.createElement
    const createElementSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'input') {
        return mockInput;
      }
      return document.createElement(tagName);
    });

    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const browseButton = screen.getByText('Browse');
    await userEvent.click(browseButton);

    expect(createdInput).toBeTruthy();
    expect(createdInput?.type).toBe('file');
    expect(createdInput?.webkitdirectory).toBe(true);

    // Simulate file selection
    if (createdInput) {
      const mockFile = {
        webkitRelativePath: 'test-directory/file.mp4'
      };
      
      const mockFileList = {
        0: mockFile,
        length: 1,
        item: (idx: number) => mockFile
      } as unknown as FileList;

      fireEvent.change(createdInput, {
        target: {
          files: mockFileList
        }
      });
      
      expect(mockOnScan).toHaveBeenCalledWith('test-directory');
    }

    // Restore original createElement
    createElementSpy.mockRestore();
  });

  it('handles empty file list', () => {
    render(
      <FileExplorer
        files={[]}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const fileList = document.querySelector('.file-list');
    expect(fileList?.children.length).toBe(0);
  });

  it('handles dragover events correctly', () => {
    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const dropzone = screen.getByText('Drop a folder here or click Browse');
    const preventDefault = jest.fn();
    const stopPropagation = jest.fn();

    // Create a mock drag event that matches React.DragEvent
    const mockDataTransfer = {
      items: [{
        kind: 'file',
        webkitGetAsEntry: () => ({
          isDirectory: true,
          fullPath: '/test/path'
        })
      }],
      types: ['Files']
    };

    // Test dragover behavior
    fireEvent.dragOver(dropzone, {
      preventDefault,
      stopPropagation,
      dataTransfer: mockDataTransfer
    });

    // Verify event handlers were called
    expect(preventDefault).toHaveBeenCalled();
    expect(stopPropagation).toHaveBeenCalled();

    // Verify dropzone has correct class
    expect(dropzone.parentElement).toHaveClass('file-explorer-dropzone');
  });

  it('handles dragenter and dragleave events', () => {
    render(
      <FileExplorer
        files={mockFiles}
        onScan={mockOnScan}
        onFileSelect={mockOnFileSelect}
      />
    );

    const dropzone = screen.getByText('Drop a folder here or click Browse');
    const dropzoneContainer = dropzone.parentElement;
    
    // Test dragenter
    fireEvent.dragEnter(dropzone, {
      dataTransfer: {
        items: [{
          kind: 'file',
          webkitGetAsEntry: () => ({
            isDirectory: true,
            fullPath: '/test/path'
          })
        }],
        types: ['Files']
      }
    });
    expect(dropzoneContainer).toHaveClass('file-explorer-dropzone');

    // Test dragleave
    fireEvent.dragLeave(dropzone);
    expect(dropzoneContainer).toHaveClass('file-explorer-dropzone');
  });
});
