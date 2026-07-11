"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { GraphExplorer } from "@/components/GraphExplorer";

export default function GraphPage() {
  const [mode, setMode] = useState<"POLICY" | "OBLIGATION">("POLICY");
  const { data, error, loading } = useApi(() => api.graph(mode), [mode]);

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Policy Graph Explorer</h1>
          <p className="mt-1 text-sm text-slate-500">
            {mode === "POLICY"
              ? "Whole-policy view — nodes are policies, edges are conflicts, redundancies, and shared topics."
              : "Obligation view — nodes are individual obligations linked by their conflict relationships."}
          </p>
        </div>
        <div className="flex rounded-lg border border-white/10 bg-ink-850 p-0.5">
          {(["POLICY", "OBLIGATION"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                mode === m ? "bg-accent/20 text-accent-soft" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {m === "POLICY" ? "Whole policy" : "Obligation level"}
            </button>
          ))}
        </div>
      </div>

      <Legend />

      {loading && <div className="text-sm text-slate-500">Loading graph…</div>}
      {error && <div className="text-sm text-severity-high">Failed to load graph: {error}</div>}
      {data && <GraphExplorer payload={data} />}
    </div>
  );
}

function Legend() {
  const items = [
    { c: "#f0476b", l: "Conflict" },
    { c: "#f5a524", l: "Redundant" },
    { c: "#3a466b", l: "Related (topic)" },
    { c: "#2dd4a7", l: "Healthy policy" },
  ];
  return (
    <div className="flex flex-wrap gap-4 text-xs text-slate-400">
      {items.map((i) => (
        <span key={i.l} className="flex items-center gap-1.5">
          <span className="h-2.5 w-4 rounded-full" style={{ background: i.c }} />
          {i.l}
        </span>
      ))}
    </div>
  );
}
