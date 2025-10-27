import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import CountdownTimer from '../CountdownTimer';

describe('CountdownTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts and counts down when Start is clicked', () => {
    render(<CountdownTimer initialSeconds={5} />);

    const startBtn = screen.getByRole('button', { name: /Start countdown/i });
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('5 seconds remaining');

    fireEvent.click(startBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('3 seconds remaining');
  });

  it('pauses when Pause is clicked', () => {
    render(<CountdownTimer initialSeconds={5} />);

    const startBtn = screen.getByRole('button', { name: /Start countdown/i });
    const pauseBtn = screen.getByRole('button', { name: /Pause countdown/i });

    fireEvent.click(startBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Should be at 3
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('3 seconds remaining');

    fireEvent.click(pauseBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Still at 3 after pause
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('3 seconds remaining');
  });

  it('resets to initialSeconds when Reset is clicked', () => {
    render(<CountdownTimer initialSeconds={5} />);

    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('5 seconds remaining');

    const startBtn = screen.getByRole('button', { name: /Start countdown/i });
    const resetBtn = screen.getByRole('button', { name: /Reset countdown/i });

    fireEvent.click(startBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Should be at 3
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('3 seconds remaining');

    fireEvent.click(resetBtn);

    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('5 seconds remaining');
  });
});
