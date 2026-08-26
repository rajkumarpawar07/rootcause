"use client";

// Throwaway inspection route — renders every screen state with fixture
// data so the whole redesign can be captured in one screenshot round.
// DELETED before ship; never linked from the app.

import BranchChart from "../components/BranchChart";
import CenterState, { SeedlingIcon } from "../components/CenterState";
import Screen01Form from "../components/Screen01Form";
import Screen02Processing from "../components/Screen02Processing";
import Screen03Dashboard from "../components/Screen03Dashboard";
import Screen04Detail from "../components/Screen04Detail";
import { DiagnoseResult } from "@/lib/api";

const FIXTURE: DiagnoseResult = {
  status: "ok",
  question: "Why does ice float on water?",
  responses_analyzed: 30,
  records: [
    { student_id: "s01", response_text: "Ice is heavy, but it's cold so it floats.", reasoning_summary: "", feedback_note: "You're right that temperature matters here — but it's density, not weight, that decides floating." },
    { student_id: "s02", response_text: "It must be lighter than the water around it because it's frozen.", reasoning_summary: "", feedback_note: "Good instinct that something about \"frozen\" matters. It's not lightness though — it's that freezing makes water take up more space, lowering its density." },
  ],
  clusters: [
    { cluster_id: 0, label: "Floating depends on weight or size, not density", gap: "These students decide floating by comparing overall weight or size.", reteach_suggestion: "Have students weigh an ice cube and an equal-sized container of water on a balance scale, then name 'less stuff in the same space' as lower density.", category: "misconception", size: 7, percentage: 23, example_response: "Ice is heavy, but it's cold so it floats.", student_ids: ["s01"] },
    { cluster_id: 1, label: "Light or airy objects float on supportive water", gap: "Students locate the cause of floating in absolute weight, size, or trapped air.", reteach_suggestion: "Predict and test identical sealed containers in a tub of water — one air-filled, one packed with clay.", category: "misconception", size: 6, percentage: 20, example_response: "There's air inside the ice, so it floats like a balloon.", student_ids: ["s02"] },
    { cluster_id: 2, label: "Ice floats because freezing makes it lighter", gap: "Students explain floating through a vague sense of 'lightness'.", reteach_suggestion: "Seal water in a rigid container, record mass and volume, freeze it, and remeasure to discover mass stays constant while volume grows.", category: "misconception", size: 5, percentage: 17, example_response: "When water freezes it traps air bubbles, and that makes it float.", student_ids: ["s03"] },
    { cluster_id: 3, label: "Floating as a familiar fact, not explained", gap: "Students accept ice floating as an unquestioned observation.", reteach_suggestion: "Run a predict-then-test sink-or-float station with small objects.", category: "misconception", size: 4, percentage: 13, example_response: "Not sure - it just floats, I've always seen it happen.", student_ids: ["s04"] },
    { cluster_id: 4, label: "Correct reasoning", gap: "", reteach_suggestion: "No reteach needed — invite one of these students to explain their thinking during the lesson.", category: "solid_understanding", size: 3, percentage: 10, example_response: "Ice is less dense than liquid water, so it displaces enough water to float.", student_ids: ["s05"] },
    { cluster_id: 5, label: "No causal model yet", gap: "", reteach_suggestion: "Reteach with a concrete demonstration first: predict, then test which everyday objects sink or float.", category: "unclear", size: 5, percentage: 17, example_response: "It must be lighter than the water around it because it's frozen.", student_ids: ["s06"] },
  ],
};

export default function Preview() {
  return (
    <main className="app-shell" style={{ display: "grid", gap: 48 }}>
      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [1] empty
        </h2>
        <div className="panel">
          <CenterState
            icon={<SeedlingIcon />}
            title="Nothing diagnosed yet"
            body="Add responses to one question and RootCause will show you what your class actually thinks."
            actionLabel="Start a diagnostic"
            onAction={() => {}}
          />
        </div>
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [2] new diagnostic
        </h2>
        <Screen01Form onSubmit={() => {}} />
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [3] processing
        </h2>
        <div className="panel">
          <Screen02Processing total={30} currentStage={1} withNotes={false} />
        </div>
        <div className="panel" style={{ marginTop: 16 }}>
          <Screen02Processing total={30} currentStage={4} withNotes />
        </div>
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [4] dashboard
        </h2>
        <Screen03Dashboard
          result={FIXTURE}
          onNewDiagnostic={() => {}}
          onViewCluster={() => {}}
        />
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [5] too few
        </h2>
        <div className="panel">
          <CenterState
            title="Add a few more responses"
            body="Diagnostics need at least 8 responses to find a reliable pattern. This one has 4."
            actionLabel="Add more responses"
            onAction={() => {}}
          />
        </div>
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [6] cluster detail
        </h2>
        <Screen04Detail
          result={FIXTURE}
          cluster={FIXTURE.clusters[0]}
          onBack={() => {}}
        />
      </section>

      <section>
        <h2 style={{ fontSize: 16, fontFamily: "var(--font-data)", fontWeight: 400 }}>
          [7] branch chart alone
        </h2>
        <div className="panel" style={{ padding: 24 }}>
          <BranchChart cards={FIXTURE.clusters} />
        </div>
      </section>
    </main>
  );
}
