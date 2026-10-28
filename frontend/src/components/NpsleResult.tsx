import type { NpsleResponse } from "@/lib/types";

const CATEGORY_COLOR: Record<string, string> = {
  Low: "var(--risk-healthy)",
  Moderate: "var(--risk-moderate)",
  High: "var(--risk-high)",
  Critical: "var(--risk-high)",
};

const ATTRIBUTION_LABEL: Record<string, string> = {
  definitely_sle: "Definitely SLE-related",
  possibly_sle: "Possibly SLE-related",
  likely_non_sle: "Likely non-SLE",
};

export default function NpsleResult({ result }: { result: NpsleResponse }) {
  return (
    <div className="rounded border border-border bg-card p-6">
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-semibold" style={{ color: CATEGORY_COLOR[result.risk_category] }}>
          {result.risk_category}
        </span>
        <span className="text-sm text-foreground/60">risk score: {result.risk_score}</span>
      </div>

      {result.matched_syndromes.length > 0 && (
        <table className="mt-4 w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-foreground/50">
              <th className="py-1 font-normal">Syndrome</th>
              <th className="py-1 font-normal">Category</th>
              <th className="py-1 font-normal">Attribution</th>
            </tr>
          </thead>
          <tbody>
            {result.matched_syndromes.map((m) => (
              <tr key={m.name} className="border-b border-border">
                <td className="py-1.5 pr-2">{m.name}</td>
                <td className="py-1.5 pr-2 capitalize">{m.category}</td>
                <td className="py-1.5">{ATTRIBUTION_LABEL[m.attribution]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="mt-4 font-serif text-sm text-foreground/70">{result.note}</p>
    </div>
  );
}
