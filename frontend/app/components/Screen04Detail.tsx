"use client";

import { useState } from "react";
import Badge from "./Badge";
import { ClusterCard, DiagnoseResult } from "@/lib/api";

const BADGE_BY_CATEGORY: Record<
  string,
  { text: string; kind: "gold" | "moss" | "muted" }
> = {
  misconception: { text: "Misconception", kind: "gold" },
  solid_understanding: { text: "Solid understanding", kind: "moss" },
  unclear: { text: "Unclear", kind: "muted" },
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
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="screen-frame">
      <div className="frame-chrome" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div className="frame-body">
        <button className="back-link" onClick={onBack}>
          &larr; Back to dashboard
        </button>
        <div className="detail-head">
          <Badge text={badge.text} kind={badge.kind} />
          <h3>{cluster.label}</h3>
          <span className="count">
            {cluster.size} of {result.responses_analyzed} students
          </span>
        </div>
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
        {notesCount > 0 && (
          <div style={{ marginTop: 18 }}>
            <button className="btn btn-secondary" onClick={copyAll}>
              {copied ? "Copied" : "Copy all feedback for this group"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
