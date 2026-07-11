"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, SeverityChip, TypeTag } from "@/components/ui";

export default function StalenessPage() {
  const { data } = useApi(() => api.staleness(), []);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Staleness Surveillance</h1>
        <p className="mt-1 text-sm text-slate-500">
          Review-overdue policies, deprecated technology references, superseded standards, and orphaned owners.
        </p>
      </div>
      <div className="grid gap-3">
        {(data?.items || []).map((s) => (
          <Panel key={s.id} className="panel-pad">
            <div className="flex items-start gap-4">
              <div className="flex flex-col items-center gap-1">
                <SeverityChip severity={s.severity} />
                {s.age_months != null && (
                  <span className="mono text-[0.66rem] text-slate-500">{s.age_months}mo</span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <TypeTag label={s.stale_reason} />
                  <Link href={`/policies/${s.policy_id}`} className="mono text-xs text-accent-soft hover:underline">
                    {s.policy_id}
                  </Link>
                </div>
                <div className="text-sm text-slate-300">{s.evidence?.join("; ")}</div>
                <div className="mt-1 text-sm text-severity-medium">→ {s.recommendation}</div>
              </div>
              <div className="text-right">
                <div className="mono text-lg font-semibold text-slate-200">{Math.round(s.risk)}</div>
                <div className="stat-label">risk</div>
              </div>
            </div>
          </Panel>
        ))}
        {data && data.items.length === 0 && (
          <div className="py-10 text-center text-slate-600">All policies are fresh.</div>
        )}
      </div>
    </div>
  );
}
