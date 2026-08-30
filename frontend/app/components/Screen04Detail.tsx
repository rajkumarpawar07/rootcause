"use client";

import { useState } from "react";
import Badge from "./Badge";
import { ClusterCard, DiagnoseResult } from "@/lib/api";

const CATEGORY_COLOR: Record<string, string> = {
  misconception: "var(--ember)",
  solid_understanding: "var(--mint)",
  unclear: "var(--drift)",
};

const BADGE_BY_CATEGORY: Record<
  string,
  { text: string; kind: "ember" | "mint" | "slate" }
> = {
  misconception: { text: "Misconception", kind: "ember" },
  solid_understanding: { text: "Solid understanding", kind: "mint" },
  unclear: { text: "Unclear", kind: "slate" },
};

export default function Screen04Detail({
  result,
  cluster,
  onBack,
}: {
  result: DiagnoseResult;
  cluster: ClusterCard;
  onBack: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const badge = BADGE_BY_CATEGORY[cluster.category];
  const byId = new Map(result.records.map((r) => [r.student_id, r]));
  const members = cluster.student_ids
    .map((sid) => byId.get(sid))
    .filter((r): r is NonNullable<typeof r> => Boolean(r));
  const notesCount = members.filter((m) => m.feedback_note).length;

  const copyAll = async () => {
    const text = members
      .map(
        (m) =>
          `"${m.response_text}"\n` +
          (m.feedback_note ? `Suggested note: ${m.feedback_note}` : "")
      )
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setCopyFailed(false);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard permission denied or unavailable — tell the user instead
      // of failing silently.
      setCopyFailed(true);
      setCopied(false);
    }
  };

  return (
    <div className="panel">
      <div style={{ padding: "26px 32px 30px" }}>
        <button className="back-link" onClick={onBack}>
          <span aria-hidden="true">&larr;</span> Back to dashboard
        </button>
        <div className="detail-head" style={{ borderLeft: `4px solid ${CATEGORY_COLOR[cluster.category] ?? "var(--drift)"}` }}>
          <Badge text={badge.text} kind={badge.kind} />
          <h3>{cluster.label}</h3>
          <span className="count">
            {cluster.size} of {result.responses_analyzed} students
          </span>
        </div>
        {cluster.gap && (
          <p className="detail-gap">
            <span className="note-label">The gap</span>
            {cluster.gap}
          </p>
        )}
        <div>
          {members.map((m) => (
            <div key={m.student_id} className="student-row">
              <p className="resp">&ldquo;{m.response_text}&rdquo;</p>
              {m.feedback_note && (
                <div className="note">
                  <span className="note-label">Suggested note</span>
                  {m.feedback_note}
                </div>
              )}
            </div>
          ))}
        </div>
        {notesCount > 0 && (
          <div className="copy-btn">
            <button className="btn btn-secondary" onClick={copyAll}>
              {copied ? "Copied" : copyFailed ? "Copy failed — try again" : "Copy all feedback for this group"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
