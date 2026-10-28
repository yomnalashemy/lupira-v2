// Must match backend/app/services/npsle_scorer.py's NPSLE_SYNDROMES
// exactly — the backend 422s on any name it doesn't recognize.
export const NPSLE_SYNDROMES = {
  central: [
    "Aseptic meningitis",
    "Cerebrovascular disease",
    "Demyelinating syndrome",
    "Headache (intractable)",
    "Movement disorder (chorea)",
    "Myelopathy",
    "Seizure disorders",
    "Acute confusional state",
    "Anxiety disorder",
    "Cognitive dysfunction",
    "Mood disorder",
    "Psychosis",
  ],
  peripheral: [
    "Acute inflammatory demyelinating polyradiculoneuropathy (Guillain-Barré)",
    "Autonomic disorder",
    "Mononeuropathy (single/multiplex)",
    "Myasthenia gravis",
    "Cranial neuropathy",
    "Plexopathy",
    "Polyneuropathy",
  ],
} as const;

export const CONFOUNDING_FACTORS = [
  { value: "medication_side_effect", label: "Medication side effect" },
  { value: "infection", label: "Infection" },
  { value: "metabolic_disturbance", label: "Metabolic disturbance" },
  { value: "pre_existing_condition", label: "Pre-existing condition" },
] as const;

export const TEMPORAL_OPTIONS = [
  { value: "within_3_months", label: "Within 3 months of SLE diagnosis" },
  { value: "within_12_months", label: "Within 12 months of SLE diagnosis" },
  { value: "over_12_months", label: "Over 12 months since SLE diagnosis" },
  { value: "unknown", label: "Unknown" },
] as const;
