import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RenamePanel from '../RenamePanel';

const mockFile = {
  path: '/test/path/video1.mp4',
  metadata: {
    resolution: '1920x1080',
    duration: '1:30:00',
    codec: 'H.264'
  }
};

// Mock window.api
const mockSend = jest.fn();
const mockReceive = jest.fn();
const mockRemoveAllListeners = jest.fn();

const mockApi = {
  send: mockSend,
  receive: mockReceive,
  removeAllListeners: mockRemoveAllListeners
};

describe('RenamePanel Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset window.api before each test
    Object.defineProperty(window, 'api', {
      value: mockApi,
      writable: true,
      configurable: true
    });
  });

  afterEach(() => {
    // Clean up window.api after each test
    delete (window as any).api;
  });

  it('renders initial state correctly', () => {
    render(<RenamePanel file={mockFile} />);

    expect(screen.getByText('Rename File')).toBeInTheDocument();
    expect(screen.getByText('Current:')).toBeInTheDocument();
    expect(screen.getByText(mockFile.path)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('{filename}_{resolution}')).toBeInTheDocument();
    expect(screen.getByText('Available Variables:')).toBeInTheDocument();
  });

  it('handles template input changes', async () => {
    render(<RenamePanel file={mockFile} />);

    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await act(async () => {
      await userEvent.type(input, '_test');
    });

    expect(input).toHaveValue('_test');
  });

  it('disables Preview button when template is empty', () => {
    render(<RenamePanel file={mockFile} />);

    const previewButton = screen.getByText('Preview');
    expect(previewButton).toBeDisabled();
  });

  it('enables Preview button when template is not empty', async () => {
    render(<RenamePanel file={mockFile} />);

    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await act(async () => {
      await userEvent.type(input, '_test');
    });

    const previewButton = screen.getByText('Preview');
    expect(previewButton).not.toBeDisabled();
  });

  it('handles preview request correctly', async () => {
    render(<RenamePanel file={mockFile} />);

    // Type in template
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');

    // Click preview button
    const previewButton = screen.getByRole('button', { name: 'Preview' });
    await userEvent.click(previewButton);

    // Verify rename request
    expect(mockSend).toHaveBeenCalledWith('rename', {
      file: mockFile.path,
      template: '_test',
      dryRun: true
    });

    // Get the preview callback
    const [[, previewCallback]] = mockReceive.mock.calls;

    // Simulate preview response
    await act(async () => {
      previewCallback({ newName: 'video1_test.mp4' });
    });

    // Verify preview is displayed
    const previewText = await screen.findByText('Preview: video1_test.mp4');
    expect(previewText).toBeInTheDocument();
  });

  it('handles stage request correctly', async () => {
    render(<RenamePanel file={mockFile} />);

    // Type in template
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');

    // Click stage button
    const stageButton = screen.getByRole('button', { name: 'Stage' });
    await userEvent.click(stageButton);

    // Verify rename request
    expect(mockSend).toHaveBeenCalledWith('rename', {
      file: mockFile.path,
      template: '_test',
      dryRun: false
    });

    // Get the stage callback
    const [[, stageCallback]] = mockReceive.mock.calls;

    // Simulate stage response
    await act(async () => {
      stageCallback();
    });

    // Verify button states after staging
    const stageButtonAfter = await screen.findByRole('button', { name: 'Stage' });
    const commitButton = await screen.findByRole('button', { name: 'Commit' });
    const undoButton = await screen.findByRole('button', { name: 'Undo' });

    expect(stageButtonAfter).toBeDisabled();
    expect(commitButton).toBeEnabled();
    expect(undoButton).toBeEnabled();
  });

  it('handles commit request correctly', async () => {
    render(<RenamePanel file={mockFile} />);

    // Stage first
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');
    
    const stageButton = screen.getByRole('button', { name: 'Stage' });
    await userEvent.click(stageButton);

    // Get and call stage callback
    const [[, stageCallback]] = mockReceive.mock.calls;
    await act(async () => {
      stageCallback();
    });

    // Click commit button
    const commitButton = await screen.findByRole('button', { name: 'Commit' });
    await userEvent.click(commitButton);

    // Verify commit request
    expect(mockSend).toHaveBeenCalledWith('commit', {});

    // Verify button states after commit
    const stageButtonAfter = await screen.findByRole('button', { name: 'Stage' });
    const commitButtonAfter = await screen.findByRole('button', { name: 'Commit' });
    const undoButton = await screen.findByRole('button', { name: 'Undo' });

    expect(stageButtonAfter).toBeEnabled();
    expect(commitButtonAfter).toBeDisabled();
    expect(undoButton).toBeDisabled();
  });

  it('handles undo request correctly', async () => {
    render(<RenamePanel file={mockFile} />);

    // Stage first
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');
    
    const stageButton = screen.getByRole('button', { name: 'Stage' });
    await userEvent.click(stageButton);

    // Get and call stage callback
    const [[, stageCallback]] = mockReceive.mock.calls;
    await act(async () => {
      stageCallback();
    });

    // Click undo button
    const undoButton = await screen.findByRole('button', { name: 'Undo' });
    await userEvent.click(undoButton);

    // Verify undo request
    expect(mockSend).toHaveBeenCalledWith('undo', {});

    // Verify button states after undo
    const stageButtonAfter = await screen.findByRole('button', { name: 'Stage' });
    const commitButton = await screen.findByRole('button', { name: 'Commit' });
    const undoButtonAfter = await screen.findByRole('button', { name: 'Undo' });

    expect(stageButtonAfter).toBeEnabled();
    expect(commitButton).toBeDisabled();
    expect(undoButtonAfter).toBeDisabled();
  });

  it('resets state when file prop changes', async () => {
    const { rerender } = render(<RenamePanel file={mockFile} />);

    // Type in template
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');

    // Verify input value
    expect(input).toHaveValue('_test');

    // Change file prop
    const newFile = {
      ...mockFile,
      path: '/test/path/video2.mp4'
    };

    // Rerender with new file
    rerender(<RenamePanel file={newFile} />);

    // Verify state reset
    await waitFor(() => {
      expect(input).toHaveValue('');
    });
    expect(screen.queryByText(/Preview:/)).not.toBeInTheDocument();
  });

  it('removes event listeners on unmount', async () => {
    const { unmount } = render(<RenamePanel file={mockFile} />);

    // Type in template and trigger preview
    const input = screen.getByPlaceholderText('{filename}_{resolution}');
    await userEvent.type(input, '_test');
    
    const previewButton = screen.getByRole('button', { name: 'Preview' });
    await userEvent.click(previewButton);

    // Unmount component
    unmount();

    // Verify cleanup
    expect(mockRemoveAllListeners).toHaveBeenCalledWith('rename-result');
  });
});
