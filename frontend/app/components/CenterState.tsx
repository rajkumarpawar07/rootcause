"use client";

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

export function SeedlingIcon() {
  // From the design doc's screen 05.
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M20 8v18M20 26c-5 0-8-4-8-8M20 26c5 0 8-4 8-8M20 14c-3-3-7-3-9 0M20 14c3-3 7-3 9 0"
        stroke="var(--moss)"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
