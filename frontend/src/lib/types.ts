// Mirrors backend/app/models/schemas.py exactly — read from the real
// Pydantic models, not guessed from the spec doc alone.

export interface PredictResponse {
  prediction: "SLE" | "Healthy";
  probability: { SLE: number; Healthy: number };
  confidence: "high" | "moderate" | "low";
  model_used: string;
  prediction_id: string;
  timestamp: string;
  genes_used: number;
  genes_expected: number;
  gene_expression: Record<string, number>;
  input_quality: "typical" | "unusual";
  input_quality_note: string | null;
}

export interface ShapContribution {
  gene: string;
  value: number;
  expression: number;
  direction: "risk" | "protective";
}

export interface ExplainResponse {
  shap_values: ShapContribution[];
  base_value: number;
  top_genes_count: number;
}

export type NpsleCategory = "central" | "peripheral";
export type NpsleAttribution = "definitely_sle" | "possibly_sle" | "likely_non_sle";
export type TemporalRelation = "within_3_months" | "within_12_months" | "over_12_months" | "unknown";

export interface MatchedSyndrome {
  name: string;
  category: NpsleCategory;
  weight: number;
  attribution: NpsleAttribution;
}

export interface NpsleResponse {
  risk_score: number;
  risk_category: "Low" | "Moderate" | "High" | "Critical";
  matched_syndromes: MatchedSyndrome[];
  note: string;
}

export interface ModelInfoResponse {
  model_type: string;
  training_dataset: string;
  training_n_samples: number;
  validation_datasets: string[];
  metrics: {
    cv_auc: number;
    cv_f1: number;
    cv_sensitivity: number;
    cv_specificity: number;
    external_auc_by_dataset: Record<string, number>;
  };
  n_features: number;
  top_features: string[];
  required_genes: string[];
  notes: string;
}

export interface HealthResponse {
  status: "ok";
  model_loaded: boolean;
  model_name: string;
  feature_count: number;
}

export interface GeneRow {
  gene: string;
  value: number;
}
