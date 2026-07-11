"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, StatusPill } from "@/components/ui";

const IMPLEMENTED = new Set(["LOCAL_FOLDER", "GITHUB", "UPLOAD"]);

export default function ConnectorsPage() {
  const connectors = useApi(() => api.connectors(), []);
  const events = useApi(() => api.webhookEvents(), []);
  const [busy, setBusy] = useState<string | null>(null);

  async function sync(id: string) {
    setBusy(id);
    try {
      await api.syncConnector(id);
      connectors.reload();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Sources & Webhooks</h1>
        <p className="mt-1 text-sm text-slate-500">
          Continuous sync from policy sources. GitHub and Local Folder are fully implemented; others are registered behind the same connector interface.
        </p>
      </div>

      <AddConnector onDone={() => connectors.reload()} />

      <Panel title="Connectors">
        <div className="grid gap-3 md:grid-cols-2">
          {(connectors.data?.items || []).map((c) => (
            <div key={c.id} className="rounded-lg border border-white/5 bg-ink-850/50 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-slate-200">{c.name}</div>
                  <div className="mono text-[0.66rem] text-slate-500">{c.type}</div>
                </div>
                <StatusPill status={c.status} />
              </div>
              <div className="mt-2 text-xs text-slate-500">
                {c.last_sync ? `Last sync ${new Date(c.last_sync).toLocaleString()}` : "Never synced"}
              </div>
              {c.error_message && <div className="mt-1 text-xs text-severity-high">{c.error_message}</div>}
              <div className="mt-3 flex justify-end">
                <button
                  onClick={() => sync(c.id)}
                  disabled={busy === c.id || !IMPLEMENTED.has(c.type)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/10 disabled:opacity-40"
                >
                  {busy === c.id ? "Syncing…" : IMPLEMENTED.has(c.type) ? "Sync now" : "Not implemented"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Webhook Events">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-head">
              <tr>
                <th className="px-3 py-2 text-left">Source</th>
                <th className="px-3 py-2 text-left">Event</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Detail</th>
                <th className="px-3 py-2 text-left">Received</th>
              </tr>
            </thead>
            <tbody>
              {(events.data?.items || []).map((e) => (
                <tr key={e.id} className="border-t border-white/5">
                  <td className="px-3 py-2 mono text-slate-400">{e.source}</td>
                  <td className="px-3 py-2 text-slate-300">{e.event_type}</td>
                  <td className="px-3 py-2"><StatusPill status={e.status} /></td>
                  <td className="px-3 py-2 text-xs text-slate-500">{e.detail}</td>
                  <td className="px-3 py-2 text-xs text-slate-500">{new Date(e.received_at).toLocaleString()}</td>
                </tr>
              ))}
              {events.data && events.data.items.length === 0 && (
                <tr><td colSpan={5} className="py-6 text-center text-slate-600">No webhook events yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function AddConnector({ onDone }: { onDone: () => void }) {
  const [type, setType] = useState("GITHUB");
  const [name, setName] = useState("");
  const [repo, setRepo] = useState("");
  const [path, setPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      const config =
        type === "GITHUB"
          ? { repo, branch: "main", path }
          : type === "LOCAL_FOLDER"
          ? { path }
          : {};
      await api.createConnector({ type, name: name || type, config });
      setName(""); setRepo(""); setPath("");
      onDone();
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title="Add a source">
      <div className="grid gap-3 md:grid-cols-4">
        <select value={type} onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none">
          {["GITHUB", "LOCAL_FOLDER", "GITLAB", "BITBUCKET", "GOOGLE_DRIVE", "SHAREPOINT", "SLACK", "TEAMS"].map((t) => (
            <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
          ))}
        </select>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Display name"
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
        {type === "GITHUB" ? (
          <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
            className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
        ) : <div />}
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder={type === "GITHUB" ? "policies/ (path)" : "/abs/path"}
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
      </div>
      {err && <div className="mt-2 text-sm text-severity-high">{err}</div>}
      <div className="mt-3 flex justify-end">
        <button onClick={submit} disabled={busy}
          className="rounded-lg bg-accent/20 px-4 py-2 text-sm text-accent-soft transition hover:bg-accent/30 disabled:opacity-40">
          {busy ? "Connecting…" : "Add connector"}
        </button>
      </div>
    </Panel>
  );
}
