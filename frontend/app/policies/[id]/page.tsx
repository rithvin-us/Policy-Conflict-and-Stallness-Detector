"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, SeverityChip, TypeTag, scoreColor } from "@/components/ui";

export default function PolicyDetailPage({ params }: { params: { id: string } }) {
  const { data, error, loading } = useApi(() => api.policy(params.id), [params.id]);

  if (loading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (error || !data) return <div className="text-sm text-severity-high">Failed to load policy.</div>;

  return (
    <div className="space-y-6">
      <Link href="/policies" className="text-sm text-accent hover:underline">← Policy library</Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">{data.title}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
            <span className="mono">{data.id}</span>
            <span>·</span><span>{data.owner}</span>
            <span>·</span><span>v{data.version}</span>
            <span>·</span><span>reviewed {data.last_reviewed?.slice(0, 10) || "—"}</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {data.tags?.map((t) => <TypeTag key={t} label={t} />)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-semibold" style={{ color: scoreColor(data.health_score) }}>
            {data.health_score}
          </div>
          <div className="stat-label">health</div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <Panel className="col-span-12 lg:col-span-7" title={`Obligations (${data.obligations?.length || 0})`}>
          <div className="space-y-2">
            {(data.obligations || []).map((o: any) => (
              <div key={o.id} className="rounded-lg border border-white/5 bg-ink-850/50 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <span className="chip bg-white/5 text-slate-300 ring-1 ring-white/10">{o.topic}</span>
                  <span className="mono text-xs text-accent-soft">
                    {o.polarity === "NEGATE" ? "¬" : ""}{o.action}
                  </span>
                  <span className="mono text-[0.66rem] text-slate-500">{o.strength}</span>
                  {o.section && <span className="kbd ml-auto">§{o.section}</span>}
                </div>
                <p className="text-sm text-slate-300">{o.evidence_text}</p>
                {Object.keys(o.parameters || {}).length > 0 && (
                  <div className="mono mt-1 text-[0.66rem] text-slate-600">
                    {JSON.stringify(o.parameters)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>

        <div className="col-span-12 space-y-6 lg:col-span-5">
          <Panel title={`Conflicts (${data.conflicts?.length || 0})`}>
            <div className="space-y-2">
              {(data.conflicts || []).map((c) => (
                <Link key={c.id} href={`/conflicts/${c.id}`}
                  className="flex items-center gap-2 rounded-lg border border-white/5 bg-ink-850/50 p-2.5 hover:bg-white/[0.03]">
                  <SeverityChip severity={c.severity} />
                  <TypeTag label={c.conflict_type} />
                  <span className="truncate text-xs text-slate-400">{c.explanation}</span>
                </Link>
              ))}
              {(!data.conflicts || data.conflicts.length === 0) && (
                <div className="py-4 text-center text-sm text-slate-600">No conflicts</div>
              )}
            </div>
          </Panel>

          <Panel title={`Staleness (${data.staleness?.length || 0})`}>
            <div className="space-y-2">
              {(data.staleness || []).map((s) => (
                <div key={s.id} className="rounded-lg border border-white/5 bg-ink-850/50 p-2.5">
                  <div className="mb-1 flex items-center gap-2">
                    <SeverityChip severity={s.severity} />
                    <TypeTag label={s.stale_reason} />
                  </div>
                  <div className="text-xs text-slate-400">{s.evidence?.join("; ")}</div>
                  <div className="mt-1 text-xs text-severity-medium">{s.recommendation}</div>
                </div>
              ))}
              {(!data.staleness || data.staleness.length === 0) && (
                <div className="py-4 text-center text-sm text-slate-600">Fresh</div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
