import Link from "next/link";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import MetricsPanel from "@/components/MetricsPanel";
import { getModelInfo } from "@/lib/api";

// This page fetches live model metrics from the backend at request time —
// not something to statically cache at build time, since those metrics
// can change when the model is retrained. Opts out of prerendering
// rather than fighting Next 16's Cache Components default.
export const instant = false;

export default async function HomePage() {
  const info = await getModelInfo().catch(() => null);

  return (
    <div className="mx-auto max-w-5xl px-6 py-12 space-y-8">
      <div>
        <h1 className="font-serif text-3xl text-primary">Lupira</h1>
        <p className="mt-2 max-w-2xl text-foreground/70">
          A research tool for SLE (lupus) classification using blood gene-expression profiles, with
          interpretable gene-level explanations and an NPSLE (neuropsychiatric lupus) risk-screening module
          based on the ACR 1999 case definitions.
        </p>
      </div>

      <DisclaimerBanner />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card href="/predict" title="Predict" desc="Upload gene expression data and get an SLE classification with SHAP explanations." />
        <Card href="/npsle" title="NPSLE Assessment" desc="Screen for neuropsychiatric lupus syndromes using the ACR 1999 case definitions." />
        <Card href="/about" title="About the Research" desc="Methodology, datasets, model comparison, and real validation results." />
      </div>

      {info && <MetricsPanel info={info} />}
    </div>
  );
}

function Card({ href, title, desc }: { href: string; title: string; desc: string }) {
  return (
    <Link href={href} className="block rounded border border-border bg-card p-5 hover:border-primary">
      <h2 className="font-medium text-primary">{title}</h2>
      <p className="mt-1 text-sm text-foreground/60">{desc}</p>
    </Link>
  );
}
