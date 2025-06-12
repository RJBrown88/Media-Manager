import '@testing-library/jest-dom';

// Mock the electron API
const mockIpcRenderer = {
  on: jest.fn(),
  send: jest.fn(),
  invoke: jest.fn(),
  removeListener: jest.fn(),
};

const mockWebFrame = {
  setVisualZoomLevelLimits: jest.fn(),
};

Object.defineProperty(window, 'electron', {
  value: {
    ipcRenderer: mockIpcRenderer,
    webFrame: mockWebFrame,
  },
});

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});

// Clean up after each test
afterEach(() => {
  jest.resetAllMocks();
});
