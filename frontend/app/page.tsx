"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useEventStream } from "@/lib/useEventStream";
import { useCallback, useState, useEffect } from "react";
import { GovernanceGauge } from "@/components/GovernanceGauge";
import { SeverityBars, GovernanceHistoryChart } from "@/components/charts";
import { Panel, SeverityChip, scoreColor } from "@/components/ui";

import {
  FileText,
  AlertTriangle,
  Copy,
  Clock,
  Network,
  ShieldCheck,
  GitBranch,
  FolderGit2,
  ArrowRight,
  Loader2,
} from "lucide-react";

export default function OverviewPage() {
  const ov = useApi(() => api.overview(), []);
  const connectors = useApi(() => api.connectors(), []);
  const queue = useApi(() => api.reviewQueue(), []);
  const tl = useApi(() => api.timeline(12), []);
  const conflicts = useApi(() => api.conflicts(), []);
  const hist = useApi(() => api.history(), []);

  // Show a tiny status ticker when an event comes in
  const [liveStatus, setLiveStatus] = useState<string | null>(null);

  useEventStream(
    useCallback(
      (type, data) => {
        if (type === "push_processed") {
          setLiveStatus(`Live update: push processed for ${data.repo}`);
        } else if (type === "pr_analyzed") {
          setLiveStatus(`Live update: PR #${data.pr_number} analyzed on ${data.repo}`);
        } else {
          setLiveStatus(`Live update: ${type}`);
        }
        
        // Auto-refresh the dashboard
        ov.reload();
        connectors.reload();
        queue.reload();
        tl.reload();
        conflicts.reload();
        hist.reload();

        setTimeout(() => setLiveStatus(null), 5000);
      },
      [ov, connectors, queue, tl, conflicts, hist]
    )
  );

  const g = ov.data;
  const c = g?.counts;

  // Gate the console: until a source is integrated and at least one policy is
  // under governance, the dashboard shows nothing but an onboarding call to
  // action. No sample data, no zeroed tiles — it waits for a real corpus.
  const policyCount = c?.policies ?? 0;
  const hasConnector = (connectors.data?.items?.length ?? 0) > 0;

  if (ov.loading && !ov.data) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-black">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
        <p className="text-sm font-medium">Connecting to governance engine…</p>
      </div>
    );
  }

  if (ov.data && policyCount === 0) {
    return <Onboarding hasConnector={hasConnector} syncing={connectors.loading} />;
  }

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
      {liveStatus && (
        <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-2 text-sm font-medium text-accent animate-fade-in shadow-sm flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
          </span>
          {liveStatus}
        </div>
      )}

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

function Onboarding({ hasConnector, syncing }: { hasConnector: boolean; syncing: boolean }) {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-2xl text-center"
      >
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-accent/20 bg-accent/10 text-accent shadow-sm">
          <ShieldCheck className="h-8 w-8" />
        </div>

        <h1 className="font-heading text-2xl font-bold tracking-tight text-black">
          {hasConnector ? "No policies under governance yet" : "Connect a source to begin"}
        </h1>
        <p className="mx-auto mt-2 max-w-lg text-sm font-medium leading-relaxed text-black/70">
          Sentinal analyzes only what you integrate. Connect a GitHub repository or a
          local folder and it will ingest your policies, extract obligations, and surface
          conflicts, redundancies, and staleness automatically — nothing is shown until then.
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <OnboardCard
            href="/connectors"
            icon={GitBranch}
            title="GitHub repository"
            desc="Continuous, webhook-driven governance on every push."
          />
          <OnboardCard
            href="/connectors"
            icon={FolderGit2}
            title="Local folder"
            desc="Point at a directory of policy files to analyze now."
          />
        </div>

        {hasConnector && (
          <div className="mt-6 rounded-xl border border-accent/30 bg-accent/5 px-4 py-3 text-sm font-medium text-black">
            {syncing
              ? "A source is connected — checking for policies…"
              : "A source is connected but hasn’t synced any policies yet."}{" "}
            <Link href="/connectors" className="font-semibold text-accent hover:underline">
              Open Sources to sync →
            </Link>
          </div>
        )}

        <p className="mt-8 text-xs font-medium text-black/40">
          Deterministic engine · findings are reproducible and cite exact source text.
        </p>
      </motion.div>
    </div>
  );
}

function OnboardCard({
  href,
  icon: Icon,
  title,
  desc,
}: {
  href: string;
  icon: React.ElementType;
  title: string;
  desc: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col items-start gap-2 rounded-2xl border border-ink-800 bg-white p-5 text-left shadow-sm transition hover:border-accent/40 hover:shadow-md"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-ink-850 text-black transition group-hover:bg-accent/10 group-hover:text-accent">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-sm font-semibold text-black">{title}</div>
      <div className="text-xs font-medium leading-snug text-black/60">{desc}</div>
      <span className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-accent opacity-0 transition group-hover:opacity-100">
        Connect <ArrowRight className="h-3.5 w-3.5" />
      </span>
    </Link>
  );
}
