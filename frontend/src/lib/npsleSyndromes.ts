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

// Plain-language explanation of each ACR 1999 syndrome, for patients who
// don't already know the clinical terms. Purely presentational — doesn't
// change the syndrome list, weights, or scoring logic in any way.
export const SYNDROME_GLOSSARY: Record<string, string> = {
  "Aseptic meningitis":
    "Inflammation of the membranes around the brain and spinal cord, not caused by a typical infection — can cause headache, neck stiffness, and fever.",
  "Cerebrovascular disease":
    "Problems with blood flow to the brain, such as a stroke or mini-stroke, which can affect movement, speech, or vision.",
  "Demyelinating syndrome":
    "Damage to the protective coating (myelin) around nerve fibers in the brain or spinal cord, which can affect vision, sensation, or movement.",
  "Headache (intractable)": "A severe, persistent headache that doesn't respond to usual pain relief.",
  "Movement disorder (chorea)": "Sudden, irregular, uncontrollable movements of the limbs or face.",
  Myelopathy: "Damage to the spinal cord that can cause weakness, numbness, or loss of bladder/bowel control.",
  "Seizure disorders":
    "Episodes of abnormal electrical activity in the brain, which can cause convulsions or temporary loss of awareness.",
  "Acute confusional state":
    "A sudden onset of confusion, disorientation, or trouble thinking clearly (also called delirium).",
  "Anxiety disorder": "Persistent, excessive worry or fear that interferes with daily life.",
  "Cognitive dysfunction": "Trouble with memory, concentration, or clear thinking.",
  "Mood disorder": "Significant, persistent changes in mood, such as depression.",
  Psychosis:
    "Losing touch with reality — such as seeing or hearing things that aren't there, or holding strong false beliefs.",
  "Acute inflammatory demyelinating polyradiculoneuropathy (Guillain-Barré)":
    "A rare condition where the immune system attacks the nerves, causing rapidly worsening weakness, often starting in the legs.",
  "Autonomic disorder":
    "Problems with the body's automatic functions, like heart rate, blood pressure, digestion, or sweating.",
  "Mononeuropathy (single/multiplex)":
    "Damage to a single nerve, or several individual nerves, causing weakness or numbness in a specific area.",
  "Myasthenia gravis":
    "A condition causing muscle weakness that worsens with activity and improves with rest, often affecting the eyes, face, or limbs.",
  "Cranial neuropathy":
    "Damage to a nerve that controls the face, eyes, or other head structures — can cause facial weakness, double vision, or numbness.",
  Plexopathy:
    "Damage to a network of nerves, often near the shoulder or hip, that can cause pain, weakness, or numbness in an arm or leg.",
  Polyneuropathy:
    "Damage to many nerves at once, typically causing symmetrical numbness, tingling, or weakness, often starting in the hands and feet.",
};

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
