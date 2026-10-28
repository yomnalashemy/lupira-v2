"use client";

import { useState } from "react";
import { CONFOUNDING_FACTORS, NPSLE_SYNDROMES, TEMPORAL_OPTIONS } from "@/lib/npsleSyndromes";
import type { TemporalRelation } from "@/lib/types";

export interface NpsleFormValues {
  syndromes: string[];
  sleDiagnosisConfirmed: boolean;
  temporalRelation: TemporalRelation;
  confoundingFactors: string[];
}

export default function NpsleForm({ onSubmit, loading }: { onSubmit: (values: NpsleFormValues) => void; loading: boolean }) {
  const [syndromes, setSyndromes] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(true);
  const [temporal, setTemporal] = useState<TemporalRelation>("unknown");
  const [confounders, setConfounders] = useState<string[]>([]);

  function toggle(list: string[], value: string, set: (v: string[]) => void) {
    set(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ syndromes, sleDiagnosisConfirmed: confirmed, temporalRelation: temporal, confoundingFactors: confounders });
      }}
      className="space-y-6"
    >
      <fieldset className="rounded border border-border p-4">
        <legend className="px-1 text-sm font-medium text-primary">Central NS syndromes</legend>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {NPSLE_SYNDROMES.central.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={syndromes.includes(s)}
                onChange={() => toggle(syndromes, s, setSyndromes)}
              />
              {s}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="rounded border border-border p-4">
        <legend className="px-1 text-sm font-medium text-primary">Peripheral NS syndromes</legend>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {NPSLE_SYNDROMES.peripheral.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={syndromes.includes(s)}
                onChange={() => toggle(syndromes, s, setSyndromes)}
              />
              {s}
            </label>
          ))}
        </div>
      </fieldset>

      {syndromes.length > 0 && (
        <fieldset className="rounded border border-border p-4 space-y-4">
          <legend className="px-1 text-sm font-medium text-primary">Attribution context</legend>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            SLE diagnosis confirmed
          </label>

          <div>
            <label className="block text-sm text-foreground/70 mb-1">Temporal relation to SLE diagnosis</label>
            <select
              value={temporal}
              onChange={(e) => setTemporal(e.target.value as TemporalRelation)}
              className="w-full rounded border border-border px-3 py-2 text-sm"
            >
              {TEMPORAL_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <p className="text-sm text-foreground/70 mb-1">Confounding factors present</p>
            <div className="flex flex-wrap gap-3">
              {CONFOUNDING_FACTORS.map((f) => (
                <label key={f.value} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={confounders.includes(f.value)}
                    onChange={() => toggle(confounders, f.value, setConfounders)}
                  />
                  {f.label}
                </label>
              ))}
            </div>
          </div>
        </fieldset>
      )}

      <button
        type="submit"
        disabled={loading}
        className="rounded bg-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {loading ? "Calculating..." : "Calculate Risk Score"}
      </button>
    </form>
  );
}
