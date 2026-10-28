import MetricsPanel from "@/components/MetricsPanel";
import { getModelInfo } from "@/lib/api";

export const instant = false;

export default async function AboutPage() {
  const info = await getModelInfo().catch(() => null);

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-8 font-serif">
      <div>
        <h1 className="text-2xl text-primary">About the Research</h1>
        <p className="mt-3 text-foreground/80 leading-relaxed">
          Lupira classifies blood gene-expression samples as SLE-positive or healthy, explains which
          genes drove each prediction, and includes a separate rule-based NPSLE (neuropsychiatric lupus)
          risk-screening module based on the ACR 1999 case definitions.
        </p>
      </div>

      <section>
        <h2 className="text-lg text-primary">Methodology</h2>
        <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-foreground/80">
          <li>
            <strong>Training data:</strong> GSE50772 only (Affymetrix HG-U133 Plus 2.0, 81 samples — 61
            SLE, 20 healthy).
          </li>
          <li>
            <strong>Preprocessing:</strong> log2 transform where needed, quantile normalization, probe-to-gene
            mapping via the platform&rsquo;s own annotation, with known sex-chromosome genes excluded from
            the candidate pool to avoid a confound with SLE&rsquo;s real female predominance.
          </li>
          <li>
            <strong>Feature selection:</strong> differential expression filtering, then LASSO, then stability
            selection across 5 resampled folds — genes are only kept if selected in most folds, not just
            once on the full dataset.
          </li>
          <li>
            <strong>Models compared:</strong> SVM, Random Forest, XGBoost, MLP — all four trained and
            reported, not just the best.
          </li>
          <li>
            <strong>External validation:</strong> GSE72509 (RNA-seq, different measurement technology) and
            GSE49454 (Illumina), both fully independent of training and feature selection.
          </li>
          <li>
            <strong>Interpretability:</strong> SHAP (KernelExplainer) on the shipped model.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg text-primary">A deliberate methodology choice</h2>
        <p className="mt-2 text-sm text-foreground/80 leading-relaxed">
          GSE72509 is RNA-seq, not microarray — a different measurement technology from the training data.
          Merging it into training with ComBat batch correction (a common approach when datasets share a
          platform) would not have been scientifically valid here, since ComBat corrects batch effects
          within one technology, not differences between technologies. It is used only as an independent
          external validation set instead.
        </p>
      </section>

      {info && (
        <section>
          <h2 className="text-lg text-primary mb-3">Results</h2>
          <MetricsPanel info={info} />
        </section>
      )}

      <section>
        <h2 className="text-lg text-primary">Citation</h2>
        <p className="mt-2 text-sm text-foreground/80">
          The original version of this work was published as: &ldquo;AI-Lupira: A Machine Learning-Powered
          Mobile System for Lupus Detection and Symptom Analysis&rdquo; (MUST, 2025). This is a full rebuild
          with research-grade methodology and production engineering.
        </p>
      </section>

      <section>
        <h2 className="text-lg text-primary">Disclaimer</h2>
        <p className="mt-2 text-sm text-foreground/80">
          This tool is for research and educational purposes only. It is not a medical device and should
          not be used for clinical decision-making.
        </p>
      </section>
    </div>
  );
}
