interface HTMLInputElement extends HTMLElement {
  type: string;
  webkitdirectory: boolean;
  files: {
    [key: number]: {
      webkitRelativePath: string;
    };
    length: number;
  } | null;
  value: string;
  onchange: ((event: Event) => void) | null;
}

interface DataTransferItem {
  kind: string;
  type: string;
  webkitGetAsEntry(): {
    isDirectory: boolean;
    fullPath: string;
  };
}

interface DataTransfer {
  items: DataTransferItem[];
}

interface DragEvent extends Event {
  dataTransfer: DataTransfer;
  preventDefault(): void;
  stopPropagation(): void;
}
