// MockWebSocket class that implements the WebSocket interface for testing
class MockWebSocket {
  url: string;
  readyState: number;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  private sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING; // Initial state
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = WebSocket.CLOSING;
    if (this.onclose) {
      const event = new CloseEvent('close', { code: code || 1000, reason: reason || '' });
      this.onclose(event);
    }
    this.readyState = WebSocket.CLOSED;
  }

  // Helper methods for testing
  simulateOpen(): void {
    this.readyState = WebSocket.OPEN;
    if (this.onopen) {
      const event = new Event('open');
      this.onopen(event);
    }
  }

  simulateMessage(data: any): void {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data: JSON.stringify(data) });
      this.onmessage(event);
    }
  }

  simulateError(): void {
    if (this.onerror) {
      const event = new Event('error');
      this.onerror(event);
    }
  }

  simulateClose(code: number, reason?: string): void {
    this.readyState = WebSocket.CLOSING;
    if (this.onclose) {
      const event = new CloseEvent('close', { code, reason: reason || '' });
      this.onclose(event);
    }
    this.readyState = WebSocket.CLOSED;
  }

  // Getter for sent messages to allow assertions
  getSentMessages(): string[] {
    return [...this.sentMessages];
  }
}

// Function to mock the global WebSocket
export function mockWebSocket(): () => void {
  const originalWebSocket = window.WebSocket;
  window.WebSocket = MockWebSocket as any; // Type assertion since MockWebSocket implements the interface

  // Return cleanup function
  return () => {
    window.WebSocket = originalWebSocket;
  };
}

// Function to create a direct instance for testing
export function createMockWebSocketInstance(url: string): MockWebSocket {
  return new MockWebSocket(url);
}