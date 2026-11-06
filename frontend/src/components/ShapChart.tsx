"use client";

import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";
import type { ShapContribution } from "@/lib/types";

export default function ShapChart({ contributions }: { contributions: ShapContribution[] }) {
  const data = [...contributions]
    .sort((a, b) => a.value - b.value)
    .map((c) => ({ ...c, label: c.gene }));

  const top3 = [...contributions].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 3);

  return (
    <div>
      {top3.length > 0 && (
        <p className="mb-3 text-sm text-foreground/70">
          The genes with the biggest influence on this result were{" "}
          {top3.map((c, i) => (
            <span key={c.gene}>
              <strong>{c.gene}</strong>
              {i < top3.length - 2 ? ", " : i === top3.length - 2 ? ", and " : ""}
            </span>
          ))}
          .
        </p>
      )}
      <BarChart width={640} height={Math.max(260, data.length * 28)} data={data} layout="vertical" margin={{ left: 80 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickFormatter={(v: number) => v.toFixed(2)} />
        <YAxis type="category" dataKey="label" width={80} tick={{ fontSize: 12 }} />
        <ReferenceLine x={0} stroke="#718096" />
        <Tooltip
          formatter={(value, _name, item) => {
            const num = typeof value === "number" ? value : Number(value);
            const payload = item.payload as (typeof data)[number];
            return [`SHAP ${num.toFixed(4)} (expression ${payload.expression.toFixed(2)})`, payload.direction];
          }}
        />
        <Bar dataKey="value">
          {data.map((entry) => (
            <Cell key={entry.gene} fill={entry.value > 0 ? "var(--risk-high)" : "#2b6cb0"} />
          ))}
        </Bar>
      </BarChart>
      <p className="mt-2 text-xs text-foreground/50">
        Red bars push the prediction toward SLE; blue bars push toward Healthy.
      </p>
    </div>
  );
}
