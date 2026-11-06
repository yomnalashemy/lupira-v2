"use client";

import { useState } from "react";
import { CONFOUNDING_FACTORS, NPSLE_SYNDROMES, SYNDROME_GLOSSARY, TEMPORAL_OPTIONS } from "@/lib/npsleSyndromes";
import type { TemporalRelation } from "@/lib/types";

export interface NpsleFormValues {
  syndromes: string[];
  sleDiagnosisConfirmed: boolean;
  temporalRelation: TemporalRelation;
  confoundingFactors: string[];
}

interface Option {
  value: string;
  label: string;
  gloss?: string;
}

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

const CENTRAL_OPTIONS: Option[] = NPSLE_SYNDROMES.central.map((s) => ({ value: s, label: s, gloss: SYNDROME_GLOSSARY[s] }));
const PERIPHERAL_OPTIONS: Option[] = NPSLE_SYNDROMES.peripheral.map((s) => ({ value: s, label: s, gloss: SYNDROME_GLOSSARY[s] }));
const CONFIRMED_OPTIONS: Option[] = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No / not yet" },
];
const TEMPORAL_MCQ_OPTIONS: Option[] = TEMPORAL_OPTIONS.map((t) => ({ value: t.value, label: t.label }));
const CONFOUNDER_OPTIONS: Option[] = CONFOUNDING_FACTORS.map((f) => ({ value: f.value, label: f.label }));

type Step = "central" | "peripheral" | "confirmed" | "temporal" | "confounders" | "review";

export default function NpsleForm({ onSubmit, loading }: { onSubmit: (values: NpsleFormValues) => void; loading: boolean }) {
  const [syndromes, setSyndromes] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState<boolean | null>(null);
  const [temporal, setTemporal] = useState<TemporalRelation | null>(null);
  const [confounders, setConfounders] = useState<string[]>([]);
  const [stepIndex, setStepIndex] = useState(0);

  function toggle(list: string[], value: string, set: (v: string[]) => void) {
    set(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  const hasSymptoms = syndromes.length > 0;
  const steps: Step[] = hasSymptoms
    ? ["central", "peripheral", "confirmed", "temporal", "confounders", "review"]
    : ["central", "peripheral", "review"];
  const step = steps[Math.min(stepIndex, steps.length - 1)];

  function next() {
    setStepIndex((i) => Math.min(i + 1, steps.length - 1));
  }
  function back() {
    setStepIndex((i) => Math.max(i - 1, 0));
  }

  function handleSubmit() {
    onSubmit({
      syndromes,
      sleDiagnosisConfirmed: confirmed ?? true,
      temporalRelation: temporal ?? "unknown",
      confoundingFactors: confounders,
    });
  }

  return (
    <div className="space-y-6">
      <p className="text-xs text-foreground/50">
        Question {stepIndex + 1} of {steps.length}
      </p>

      {step === "central" && (
        <MultiSelectQuestion
          title="Which of these neurological symptoms have you experienced? (Select all that apply)"
          options={CENTRAL_OPTIONS}
          selected={syndromes}
          onToggle={(v) => toggle(syndromes, v, setSyndromes)}
        />
      )}

      {step === "peripheral" && (
        <MultiSelectQuestion
          title="Which of these nerve-related symptoms have you experienced? (Select all that apply)"
          options={PERIPHERAL_OPTIONS}
          selected={syndromes}
          onToggle={(v) => toggle(syndromes, v, setSyndromes)}
        />
      )}

      {step === "confirmed" && (
        <SingleSelectQuestion
          title="Has lupus (SLE) been confirmed by a doctor?"
          options={CONFIRMED_OPTIONS}
          selected={confirmed === null ? null : confirmed ? "yes" : "no"}
          onSelect={(v) => setConfirmed(v === "yes")}
        />
      )}

      {step === "temporal" && (
        <SingleSelectQuestion
          title="When did these symptoms occur relative to your lupus diagnosis?"
          options={TEMPORAL_MCQ_OPTIONS}
          selected={temporal}
          onSelect={(v) => setTemporal(v as TemporalRelation)}
        />
      )}

      {step === "confounders" && (
        <MultiSelectQuestion
          title="Do any of these also apply? (Select all that apply, or none)"
          options={CONFOUNDER_OPTIONS}
          selected={confounders}
          onToggle={(v) => toggle(confounders, v, setConfounders)}
        />
      )}

      {step === "review" && (
        <fieldset>
          <legend className="mb-3 text-base font-medium text-primary">Review your answers</legend>
          {hasSymptoms ? (
            <ul className="list-disc space-y-1 pl-5 text-sm text-foreground/80">
              <li>Symptoms selected ({syndromes.length}): {syndromes.join(", ")}</li>
              <li>SLE diagnosis confirmed: {confirmed ? "Yes" : "No / not yet"}</li>
              <li>Timing: {TEMPORAL_OPTIONS.find((t) => t.value === temporal)?.label ?? "Unknown"}</li>
              <li>
                Other factors:{" "}
                {confounders.length > 0
                  ? confounders.map((v) => CONFOUNDING_FACTORS.find((f) => f.value === v)?.label).join(", ")
                  : "None"}
              </li>
            </ul>
          ) : (
            <p className="text-sm text-foreground/70">No symptoms selected — your score will be Low.</p>
          )}
        </fieldset>
      )}

      <div className="flex justify-between pt-2">
        <button
          type="button"
          onClick={back}
          disabled={stepIndex === 0}
          className="rounded border border-border px-4 py-2 text-sm disabled:opacity-40"
        >
          Back
        </button>
        {step === "review" ? (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="rounded bg-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Calculating..." : "Calculate My Score"}
          </button>
        ) : (
          <button type="button" onClick={next} className="rounded bg-primary px-5 py-2.5 text-sm font-medium text-white">
            Next
          </button>
        )}
      </div>
    </div>
  );
}

function OptionButton({
  letter,
  label,
  gloss,
  isSelected,
  onClick,
}: {
  letter: string;
  label: string;
  gloss?: string;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      className={`flex w-full items-start gap-3 rounded border p-3 text-left transition-colors ${
        isSelected ? "border-accent bg-accent-soft" : "border-border bg-card hover:border-accent/50"
      }`}
    >
      <span
        className={`mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
          isSelected ? "border-accent bg-accent text-white" : "border-border text-foreground/50"
        }`}
      >
        {letter}
      </span>
      <span>
        <span className="block text-sm font-medium">{label}</span>
        {gloss && <span className="block text-xs text-foreground/50">{gloss}</span>}
      </span>
    </button>
  );
}

function MultiSelectQuestion({
  title,
  options,
  selected,
  onToggle,
}: {
  title: string;
  options: Option[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-3 text-base font-medium text-primary">{title}</legend>
      <div className="space-y-2">
        {options.map((option, i) => (
          <OptionButton
            key={option.value}
            letter={LETTERS[i]}
            label={option.label}
            gloss={option.gloss}
            isSelected={selected.includes(option.value)}
            onClick={() => onToggle(option.value)}
          />
        ))}
      </div>
    </fieldset>
  );
}

function SingleSelectQuestion({
  title,
  options,
  selected,
  onSelect,
}: {
  title: string;
  options: Option[];
  selected: string | null;
  onSelect: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-3 text-base font-medium text-primary">{title}</legend>
      <div className="space-y-2">
        {options.map((option, i) => (
          <OptionButton
            key={option.value}
            letter={LETTERS[i]}
            label={option.label}
            isSelected={selected === option.value}
            onClick={() => onSelect(option.value)}
          />
        ))}
      </div>
    </fieldset>
  );
}
