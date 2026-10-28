"use client";

import { useState } from "react";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import NpsleForm, { type NpsleFormValues } from "@/components/NpsleForm";
import NpsleResult from "@/components/NpsleResult";
import { ApiError, scoreNpsle } from "@/lib/api";
import type { NpsleResponse } from "@/lib/types";

export default function NpslePage() {
  const [result, setResult] = useState<NpsleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(values: NpsleFormValues) {
    setLoading(true);
    setError(null);
    try {
      const res = await scoreNpsle(
        values.syndromes,
        values.sleDiagnosisConfirmed,
        values.temporalRelation,
        values.confoundingFactors,
      );
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not reach the Lupira API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
      <h1 className="font-serif text-2xl text-primary">NPSLE Assessment</h1>
      <DisclaimerBanner />
      <p className="text-sm text-foreground/70">
        Select any observed neuropsychiatric syndromes from the ACR 1999 case definitions. This is a
        screening aid, not a diagnosis — see the note below the result for what the weighting does and
        doesn&rsquo;t represent.
      </p>

      <NpsleForm onSubmit={handleSubmit} loading={loading} />

      {error && <p className="text-sm text-risk-high">{error}</p>}
      {result && <NpsleResult result={result} />}
    </div>
  );
}
