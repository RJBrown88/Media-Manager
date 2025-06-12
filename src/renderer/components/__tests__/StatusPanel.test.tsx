import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import StatusPanel from '../StatusPanel';

const mockStatus = {
  version: '1.0.0',
  platform: 'win32',
  ffprobe: 'ok',
  lastOperation: {
    type: 'scan' as const,
    timestamp: '2025-06-08T21:55:00.000Z',
    success: true
  }
};

describe('StatusPanel Component', () => {
  it('renders CLI disconnected state', () => {
    render(<StatusPanel status={null} />);
    
    expect(screen.getByText('Failed to connect to CLI')).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });

  it('renders CLI connected state with all systems ok', () => {
    render(<StatusPanel status={mockStatus} />);
    
    expect(screen.getByText('CLI Version:')).toBeInTheDocument();
    expect(screen.getByText('1.0.0')).toBeInTheDocument();
    expect(screen.getByText('Platform:')).toBeInTheDocument();
    expect(screen.getByText('win32')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('renders FFprobe not found warning', () => {
    const statusWithoutFFprobe = {
      ...mockStatus,
      ffprobe: 'not_found'
    };

    render(<StatusPanel status={statusWithoutFFprobe} />);
    
    expect(screen.getByText('Not Found')).toBeInTheDocument();
    expect(screen.getByText('Please install FFmpeg to enable media file analysis')).toBeInTheDocument();
  });

  it('displays last operation details', () => {
    render(<StatusPanel status={mockStatus} />);
    
    expect(screen.getByText(/scan - Success/)).toBeInTheDocument();
    expect(screen.getByText(/6\/8\/2025/)).toBeInTheDocument();
  });

  it('displays failed operation status', () => {
    const statusWithFailedOp = {
      ...mockStatus,
      lastOperation: {
        ...mockStatus.lastOperation,
        success: false
      }
    };

    render(<StatusPanel status={statusWithFailedOp} />);
    
    expect(screen.getByText(/scan - Failed/)).toBeInTheDocument();
  });

  it('handles error display and dismissal', () => {
    const error = {
      message: 'Test error message',
      details: { code: 'TEST_ERROR' }
    };
    const onDismissError = jest.fn();

    render(
      <StatusPanel
        status={mockStatus}
        error={error}
        onDismissError={onDismissError}
      />
    );
    
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    
    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);
    
    expect(onDismissError).toHaveBeenCalled();
  });

  it('displays error in disconnected state', () => {
    const error = {
      message: 'Connection error',
      details: { code: 'CONNECTION_ERROR' }
    };

    render(<StatusPanel status={null} error={error} />);
    
    expect(screen.getByText('Failed to connect to CLI')).toBeInTheDocument();
    expect(screen.getByText('Connection error')).toBeInTheDocument();
  });

  it('applies correct CSS classes based on status', () => {
    const { container, rerender } = render(<StatusPanel status={mockStatus} />);
    
    expect(container.firstChild).toHaveClass('status-panel-ok');

    const statusWithoutFFprobe = {
      ...mockStatus,
      ffprobe: 'not_found'
    };
    
    rerender(<StatusPanel status={statusWithoutFFprobe} />);
    expect(container.firstChild).toHaveClass('status-panel-warning');

    rerender(<StatusPanel status={null} />);
    expect(container.firstChild).toHaveClass('status-panel-error');
  });

  it('handles different operation types', () => {
    const operations: Array<'scan' | 'rename' | 'preview' | 'commit' | 'undo'> = [
      'scan', 'rename', 'preview', 'commit', 'undo'
    ];

    operations.forEach(opType => {
      const status = {
        ...mockStatus,
        lastOperation: {
          type: opType,
          timestamp: '2025-06-08T21:55:00.000Z',
          success: true
        }
      };

      const { rerender } = render(<StatusPanel status={status} />);
      expect(screen.getByText(new RegExp(`${opType} - Success`))).toBeInTheDocument();
      rerender(<></>); // Clean up before next iteration
    });
  });

  it('formats timestamp correctly', () => {
    const timestamp = new Date('2025-06-08T21:55:00.000Z').toLocaleString();
    render(<StatusPanel status={mockStatus} />);
    
    expect(screen.getByText(timestamp)).toBeInTheDocument();
  });

  it('handles missing last operation', () => {
    const statusWithoutOp = {
      version: '1.0.0',
      platform: 'win32',
      ffprobe: 'ok'
    };

    render(<StatusPanel status={statusWithoutOp} />);
    
    expect(screen.queryByText(/Last Operation:/)).not.toBeInTheDocument();
  });
});
