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
      if (e instanceof ApiError) console.error("NPSLE scoring failed:", e.status, e.message);
      setError("We couldn't calculate your score right now — please try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
      <h1 className="text-2xl font-semibold text-primary">Symptom Screening</h1>
      <DisclaimerBanner />
      <p className="text-sm text-foreground/70">
        If you&rsquo;ve already been diagnosed with lupus, this checklist screens for neuropsychiatric lupus
        (NPSLE) — neurological or psychiatric symptoms that can occur alongside lupus. Check anything
        you&rsquo;ve experienced; each item has a plain-language explanation below it. This is a screening
        aid based on established clinical criteria, not a diagnosis — see the note below the result for
        what the weighting does and doesn&rsquo;t represent.
      </p>

      <NpsleForm onSubmit={handleSubmit} loading={loading} />

      {error && <p className="text-sm text-risk-high">{error}</p>}
      {result && <NpsleResult result={result} />}
    </div>
  );
}
