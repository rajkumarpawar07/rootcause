"use client";

import { useMemo, useState } from "react";

export interface FormDraft {
  question: string;
  correctConcept: string;
  raw: string;
  includeFeedback: boolean;
}

export default function Screen01Form({
  onSubmit,
  error,
  initial,
}: {
  onSubmit: (
    question: string,
    correctConcept: string,
    raw: string,
    responses: string[],
    includeFeedback: boolean
  ) => void;
  error?: string;
  initial?: FormDraft;
}) {
  const [question, setQuestion] = useState(initial?.question ?? "Why does ice float on water?");
  const [correctConcept, setCorrectConcept] = useState(
    initial?.correctConcept ?? "Density determines whether an object floats"
  );
  const [raw, setRaw] = useState(initial?.raw ?? "");
  const [includeFeedback, setIncludeFeedback] = useState(
    initial?.includeFeedback ?? false
  );

  const responses = useMemo(
    () =>
      raw
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean),
    [raw]
  );

  const canSubmit = question.trim().length > 0 && responses.length > 0;

  return (
    <div className="panel">
      <div style={{ padding: "30px 32px 32px" }}>
        <h3 className="intro-title">What did your class just answer?</h3>
        <p className="intro-sub">
          Paste responses to one open-ended question. Works best with 10 or more.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            onSubmit(
              question.trim(),
              correctConcept.trim(),
              raw,
              responses,
              includeFeedback
            );
          }}
        >
          <div className="field">
            <label htmlFor="question">Question</label>
            <input
              id="question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="concept">
              Correct concept <span className="optional">(optional)</span>
            </label>
            <input
              id="concept"
              type="text"
              value={correctConcept}
              onChange={(e) => setCorrectConcept(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="responses">Student responses</label>
            <textarea
              id="responses"
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              placeholder={"Paste one response per line…"}
            />
            <div className="hint">
              One response per line —{" "}
              <span className={responses.length >= 8 ? "hint-strong" : ""}>
                {responses.length} response{responses.length === 1 ? "" : "s"} added
              </span>
            </div>
          </div>
          <label className="check-field">
            <input
              type="checkbox"
              checked={includeFeedback}
              onChange={(e) => setIncludeFeedback(e.target.checked)}
            />
            <span className="check-copy">
              <b>Draft a suggested note for each student</b>
              Patterns arrive in seconds — personal notes are written live and
              add a few minutes.
            </span>
          </label>
          <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
            {error ? "Try again" : "Find the patterns"}
          </button>
          {error && <div className="error-note">{error}</div>}
        </form>
      </div>
    </div>
  );
}
