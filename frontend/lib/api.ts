export type Category = "misconception" | "solid_understanding" | "unclear";

export interface ClusterCard {
  cluster_id: number;
  label: string;
  gap: string;
  reteach_suggestion: string;
  category: Category;
  size: number;
  percentage: number;
  example_response: string;
  student_ids: string[];
}

export interface StudentRecord {
  student_id: string;
  response_text: string;
  reasoning_summary: string;
  feedback_note?: string;
}

export interface DiagnoseResult {
  status: "ok";
  question: string;
  responses_analyzed: number;
  records: StudentRecord[];
  clusters: ClusterCard[];
}

export interface InsufficientResponses {
  error: "insufficient_responses";
  message: string;
  received: number;
  minimum: number;
}

export interface ModelUnavailable {
  error: "model_unavailable";
  message: string;
}

export function isInsufficient(body: unknown): body is { detail: InsufficientResponses } {
  return (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof (body as { detail: unknown }).detail === "object" &&
    (body as { detail: InsufficientResponses }).detail?.error ===
      "insufficient_responses"
  );
}

export function isModelUnavailable(body: unknown): body is { detail: ModelUnavailable } {
  return (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof (body as { detail: unknown }).detail === "object" &&
    (body as { detail: ModelUnavailable }).detail?.error === "model_unavailable"
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function diagnose(payload: {
  question: string;
  correct_concept?: string;
  include_feedback: boolean;
  responses: { response: string }[];
}): Promise<DiagnoseResult> {
  const res = await fetch(`${API_BASE}/api/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    if (res.status === 422 && isInsufficient(body)) {
      throw Object.assign(new Error(body.detail.message), {
        insufficient: body.detail,
      });
    }
    if (res.status === 503 && isModelUnavailable(body)) {
      throw Object.assign(new Error(body.detail.message), {
        modelUnavailable: body.detail,
      });
    }
    throw new Error(`Diagnose failed (${res.status})`);
  }
  return res.json();
}
