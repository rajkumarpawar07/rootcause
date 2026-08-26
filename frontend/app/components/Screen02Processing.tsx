"use client";

interface Stage {
  label: string;
}

export default function Screen02Processing({
  total,
  currentStage,
  withNotes,
}: {
  total: number;
  currentStage: number; // 0..3 (0..4 with notes); stages before current are done, after are pending
  withNotes: boolean;
}) {
  const stages: Stage[] = [
    { label: `Reading ${total} responses` },
    { label: "Grouping similar reasoning" },
    { label: "Naming the patterns" },
    { label: "Building the dashboard" },
    ...(withNotes ? [{ label: "Drafting suggested notes" }] : []),
  ];

  return (
    <div className="panel">
      <div
        aria-live="polite"
        style={{ padding: "8px 32px 8px" }}
      >
        <div className="stage-list" role="status">
          <h3>Reading your class</h3>
          {stages.map((stage, i) => (
            <div
              key={stage.label}
              className={
                i < currentStage
                  ? "stage done"
                  : i === currentStage
                    ? "stage active"
                    : "stage pending"
              }
            >
              <span className="idx">
                {String(i + 1).padStart(2, "0")}
              </span>
              {i < currentStage ? (
                <span className="icon" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="9" fill="rgba(143,216,172,0.12)" />
                    <path
                      d="M6 10l3 3 5-6"
                      stroke="var(--mint)"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
              ) : (
                <span className="dot" aria-hidden="true"></span>
              )}
              {stage.label}
              {i === currentStage && <span className="cursor-blink" aria-hidden="true" />}
            </div>
          ))}
        </div>
        <p className="stage-footer">
          {withNotes
            ? "Patterns arrive first — personal notes take a few minutes longer."
            : "Usually takes about 15 seconds."}
        </p>
      </div>
    </div>
  );
}
