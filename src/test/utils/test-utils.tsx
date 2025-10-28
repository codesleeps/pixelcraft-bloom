import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ReactElement } from 'react';

// Custom render function that wraps components with MemoryRouter
export const renderWithProviders = (
  ui: ReactElement,
  options?: Parameters<typeof render>[1]
) => {
  const Wrapper = ({ children }: { children: ReactElement }) => (
    <MemoryRouter>{children}</MemoryRouter>
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
