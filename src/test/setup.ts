import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Prevent WebSocket server initialization during tests
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({ isConnected: false, error: null }),
}));


