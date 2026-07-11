"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, SeverityChip, TypeTag } from "@/components/ui";

export default function ConflictsPage() {
  const [sev, setSev] = useState<string>("");
  const [type, setType] = useState<string>("");
  const conflicts = useApi(() => api.conflicts(), []);
  const redundancies = useApi(() => api.redundancies(), []);

  const rows = useMemo(() => {
    const items = [
      ...(conflicts.data?.items || []),
      ...(redundancies.data?.items || []),
    ];
    return items
      .filter((c) => (sev ? c.severity === sev : true))
      .filter((c) => (type ? c.conflict_type === type : true))
      .sort((a, b) => b.risk - a.risk);
  }, [conflicts.data, redundancies.data, sev, type]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Conflicts & Redundancies</h1>
          <p className="mt-1 text-sm text-slate-500">
            Every finding cites the exact triggering text and a resolution. Click a row to compare side by side.
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={sev} onChange={setSev} label="Severity" options={["HIGH", "MEDIUM", "LOW"]} />
          <Select
            value={type}
            onChange={setType}
            label="Type"
            options={["DIRECT", "TEMPORAL", "SCOPE", "STRENGTH", "PARAMETER", "REDUNDANCY", "PARTIAL_REDUNDANCY"]}
          />
        </div>
      </div>

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-head">
              <tr>
                <th className="px-3 py-2 text-left">Severity</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-left">Policies</th>
                <th className="px-3 py-2 text-left">Explanation</th>
                <th className="px-3 py-2 text-right">Conf.</th>
                <th className="px-3 py-2 text-right">Risk</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} className="group border-t border-white/5 hover:bg-white/[0.03]">
                  <td className="px-3 py-3"><SeverityChip severity={c.severity} /></td>
                  <td className="px-3 py-3"><TypeTag label={c.conflict_type} /></td>
                  <td className="px-3 py-3">
                    <span className="mono text-slate-400">{c.policy_a_id}</span>
                    <span className="px-1 text-slate-600">↔</span>
                    <span className="mono text-slate-400">{c.policy_b_id}</span>
                  </td>
                  <td className="max-w-md px-3 py-3">
                    <Link href={`/conflicts/${c.id}`} className="block truncate text-slate-300 group-hover:text-accent-soft">
                      {c.explanation}
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-right mono text-slate-400">{Math.round(c.confidence * 100)}%</td>
                  <td className="px-3 py-3 text-right mono font-semibold text-slate-200">{Math.round(c.risk)}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr><td colSpan={6} className="py-8 text-center text-slate-600">No findings match the filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function Select({
  value,
  onChange,
  label,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  label: string;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-white/10 bg-ink-850 px-3 py-1.5 text-xs text-slate-300 focus:border-accent focus:outline-none"
    >
      <option value="">All {label}</option>
      {options.map((o) => (
        <option key={o} value={o}>{o.replace(/_/g, " ")}</option>
      ))}
    </select>
  );
}
