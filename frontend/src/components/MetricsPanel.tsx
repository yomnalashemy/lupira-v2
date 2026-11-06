import type { ModelInfoResponse } from "@/lib/types";

export default function MetricsPanel({ info }: { info: ModelInfoResponse }) {
  const m = info.metrics;
  return (
    <div className="rounded border border-border bg-card p-6">
      <h3 className="font-serif text-lg">Model performance</h3>
      <p className="mt-1 text-sm text-foreground/60">
        {info.model_type}, trained on {info.training_dataset} ({info.training_n_samples} samples), {info.n_features}{" "}
        selected genes.
      </p>

      <p className="mt-3 text-sm text-foreground/80">
        In testing, this model correctly identified lupus patterns in about {Math.round(m.cv_sensitivity * 100)}%
        of confirmed lupus cases, and correctly ruled out lupus in about {Math.round(m.cv_specificity * 100)}% of
        healthy cases.
      </p>

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Metric label="Internal CV AUC" value={m.cv_auc} />
        <Metric label="Internal CV F1" value={m.cv_f1} />
        <Metric label="Sensitivity" value={m.cv_sensitivity} />
        <Metric label="Specificity" value={m.cv_specificity} />
      </div>

      <h4 className="mt-6 text-sm font-medium text-primary">External validation AUC (independent cohorts)</h4>
      <div className="mt-2 grid grid-cols-2 gap-4">
        {Object.entries(m.external_auc_by_dataset).map(([dataset, auc]) => (
          <Metric key={dataset} label={dataset} value={auc} />
        ))}
      </div>

      <p className="mt-6 font-serif text-sm text-foreground/70">{info.notes}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-2xl font-semibold text-primary">{value.toFixed(3)}</p>
      <p className="text-xs text-foreground/50">{label}</p>
    </div>
  );
}
