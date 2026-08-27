"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface CountUpProps {
  end: number;
  duration?: number;
  delay?: number;
  className?: string;
  suffix?: string;
}

export default function CountUp({ end, duration = 1200, delay = 0, className, suffix = "" }: CountUpProps) {
  const [count, setCount] = useState(0);
  const frame = useRef<number | null>(null);

  const start = useCallback(() => {
    const startTime = performance.now();
    function tick(now: number) {
      const p = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setCount(Math.floor(eased * end));
      if (p < 1) frame.current = requestAnimationFrame(tick);
    }
    frame.current = requestAnimationFrame(tick);
  }, [duration, end]);

  useEffect(() => {
    if (delay > 0) {
      const t = setTimeout(() => start(), delay);
      return () => clearTimeout(t);
    }
    start();
  }, [delay, start]);

  useEffect(() => () => cancelAnimationFrame(frame.current!), []);

  return (
    <span className={className}>
      {count}{suffix && <span className="unit">{suffix}</span>}
    </span>
  );
}