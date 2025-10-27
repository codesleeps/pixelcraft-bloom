import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import CountdownTimer from '../CountdownTimer';

describe('CountdownTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('counts down after start', () => {
    render(<CountdownTimer initialSeconds={3} />);

    const startBtn = screen.getByRole('button', { name: /start countdown/i });
    fireEvent.click(startBtn);

    // advance 1 second
    vi.advanceTimersByTime(1000);
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('2 seconds remaining');

    // advance another 2 seconds to hit zero
    vi.advanceTimersByTime(2000);
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('0 seconds remaining');
  });

  it('pauses the countdown', () => {
    render(<CountdownTimer initialSeconds={5} />);

    const startBtn = screen.getByRole('button', { name: /start countdown/i });
    const pauseBtn = screen.getByRole('button', { name: /pause countdown/i });

    fireEvent.click(startBtn);
    vi.advanceTimersByTime(1000);
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('4 seconds remaining');

    fireEvent.click(pauseBtn);
    vi.advanceTimersByTime(2000);
    // should remain the same after pausing
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('4 seconds remaining');
  });

  it('resets the countdown', () => {
    render(<CountdownTimer initialSeconds={10} />);

    const startBtn = screen.getByRole('button', { name: /start countdown/i });
    const resetBtn = screen.getByRole('button', { name: /reset countdown/i });

    fireEvent.click(startBtn);
    vi.advanceTimersByTime(3000);
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('7 seconds remaining');

    fireEvent.click(resetBtn);
    expect(screen.getByTestId('countdown-heading')).toHaveTextContent('10 seconds remaining');
  });
});
import React from 'react';
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
    expect(screen.getByText(/5 seconds remaining/i)).toBeInTheDocument();

    fireEvent.click(startBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByText(/3 seconds remaining/i)).toBeInTheDocument();
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
    expect(screen.getByText(/3 seconds remaining/i)).toBeInTheDocument();

    fireEvent.click(pauseBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Still at 3 after pause
    expect(screen.getByText(/3 seconds remaining/i)).toBeInTheDocument();
  });

  it('resets to initialSeconds when Reset is clicked', () => {
    render(<CountdownTimer initialSeconds={5} />);

    const startBtn = screen.getByRole('button', { name: /Start countdown/i });
    const resetBtn = screen.getByRole('button', { name: /Reset countdown/i });

    fireEvent.click(startBtn);

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Should be at 3
    expect(screen.getByText(/3 seconds remaining/i)).toBeInTheDocument();

    fireEvent.click(resetBtn);

    expect(screen.getByText(/5 seconds remaining/i)).toBeInTheDocument();
  });
});
