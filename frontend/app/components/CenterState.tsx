"use client";

import { useEffect, useRef, useState } from "react";

export default function CenterState({
  icon,
  title,
  body,
  actionLabel,
  onAction,
}: {
  icon?: React.ReactNode;
  title: string;
  body: string;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="center-state">
      {icon && <div className="icon-wrap">{icon}</div>}
      <h3>{title}</h3>
      <p>{body}</p>
      <button className="btn btn-primary" onClick={onAction}>
        {actionLabel}
      </button>
    </div>
  );
}

export function SeedlingIcon({ animated = false, size = 56 }: { animated?: boolean; size?: number }) {
  const [grow, setGrow] = useState(0);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (!animated) return;
    let t = 0;
    const loop = () => {
      t += 0.012;
      setGrow(Math.sin(t) * 0.06 + 1.02); // subtle pulse
      raf.current = requestAnimationFrame(loop);
    };
    raf.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf.current!);
  }, [animated]);

  const s = size;
  const stroke = 2.2;
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      style={{ transform: `scale(${grow})`, transformOrigin: "center", transition: "transform 0.3s ease-out" }}
    >
      {/* subtle glow ring when animated */}
      {animated && (
        <circle
          cx="20"
          cy="20"
          r="16"
          stroke="var(--mint)"
          strokeWidth="0.6"
          fill="none"
          opacity={0.18}
          className="seedling-ring"
        />
      )}
      <path
        d="M20 8v18M20 26c-5 0-8-4-8-8M20 26c5 0 8-4 8-8M20 14c-3-3-7-3-9 0M20 14c3-3 7-3 9 0"
        stroke="var(--mint)"
        strokeWidth={stroke}
        strokeLinecap="round"
        style={{
          filter: animated ? "drop-shadow(0 0 4px rgba(143,216,172,0.35))" : "none",
        }}
      />
    </svg>
  );
}
