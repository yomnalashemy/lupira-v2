import { AlertTriangle } from "lucide-react";
import type { PredictResponse } from "@/lib/types";

const PLAIN_SUMMARY: Record<"SLE" | "Healthy", string> = {
  SLE: "Your results show patterns that are closely associated with lupus in medical studies.",
  Healthy: "Your results show patterns that are not typically associated with lupus in medical studies.",
};

export default function PredictionCard({ result }: { result: PredictResponse }) {
  const isSle = result.prediction === "SLE";
  const color = isSle ? "var(--risk-high)" : "var(--risk-healthy)";
  const pct = Math.round(result.probability[result.prediction] * 100);

  return (
    <div className="rounded border border-border bg-card p-6 shadow-soft">
      {result.input_quality === "unusual" && result.input_quality_note && (
        <div className="mb-4 flex items-start gap-2 rounded border border-risk-moderate/40 bg-risk-moderate/10 px-3 py-2 text-sm text-foreground">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-risk-moderate" />
          <span>{result.input_quality_note}</span>
        </div>
      )}

      <p className="text-foreground/80">{PLAIN_SUMMARY[result.prediction]}</p>

      <div
        className="mt-3 inline-block rounded px-4 py-2 text-lg font-semibold text-white"
        style={{ backgroundColor: color }}
      >
        {isSle ? "SLE Detected" : "Healthy"}
      </div>

      <p className="mt-3 text-sm text-foreground/60">
        This is a screening result, not a diagnosis — share it with a rheumatologist for confirmation.
      </p>

      <div className="mt-4">
        <div className="flex justify-between text-sm text-foreground/70">
          <span>SLE probability</span>
          <span>{Math.round(result.probability.SLE * 100)}%</span>
        </div>
        <div className="mt-1 h-3 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full bg-risk-high"
            style={{ width: `${Math.round(result.probability.SLE * 100)}%` }}
          />
        </div>
      </div>

      <details className="mt-4 text-sm">
        <summary className="cursor-pointer text-foreground/60">Technical details</summary>
        <dl className="mt-3 grid grid-cols-2 gap-3">
          <div>
            <dt className="text-foreground/50">Confidence</dt>
            <dd className="font-medium capitalize">
              {result.confidence} ({pct}%)
            </dd>
          </div>
          <div>
            <dt className="text-foreground/50">Model</dt>
            <dd className="font-medium">{result.model_used}</dd>
          </div>
          <div>
            <dt className="text-foreground/50">Genes used</dt>
            <dd className="font-medium">
              {result.genes_used}/{result.genes_expected}
            </dd>
          </div>
          <div>
            <dt className="text-foreground/50">Prediction ID</dt>
            <dd className="font-mono text-xs">{result.prediction_id.slice(0, 8)}</dd>
          </div>
        </dl>
      </details>
    </div>
  );
}
