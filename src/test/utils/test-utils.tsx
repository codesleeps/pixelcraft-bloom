import { render, renderHook, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Custom render function that wraps components with MemoryRouter and QueryClientProvider
export const renderWithProviders = (
  ui: ReactElement,
  options?: Parameters<typeof render>[1]
) => {
  const Wrapper = ({ children }: { children: ReactElement }) => (
    <MemoryRouter>
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    </MemoryRouter>
  );

  return render(ui, { wrapper: Wrapper, ...options });
};

// Helper to wait for loading states to finish
export const waitForLoadingToFinish = () =>
  waitFor(() =>
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
  );

// Helper to fill a form field by its label
export const fillFormField = async (label: string, value: string) => {
  const input = screen.getByLabelText(label);
  await userEvent.clear(input);
  await userEvent.type(input, value);
};

// Helper to submit a form by clicking the submit button
export const submitForm = async (buttonText?: string) => {
  const submitButton = screen.getByRole('button', {
    name: buttonText || /submit/i,
  });
  await userEvent.click(submitButton);
};

// Helper to create a mock event object
export const createMockEvent = (overrides: Partial<Event> = {}) => ({
  preventDefault: vi.fn(),
  stopPropagation: vi.fn(),
  target: { value: '' },
  ...overrides,
});

// Create a test QueryClient with disabled retries, no cache time, and suppressed error logging
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // Suppress error logging for cleaner test output
    },
  });

// Custom renderHook function that wraps hooks with MemoryRouter and QueryClientProvider
export const renderHookWithProviders = (
  hook: () => any,
  options?: { queryClient?: QueryClient }
) => {
  const queryClient = options?.queryClient || createTestQueryClient();
  const Wrapper = ({ children }: { children: ReactElement }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </MemoryRouter>
  );
  return renderHook(hook, { wrapper: Wrapper });
};
