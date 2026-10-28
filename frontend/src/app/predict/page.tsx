"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import GeneUploader from "@/components/GeneUploader";
import { ApiError, getModelInfo, predict } from "@/lib/api";

export default function PredictPage() {
  const router = useRouter();
  const [requiredGenes, setRequiredGenes] = useState<string[]>([]);
  const [expression, setExpression] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getModelInfo()
      .then((info) => setRequiredGenes(info.required_genes))
      .catch(() => setError("Could not reach the Lupira API. Is the backend running?"));
  }, []);

  async function runPrediction() {
    if (!expression) return;
    setLoading(true);
    setError(null);
    try {
      const result = await predict(expression);
      sessionStorage.setItem(`lupira_result_${result.prediction_id}`, JSON.stringify(result));
      router.push(`/results?id=${result.prediction_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Prediction failed — the backend may be unreachable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
      <h1 className="font-serif text-2xl text-primary">Predict</h1>
      <DisclaimerBanner />

      {requiredGenes.length > 0 ? (
        <>
          <GeneUploader requiredGenes={requiredGenes} onParsed={setExpression} />
          {error && <p className="text-sm text-risk-high">{error}</p>}
          <button
            onClick={runPrediction}
            disabled={!expression || loading}
            className="rounded bg-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Running prediction..." : "Run Prediction"}
          </button>
        </>
      ) : (
        <p className="text-sm text-foreground/60">{error || "Loading required gene list..."}</p>
      )}
    </div>
  );
}
