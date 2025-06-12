import '@testing-library/jest-dom';

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
    }
  }
}

// Extend HTMLInputElement to include webkitdirectory
interface HTMLInputElement extends HTMLElement {
  webkitdirectory: boolean;
}

export {};
