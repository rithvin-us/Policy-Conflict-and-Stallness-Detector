"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, StatusPill, SeverityChip, TypeTag } from "@/components/ui";
import type { AuditEvent, RepoStatus } from "@/lib/types";

// Continuous Policy Governance console: GitHub repository health, a live feed
// driven by Server-Sent Events, and the searchable immutable audit trail.
export default function GovernancePage() {
  const status = useApi(() => api.githubStatus(), []);
  const [query, setQuery] = useState("");
  const audit = useApi(() => api.audit(query ? `?search=${encodeURIComponent(query)}` : ""), [query]);
  const feed = useLiveFeed(() => {
    status.reload();
    audit.reload();
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Continuous Governance</h1>
        <p className="mt-1 text-sm text-slate-500">
          Live GitHub monitoring. Every policy change is verified, re-analyzed by the
          existing engine, and written to an immutable audit trail — no manual upload.
        </p>
      </div>

      <RepoHealth status={status.data} error={status.error} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AuditTrail
            rows={audit.data?.items || []}
            total={audit.data?.total || 0}
            query={query}
            onQuery={setQuery}
            onReview={async (id, patch) => {
              await api.reviewAudit(id, patch);
              audit.reload();
            }}
          />
        </div>
        <LiveFeed items={feed} />
      </div>
    </div>
  );
}

// ------------------------------- repo health -------------------------------

function RepoHealth({ status, error }: { status: any; error: string | null }) {
  if (error) {
    return <Panel title="Repository Health"><div className="text-sm text-severity-high">{error}</div></Panel>;
  }
  const repos: RepoStatus[] = status?.repositories || [];
  return (
    <Panel
      title="Repository Health"
      action={
        <span className="text-xs text-slate-500">
          Signature verification{" "}
          <span className={status?.signature_verification ? "text-severity-ok" : "text-severity-medium"}>
            {status?.signature_verification ? "ON" : "OFF (dev)"}
          </span>
        </span>
      }
    >
      {repos.length === 0 ? (
        <div className="text-sm text-slate-500">
          No GitHub connector configured. Add one on{" "}
          <a href="/connectors" className="text-accent-soft underline">Sources &amp; Webhooks</a>,
          then point a webhook at{" "}
          <code className="mono text-slate-300">{status?.webhook_url || "/api/v1/webhooks/github"}</code>.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {repos.map((r) => (
            <div key={r.connector_id} className="rounded-lg border border-white/5 bg-ink-850/50 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-slate-200">{r.repo || r.name}</div>
                  <div className="mono text-[0.66rem] text-slate-500">
                    {r.branch}{r.path ? ` · ${r.path}/` : ""}
                  </div>
                </div>
                <StatusPill status={r.status} />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <Stat label="Policies" value={String(r.policy_count)} />
                <Stat label="Webhook" value={r.webhook_configured ? "Configured" : "Not set"} />
                <Stat label="Last sync" value={r.last_sync ? new Date(r.last_sync).toLocaleString() : "Never"} />
                <Stat label="Events" value={(r.webhook_events || []).join(", ") || "—"} />
              </div>
              {r.latest_commit && (
                <div className="mt-3 rounded-md border border-white/5 bg-black/20 p-2 text-xs">
                  <div className="text-slate-400">Latest commit</div>
                  <a href={r.latest_commit.url} target="_blank" rel="noreferrer"
                     className="mono text-accent-soft">
                    {r.latest_commit.sha.slice(0, 7)}
                  </a>{" "}
                  <span className="text-slate-300">{r.latest_commit.message}</span>
                  <div className="text-slate-500">
                    {r.latest_commit.author}
                    {r.latest_commit.date ? ` · ${new Date(r.latest_commit.date).toLocaleString()}` : ""}
                  </div>
                </div>
              )}
              {r.error_message && <div className="mt-2 text-xs text-severity-high">{r.error_message}</div>}
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[0.62rem] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-slate-300">{value}</div>
    </div>
  );
}

// -------------------------------- live feed --------------------------------

type FeedItem = { type: string; data: any; at: string };

function useLiveFeed(onEvent: () => void): FeedItem[] {
  const [items, setItems] = useState<FeedItem[]>([]);
  const cb = useRef(onEvent);
  cb.current = onEvent;

  useEffect(() => {
    const es = new EventSource(api.eventStreamUrl());
    es.onmessage = (e) => {
      if (!e.data || e.data === "{}") return;
      try {
        const parsed = JSON.parse(e.data);
        setItems((prev) => [{ ...parsed, at: new Date().toISOString() }, ...prev].slice(0, 40));
        cb.current();
      } catch {
        /* keepalive / non-JSON frame */
      }
    };
    es.onerror = () => {/* browser auto-reconnects */};
    return () => es.close();
  }, []);

  return items;
}

const FEED_LABEL: Record<string, string> = {
  push_processed: "Push analyzed",
  pr_analyzed: "PR preview",
  webhook_processed: "Webhook",
  analysis_complete: "Re-analysis",
  audit_updated: "Review updated",
};

function LiveFeed({ items }: { items: FeedItem[] }) {
  return (
    <Panel
      title="Live Governance Feed"
      action={<span className="flex items-center gap-1.5 text-xs text-severity-ok">
        <span className="h-2 w-2 animate-pulse rounded-full bg-severity-ok" /> live
      </span>}
    >
      {items.length === 0 ? (
        <div className="text-sm text-slate-500">
          Waiting for events. Push a change to a monitored policy and it appears here in real time.
        </div>
      ) : (
        <ol className="space-y-2">
          {items.map((it, i) => (
            <li key={i} className="rounded-md border border-white/5 bg-ink-850/50 p-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-300">{FEED_LABEL[it.type] || it.type}</span>
                <span className="mono text-[0.6rem] text-slate-500">
                  {new Date(it.at).toLocaleTimeString()}
                </span>
              </div>
              <div className="mt-1 text-slate-500">{summarize(it)}</div>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  );
}

function summarize(it: FeedItem): string {
  const d = it.data || {};
  if (it.type === "push_processed") return `${d.changed_policies} policy file(s) on ${d.branch} @ ${(d.commit_sha || "").slice(0, 7)}`;
  if (it.type === "pr_analyzed") return `PR #${d.pr_number}: ${d.conflicts} conflict(s), review ${d.verdict}`;
  if (it.type === "analysis_complete") return `Governance ${d.overall} · ${d.counts?.conflicts ?? "?"} conflicts`;
  if (it.type === "webhook_processed") return d.detail || d.event_type;
  if (it.type === "audit_updated") return `${d.reviewer_status} / ${d.resolution_status}`;
  return JSON.stringify(d).slice(0, 80);
}

// ------------------------------- audit trail -------------------------------

function statusChip(value: string) {
  if (!value || value === "NONE") return null;
  return <SeverityChip severity={value} />;
}

function AuditTrail({
  rows, total, query, onQuery, onReview,
}: {
  rows: AuditEvent[];
  total: number;
  query: string;
  onQuery: (q: string) => void;
  onReview: (id: string, patch: Record<string, unknown>) => void;
}) {
  return (
    <Panel
      title="Audit Timeline"
      action={
        <input
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Search file, commit, author…"
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-1.5 text-xs text-slate-200 focus:border-accent focus:outline-none"
        />
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="table-head">
            <tr>
              <th className="px-3 py-2 text-left">When</th>
              <th className="px-3 py-2 text-left">Policy File</th>
              <th className="px-3 py-2 text-left">Change</th>
              <th className="px-3 py-2 text-left">Commit</th>
              <th className="px-3 py-2 text-left">Author</th>
              <th className="px-3 py-2 text-left">Findings</th>
              <th className="px-3 py-2 text-left">Risk</th>
              <th className="px-3 py-2 text-left">Review</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id} className="border-t border-white/5 align-top">
                <td className="px-3 py-2 text-xs text-slate-500">{new Date(a.created_at).toLocaleString()}</td>
                <td className="px-3 py-2">
                  <div className="mono text-xs text-slate-300">{a.policy_file}</div>
                  {a.repo && <div className="mono text-[0.6rem] text-slate-600">{a.repo}@{a.branch}</div>}
                </td>
                <td className="px-3 py-2"><TypeTag label={a.change_type} /></td>
                <td className="px-3 py-2 text-xs">
                  {a.commit_url ? (
                    <a href={a.commit_url} target="_blank" rel="noreferrer" className="mono text-accent-soft">
                      {(a.commit_sha || "").slice(0, 7)}
                    </a>
                  ) : (
                    <span className="mono text-slate-500">{(a.commit_sha || "").slice(0, 7) || "—"}</span>
                  )}
                  {a.pr_number ? <div className="text-[0.6rem] text-slate-500">PR #{a.pr_number}</div> : null}
                </td>
                <td className="px-3 py-2 text-xs text-slate-400">{a.author || "—"}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {statusChip(a.conflict_status)}
                    {a.duplicate_status !== "NONE" && <TypeTag label="dup" />}
                    {a.staleness_status !== "NONE" && <TypeTag label="stale" />}
                    {a.conflict_status === "NONE" &&
                      a.duplicate_status === "NONE" &&
                      a.staleness_status === "NONE" && (
                        <span className="text-xs text-severity-ok">clean</span>
                      )}
                  </div>
                  {a.compliance_impact.length > 0 && (
                    <div className="mt-1 mono text-[0.6rem] text-slate-500">
                      {a.compliance_impact.slice(0, 3).join(", ")}
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 mono text-xs text-slate-300">{a.risk_score.toFixed(2)}</td>
                <td className="px-3 py-2">
                  <select
                    value={a.reviewer_status}
                    onChange={(e) => onReview(a.id, { reviewer_status: e.target.value })}
                    className="rounded border border-white/10 bg-ink-850 px-1.5 py-1 text-[0.65rem] text-slate-300"
                  >
                    {["PENDING", "ACKNOWLEDGED", "REVIEWED", "DISMISSED"].map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="py-6 text-center text-slate-600">
                  No audit events yet. Changes pushed to a monitored repo appear here.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-right text-[0.65rem] text-slate-600">{total} record(s)</div>
    </Panel>
  );
}
