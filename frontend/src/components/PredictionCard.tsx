import type { PredictResponse } from "@/lib/types";

export default function PredictionCard({ result }: { result: PredictResponse }) {
  const isSle = result.prediction === "SLE";
  const color = isSle ? "var(--risk-high)" : "var(--risk-healthy)";
  const pct = Math.round(result.probability[result.prediction] * 100);

  return (
    <div className="rounded border border-border bg-card p-6">
      <div
        className="inline-block rounded px-4 py-2 text-lg font-semibold text-white"
        style={{ backgroundColor: color }}
      >
        {isSle ? "SLE Detected" : "Healthy"}
      </div>

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

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
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
    </div>
  );
}
