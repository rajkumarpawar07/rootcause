"use client";

import { useMemo, useState } from "react";

export default function Screen01Form({
  onSubmit,
  error,
}: {
  onSubmit: (question: string, correctConcept: string, responses: string[]) => void;
  error?: string;
}) {
  const [question, setQuestion] = useState("Why does ice float on water?");
  const [correctConcept, setCorrectConcept] = useState(
    "Density determines whether an object floats"
  );
  const [raw, setRaw] = useState("");

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
    <div className="screen-frame">
      <div className="frame-chrome" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div className="frame-body">
        <h3 className="intro-title">What did your class just answer?</h3>
        <p className="intro-sub">
          Paste responses to one open-ended question. Works best with 10 or more.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            onSubmit(question.trim(), correctConcept.trim(), responses);
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
              One response per line — {responses.length} response
              {responses.length === 1 ? "" : "s"} added.
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
            Find the patterns
          </button>
          {error && <div className="error-note">{error}</div>}
        </form>
      </div>
    </div>
  );
}
