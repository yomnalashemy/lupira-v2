"use client";

import Papa from "papaparse";
import { useRef, useState } from "react";
import type { GeneRow } from "@/lib/types";

interface Props {
  requiredGenes: string[];
  onParsed: (expression: Record<string, number>) => void;
}

const MIN_COVERAGE = 0.8;

export default function GeneUploader({ requiredGenes, onParsed }: Props) {
  const [rows, setRows] = useState<GeneRow[]>([]);
  const [missing, setMissing] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File) {
    setError(null);
    Papa.parse<string[]>(file, {
      skipEmptyLines: true,
      complete: (result) => {
        const parsed: GeneRow[] = [];
        for (const row of result.data) {
          if (row.length < 2) continue;
          const gene = row[0]?.trim();
          const value = parseFloat(row[1]);
          if (!gene || Number.isNaN(value)) continue;
          parsed.push({ gene, value });
        }
        if (parsed.length === 0) {
          setError(
            "We couldn't read any valid rows from this file. It should have a gene name in the first " +
            "column and an expression value in the second — check with your lab if you're unsure of the format.",
          );
          return;
        }

        const foundGenes = new Set(parsed.map((r) => r.gene));
        const missingGenes = requiredGenes.filter((g) => !foundGenes.has(g));
        const coverage = (requiredGenes.length - missingGenes.length) / requiredGenes.length;

        setRows(parsed);
        setMissing(missingGenes);

        if (coverage < MIN_COVERAGE) {
          setError(
            `This file only covers ${requiredGenes.length - missingGenes.length} of the ${requiredGenes.length} ` +
            `genes we need (at least ${Math.round(MIN_COVERAGE * 100)}% required). Missing: ${missingGenes.join(", ")}`,
          );
          return;
        }

        const expression: Record<string, number> = {};
        for (const r of parsed) expression[r.gene] = r.value;
        onParsed(expression);
      },
      error: (err) => setError(err.message),
    });
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded border-2 border-dashed p-10 text-center transition-colors ${
          dragOver ? "border-primary bg-primary/5" : "border-border"
        }`}
      >
        <p className="text-sm text-foreground/70">
          Drag and drop your results file here, or click to browse.
        </p>
        <p className="mt-1 text-xs text-foreground/50">
          Works with the file as exported by your lab — gene names in one column, values in the next.
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.tsv,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </div>

      {error && (
        <p className="mt-3 rounded border border-risk-high/40 bg-risk-high/10 px-3 py-2 text-sm text-risk-high">
          {error}
        </p>
      )}

      {rows.length > 0 && !error && (
        <div className="mt-4">
          <p className="text-sm text-risk-healthy">
            Good — this file covers {requiredGenes.length - missing.length} of the {requiredGenes.length} genes we need.
          </p>
          <p className="mt-2 text-xs text-foreground/50">Preview (first 10 rows):</p>
          <table className="mt-1 w-full text-xs">
            <tbody>
              {rows.slice(0, 10).map((r) => (
                <tr key={r.gene} className="border-b border-border">
                  <td className="py-1 pr-4 font-mono">{r.gene}</td>
                  <td className="py-1 font-mono">{r.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
