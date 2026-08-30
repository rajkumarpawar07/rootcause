"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import CenterState, { SeedlingIcon } from "./components/CenterState";
import Screen01Form, { FormDraft } from "./components/Screen01Form";
import Screen02Processing from "./components/Screen02Processing";
import Screen03Dashboard from "./components/Screen03Dashboard";
import Screen04Detail from "./components/Screen04Detail";
import { DiagnoseResult, diagnose } from "@/lib/api";

type View =
  | { kind: "empty" }
  | { kind: "form"; error?: string }
  | { kind: "processing"; total: number; withNotes: boolean }
  | { kind: "dashboard" }
  | { kind: "detail"; clusterId: number }
  | { kind: "toofew"; received: number; minimum: number };

// Stage list advances while the real pipeline runs server-side; each stage
// names an actual pipeline step (design doc principle 04).
const STAGE_ADVANCE_MS = 80_000;

export default function Home() {
  const [view, setView] = useState<View>({ kind: "empty" });
  const [result, setResult] = useState<DiagnoseResult | null>(null);
  const [draft, setDraft] = useState<FormDraft | null>(null);
  const [stage, setStage] = useState(0);
  const stageTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearStageTimer = useCallback(() => {
    if (stageTimer.current) {
      clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
  }, []);

  useEffect(() => clearStageTimer, [clearStageTimer]);

  const runDiagnostic = async (
    question: string,
    correctConcept: string,
    raw: string,
    responses: string[],
    includeFeedback: boolean
  ) => {
    // Keep what was pasted so an error or too-few return can restore it.
    setDraft({ question, correctConcept, raw, includeFeedback });
    setResult(null);
    setStage(0);
    setView({ kind: "processing", total: responses.length, withNotes: includeFeedback });
    clearStageTimer();
    stageTimer.current = setInterval(() => {
      setStage((s) => Math.min(s + 1, includeFeedback ? 4 : 3));
    }, STAGE_ADVANCE_MS);

    try {
      const res = await diagnose({
        question,
        correct_concept: correctConcept || undefined,
        include_feedback: includeFeedback,
        responses: responses.map((response) => ({ response })),
      });
      setResult(res);
      setView({ kind: "dashboard" });
    } catch (err) {
      const insufficient = (
        err as Error & { insufficient?: { received: number; minimum: number } }
      ).insufficient;
      if (insufficient) {
        setView({
          kind: "toofew",
          received: insufficient.received,
          minimum: insufficient.minimum,
        });
      } else if ((err as Error & { modelUnavailable?: unknown }).modelUnavailable) {
        setView({ kind: "form", error: (err as Error).message });
      } else if ((err as Error & { configurationError?: unknown }).configurationError) {
        setView({ kind: "form", error: (err as Error).message });
      } else if ((err as Error & { pipelineError?: unknown }).pipelineError) {
        setView({ kind: "form", error: (err as Error).message });
      } else {
        setView({
          kind: "form",
          error:
            "Something went wrong reaching the pipeline. Check that the backend is running, then try again.",
        });
      }
    } finally {
      clearStageTimer();
    }
  };

  let screen: React.ReactNode;

  switch (view.kind) {
    case "empty":
      screen = (
        <div className="panel empty-panel">
          <CenterState
            icon={<SeedlingIcon animated size={72} />}
            title="Nothing diagnosed yet"
            body="Add responses to one question and RootCause will show you what your class actually thinks."
            actionLabel="Start a diagnostic"
            onAction={() => setView({ kind: "form" })}
          />
        </div>
      );
      break;
    case "form":
      screen = (
        <Screen01Form
          onSubmit={runDiagnostic}
          error={view.error}
          initial={draft ?? undefined}
        />
      );
      break;
    case "processing":
      screen = (
        <Screen02Processing
          total={view.total}
          currentStage={stage}
          withNotes={view.withNotes}
        />
      );
      break;
    case "dashboard":
      screen = result ? (
        <Screen03Dashboard
          result={result}
          onNewDiagnostic={() => setView({ kind: "form" })}
          onViewCluster={(clusterId) => setView({ kind: "detail", clusterId })}
        />
      ) : (
        <></>
      );
      break;
    case "detail":
      screen =
        result &&
        result.clusters.find((c) => c.cluster_id === view.clusterId) ? (
          <Screen04Detail
            result={result}
            cluster={
              result.clusters.find((c) => c.cluster_id === view.clusterId)!
            }
            onBack={() => setView({ kind: "dashboard" })}
          />
        ) : (
          <></>
        );
      break;
    case "toofew":
      screen = (
        <div className="panel">
          <CenterState
            title="Add a few more responses"
            body={`Diagnostics need at least ${view.minimum} responses to find a reliable pattern. This one has ${view.received}.`}
            actionLabel="Add more responses"
            onAction={() => setView({ kind: "form" })}
          />
        </div>
      );
      break;
  }

  return (
    <main className="app-shell">
      <span className="wordmark">RootCause</span>
      {screen}
    </main>
  );
}
