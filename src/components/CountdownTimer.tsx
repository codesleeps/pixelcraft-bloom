import React, { useEffect, useRef, useState } from 'react';

export type CountdownTimerProps = {
  initialSeconds: number;
};

export default function CountdownTimer({ initialSeconds }: CountdownTimerProps) {
  const [seconds, setSeconds] = useState<number>(initialSeconds);
  const [running, setRunning] = useState<boolean>(false);
  const intervalRef = useRef<number | null>(null);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []);

  // Manage interval when `running` toggles
  useEffect(() => {
    if (running && intervalRef.current === null) {
      intervalRef.current = window.setInterval(() => {
        setSeconds((prev) => {
          if (prev <= 1) {
            // stop at zero
            if (intervalRef.current !== null) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
            setRunning(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    if (!running && intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [running]);

  const start = () => {
    if (!running && seconds > 0) setRunning(true);
  };

  const pause = () => {
    setRunning(false);
  };

  const reset = () => {
    setRunning(false);
    setSeconds(initialSeconds);
  };

  return (
    <div aria-live="polite" role="region" aria-label="Countdown Timer">
      <h2 data-testid="countdown-heading">{seconds} seconds remaining</h2>

      <div className="controls" role="group" aria-label="Countdown controls">
        <button aria-label="Start countdown" onClick={start} disabled={running || seconds === 0}>
          Start
        </button>
        <button aria-label="Pause countdown" onClick={pause} disabled={!running}>
          Pause
        </button>
        <button aria-label="Reset countdown" onClick={reset}>
          Reset
        </button>
      </div>
    </div>
  );
}
