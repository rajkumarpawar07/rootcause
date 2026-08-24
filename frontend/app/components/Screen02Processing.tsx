"use client";

interface Stage {
  label: string;
}

export default function Screen02Processing({
  total,
  currentStage,
}: {
  total: number;
  currentStage: number; // 0..3; stages before current are done, after are pending
}) {
  const stages: Stage[] = [
    { label: `Reading ${total} responses` },
    { label: "Grouping similar reasoning" },
    { label: "Naming the patterns" },
    { label: "Building the dashboard" },
  ];

  return (
    <div className="screen-frame">
      <div className="frame-chrome" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div aria-live="polite">
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
              {i < currentStage ? (
                <svg
                  className="icon"
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  aria-hidden="true"
                >
                  <circle cx="10" cy="10" r="9" fill="var(--moss-soft)" />
                  <path
                    d="M6 10l3 3 5-6"
                    stroke="var(--moss)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <span className="dot" aria-hidden="true"></span>
              )}
              {stage.label}
            </div>
          ))}
        </div>
        <p className="stage-footer">Usually takes about 15 seconds.</p>
      </div>
    </div>
  );
}
