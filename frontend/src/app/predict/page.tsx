"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FlaskConical, HelpCircle } from "lucide-react";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import GeneUploader from "@/components/GeneUploader";
import { ApiError, getModelInfo, predict } from "@/lib/api";

type Mode = "ask" | "upload" | "guide";

function modeFromParam(value: string | null): Mode {
  return value === "upload" || value === "guide" ? value : "ask";
}

function PredictContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [mode, setMode] = useState<Mode>(() => modeFromParam(params.get("mode")));
  const [requiredGenes, setRequiredGenes] = useState<string[]>([]);
  const [expression, setExpression] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "upload") return;
    getModelInfo()
      .then((info) => setRequiredGenes(info.required_genes))
      .catch(() => setError("We couldn't reach the results checker right now — please try again in a moment."));
  }, [mode]);

  async function runPrediction() {
    if (!expression) return;
    setLoading(true);
    setError(null);
    try {
      const result = await predict(expression);
      sessionStorage.setItem(`lupira_result_${result.prediction_id}`, JSON.stringify(result));
      router.push(`/results?id=${result.prediction_id}`);
    } catch (e) {
      if (e instanceof ApiError) console.error("Prediction failed:", e.status, e.message);
      setError("We couldn't check your results right now — please try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  if (mode === "ask") {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
        <h1 className="text-2xl font-semibold text-primary">Check My Results</h1>
        <DisclaimerBanner />
        <p className="text-foreground/80">Do you have gene-expression test results from a lab or doctor?</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <button
            onClick={() => setMode("upload")}
            className="flex items-start gap-3 rounded border border-border bg-card p-5 text-left shadow-soft transition-colors hover:border-accent"
          >
            <FlaskConical className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
            <span>
              <span className="block font-medium text-primary">Yes, I have results</span>
              <span className="block text-sm text-foreground/60">Upload the file and we&rsquo;ll analyze it.</span>
            </span>
          </button>
          <button
            onClick={() => setMode("guide")}
            className="flex items-start gap-3 rounded border border-border bg-card p-5 text-left shadow-soft transition-colors hover:border-accent"
          >
            <HelpCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
            <span>
              <span className="block font-medium text-primary">No, not yet</span>
              <span className="block text-sm text-foreground/60">
                We&rsquo;ll explain what this test is and how to get one.
              </span>
            </span>
          </button>
        </div>
      </div>
    );
  }

  if (mode === "guide") {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
        <h1 className="text-2xl font-semibold text-primary">Getting tested</h1>
        <DisclaimerBanner />
        <div className="space-y-4 text-foreground/80 leading-relaxed">
          <p>
            This tool reads a specific kind of blood test called a <strong>gene-expression profile</strong>{" "}
            (sometimes called a transcriptomic, microarray, or RNA-seq panel). It measures how active certain
            genes are in your blood cells — a more detailed test than a standard blood panel, and not
            something most routine checkups include.
          </p>
          <p>
            Symptoms alone — joint pain, fatigue, rashes, and so on — overlap with many other conditions,
            which is part of why lupus is so hard to diagnose from symptoms by themselves. That overlap is
            exactly what this kind of test is designed to help cut through.
          </p>
          <p className="font-medium text-primary">What to do next</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>Ask your doctor or rheumatologist whether a gene-expression (transcriptomic) panel makes sense for you.</li>
            <li>If you&rsquo;re part of a research study that has already run this kind of test, ask for a copy of your results file.</li>
            <li>
              Once you have a results file, come back and choose{" "}
              <button onClick={() => setMode("upload")} className="text-accent underline">
                &ldquo;I have test results&rdquo;
              </button>
              .
            </li>
          </ul>
          <p className="text-sm text-foreground/60">
            Already diagnosed with lupus and tracking neurological or psychiatric symptoms instead? Try the{" "}
            <a href="/npsle" className="text-accent underline">
              symptom screening
            </a>
            .
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-6">
      <h1 className="text-2xl font-semibold text-primary">Check My Results</h1>
      <DisclaimerBanner />

      {requiredGenes.length > 0 ? (
        <>
          <p className="text-sm text-foreground/70">
            Upload the file your lab or doctor gave you — we&rsquo;ll handle the technical part. Extra genes
            in the file beyond what the model needs are fine; they&rsquo;re just ignored.
          </p>
          <GeneUploader requiredGenes={requiredGenes} onParsed={setExpression} />
          {error && <p className="text-sm text-risk-high">{error}</p>}
          <button
            onClick={runPrediction}
            disabled={!expression || loading}
            className="rounded bg-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Checking your results..." : "Check My Results"}
          </button>
        </>
      ) : (
        <p className="text-sm text-foreground/60">{error || "Getting ready..."}</p>
      )}
    </div>
  );
}

export default function PredictPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-3xl px-6 py-12">
          <p className="text-sm text-foreground/60">Loading...</p>
        </div>
      }
    >
      <PredictContent />
    </Suspense>
  );
}
