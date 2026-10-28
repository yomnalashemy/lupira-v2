import type {
  ExplainResponse,
  HealthResponse,
  ModelInfoResponse,
  NpsleResponse,
  PredictResponse,
  TemporalRelation,
} from "./types";

// Server Components (page.tsx's async home/about pages) run their fetch
// INSIDE the frontend container, where "localhost" means the container
// itself, not the backend container — confirmed by actually testing this
// in Docker, not assumed. The browser's own fetches (everything in
// components/*.tsx marked "use client") run on the host/user's machine,
// where localhost correctly reaches the backend's published port. These
// need different base URLs in a multi-container deployment:
// INTERNAL_API_URL (server-only, never sent to the client bundle) for
// the server-side case, NEXT_PUBLIC_API_URL for the browser case. Same
// value by default, so plain `next dev`/`next start` on one host needs
// no extra config — only docker-compose.yml sets them differently.
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const API_URL = typeof window === "undefined" ? process.env.INTERNAL_API_URL || PUBLIC_API_URL : PUBLIC_API_URL;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function predict(geneExpression: Record<string, number>, patientId?: string): Promise<PredictResponse> {
  return request<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify({ gene_expression: geneExpression, patient_id: patientId }),
  });
}

export function explain(predictionId: string): Promise<ExplainResponse> {
  return request<ExplainResponse>("/explain", {
    method: "POST",
    body: JSON.stringify({ prediction_id: predictionId }),
  });
}

export function scoreNpsle(
  syndromes: string[],
  sleDiagnosisConfirmed: boolean,
  temporalRelation: TemporalRelation,
  confoundingFactors: string[],
): Promise<NpsleResponse> {
  return request<NpsleResponse>("/npsle-score", {
    method: "POST",
    body: JSON.stringify({
      syndromes,
      sle_diagnosis_confirmed: sleDiagnosisConfirmed,
      temporal_relation: temporalRelation,
      confounding_factors: confoundingFactors,
    }),
  });
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getModelInfo(): Promise<ModelInfoResponse> {
  return request<ModelInfoResponse>("/model-info");
}
