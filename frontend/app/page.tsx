"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { GovernanceGauge } from "@/components/GovernanceGauge";
import { SeverityBars, GovernanceHistoryChart } from "@/components/charts";
import { Panel, SeverityChip, scoreColor } from "@/components/ui";

import { 
  FileText, 
  AlertTriangle, 
  Copy, 
  Clock, 
  Network, 
  ShieldCheck 
} from "lucide-react";

export default function OverviewPage() {
  const ov = useApi(() => api.overview(), []);
  const queue = useApi(() => api.reviewQueue(), []);
  const tl = useApi(() => api.timeline(12), []);
  const conflicts = useApi(() => api.conflicts(), []);
  const hist = useApi(() => api.history(), []);

  const g = ov.data;
  const c = g?.counts;

  const sevData = (() => {
    const items = conflicts.data?.items || [];
    return ["HIGH", "MEDIUM", "LOW"].map((s) => ({
      name: s,
      sev: s,
      value: items.filter((x) => x.severity === s).length,
    }));
  })();

  return (
    <div className="space-y-6">
      <PageHead
        title="Governance Overview"
        subtitle="Corpus-wide policy health, live conflicts, and remediation priorities."
      />

      <div className="grid grid-cols-12 gap-6">
        {/* Governance score + subscores */}
        <Panel className="col-span-12 lg:col-span-4" title="Governance Score">
          <div className="flex items-center gap-6">
            <GovernanceGauge score={g?.overall ?? 0} />
            <div className="flex-1 space-y-3">
              <SubScore label="Policy health" value={g?.policy_health ?? 0} good />
              <SubScore label="Conflict pressure" value={g?.conflict_pressure ?? 0} />
              <SubScore label="Staleness index" value={g?.staleness_index ?? 0} />
              <SubScore label="Topic coverage" value={g?.coverage ?? 0} good />
            </div>
          </div>
          <div className="mt-4 border-t border-ink-800 pt-3">
            <div className="stat-label mb-1">30-day Trend</div>
            {hist.data?.length ? <GovernanceHistoryChart data={hist.data} /> : <Empty />}
          </div>
        </Panel>

        {/* KPI tiles */}
        <div className="col-span-12 grid grid-cols-2 gap-4 lg:col-span-5 lg:grid-cols-2">
          <Kpi label="Policies" value={c?.policies} href="/policies" icon={FileText} />
          <Kpi label="Conflicts" value={c?.conflicts} href="/conflicts" icon={AlertTriangle} tone="high" />
          <Kpi label="Redundancies" value={c?.redundancies} href="/conflicts" icon={Copy} tone="medium" />
          <Kpi label="Stale policies" value={c?.stale} href="/staleness" icon={Clock} tone="medium" />
          <Kpi label="Obligations" value={c?.obligations} href="/graph" icon={Network} />
          <Kpi label="Coverage" value={g ? `${g.coverage}%` : undefined} href="/compliance" icon={ShieldCheck} tone="ok" />
        </div>

        {/* Severity distribution */}
        <Panel className="col-span-12 lg:col-span-3" title="Conflict Severity">
          {conflicts.data ? <SeverityBars data={sevData} /> : <Empty />}
        </Panel>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Review queue */}
        <Panel
          className="col-span-12 lg:col-span-7"
          title="Priority Review Queue"
          action={<Link href="/conflicts" className="text-xs text-accent hover:underline font-semibold">open all →</Link>}
        >
          <div className="space-y-2">
            {(queue.data?.items || []).slice(0, 6).map((item, i) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-950 px-3 py-2.5 shadow-sm"
              >
                <div className="w-10 text-center">
                  <div className="text-sm font-bold" style={{ color: scoreColor(100 - item.risk) }}>
                    {Math.round(item.risk)}
                  </div>
                  <div className="stat-label">risk</div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-black">{item.title}</div>
                  <div className="truncate text-xs text-black">{item.summary}</div>
                </div>
                <SeverityChip severity={item.severity} />
                <span className="chip bg-ink-900 text-black ring-1 ring-ink-800">{item.kind}</span>
              </motion.div>
            ))}
            {queue.data && queue.data.items.length === 0 && <Empty label="No open findings" />}
          </div>
        </Panel>

        {/* Timeline */}
        <Panel className="col-span-12 lg:col-span-5" title="Activity Timeline">
          <ol className="relative space-y-4 border-l border-ink-800 pl-4">
            {(tl.data?.items || []).map((e) => (
              <li key={e.id} className="relative">
                <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-accent/70 ring-2 ring-ink-900" />
                <div className="text-sm font-medium text-black">{e.title}</div>
                {e.detail && <div className="text-xs text-black">{e.detail}</div>}
                <div className="mono mt-0.5 text-[0.68rem] text-black">
                  {e.kind} · {e.at ? new Date(e.at).toLocaleString() : ""}
                </div>
              </li>
            ))}
            {tl.data && tl.data.items.length === 0 && <Empty />}
          </ol>
        </Panel>
      </div>

      {(ov.error || conflicts.error) && (
        <div className="rounded-lg border border-severity-high/30 bg-severity-high/10 p-3 text-sm font-medium text-severity-high">
          Backend unreachable — start the API on :8000. ({ov.error || conflicts.error})
        </div>
      )}
    </div>
  );
}

function PageHead({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h1 className="text-2xl font-bold font-heading text-black tracking-tight">{title}</h1>
      <p className="mt-1 text-sm text-black font-medium">{subtitle}</p>
    </div>
  );
}

function SubScore({ label, value, good }: { label: string; value: number; good?: boolean }) {
  const color = good ? scoreColor(value) : scoreColor(100 - value);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs font-medium">
        <span className="text-black">{label}</span>
        <span className="mono font-semibold" style={{ color }}>{value}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-ink-800">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8 }}
        />
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  href,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value?: number | string;
  href: string;
  icon: React.ElementType;
  tone?: "default" | "high" | "medium" | "ok";
}) {
  const toneColor = {
    default: "#3b82f6", // accent.soft
    high: "#e11d48",
    medium: "#d97706",
    ok: "#059669",
  }[tone];
  return (
    <Link href={href} className="panel panel-pad group transition hover:shadow-glow bg-ink-950">
      <div className="flex items-start justify-between">
        <span className="stat-label">{label}</span>
        <Icon size={20} style={{ color: toneColor }} className="opacity-80" />
      </div>
      <div className="mt-3 text-3xl font-bold font-heading tracking-tight text-black">
        {value ?? <span className="text-black">—</span>}
      </div>
    </Link>
  );
}

function Empty({ label = "No data" }: { label?: string }) {
  return <div className="py-6 text-center text-sm font-medium text-black">{label}</div>;
}
