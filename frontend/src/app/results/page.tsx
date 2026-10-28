"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import PredictionCard from "@/components/PredictionCard";
import ShapChart from "@/components/ShapChart";
import { ApiError, explain } from "@/lib/api";
import type { ExplainResponse, PredictResponse } from "@/lib/types";

function ResultsContent() {
  const params = useSearchParams();
  const id = params.get("id");

  // read synchronously during render, not inside an effect — this is a
  // plain lookup of data already on the client (sessionStorage), not a
  // subscription to an external system, so there's nothing to
  // synchronize via useEffect for this part
  const [result] = useState<PredictResponse | null>(() => {
    if (!id || typeof window === "undefined") return null;
    const stored = sessionStorage.getItem(`lupira_result_${id}`);
    return stored ? JSON.parse(stored) : null;
  });
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<string | null>(
    id && !result ? "No prediction found for this ID in this session. Run a prediction first." : null,
  );

  useEffect(() => {
    if (!id || !result) return;
    explain(id)
      .then(setExplanation)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Could not load explanation."));
  }, [id, result]);

  if (!id) {
    return (
      <p className="text-sm text-foreground/60">
        No prediction selected. <Link href="/predict" className="text-primary underline">Run a prediction</Link>.
      </p>
    );
  }

  return (
    <div className="space-y-8">
      {error && <p className="rounded border border-risk-high/40 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">{error}</p>}

      {result && <PredictionCard result={result} />}

      {explanation && (
        <div>
          <h2 className="font-serif text-lg text-primary mb-3">
            Gene contributions (top {explanation.top_genes_count})
          </h2>
          <ShapChart contributions={explanation.shap_values} />
        </div>
      )}

      <div>
        <button
          onClick={() => window.print()}
          className="rounded border border-primary px-4 py-2 text-sm text-primary"
        >
          Download Report
        </button>
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
      <h1 className="font-serif text-2xl text-primary">Results</h1>
      <DisclaimerBanner />
      <Suspense fallback={<p className="text-sm text-foreground/60">Loading...</p>}>
        <ResultsContent />
      </Suspense>
    </div>
  );
}
