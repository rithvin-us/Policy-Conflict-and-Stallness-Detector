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
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set());

  async function sync(id: string) {
    setBusy(id);
    try {
      await api.syncConnector(id);
      connectors.reload();
    } finally {
      setBusy(null);
    }
  }

  async function registerHook(id: string) {
    setBusy(id);
    try {
      const res = await api.registerWebhook(id);
      connectors.reload();
      alert(`Webhook registered.\nPOST payloads to: ${res.url}\nEvents: push, pull_request`);
    } finally {
      setBusy(null);
    }
  }

  function handleEdit(id: string) {
    alert("Edit mode activated. (Mocked for demo)");
  }

  function handleDelete(id: string) {
    if (confirm("Are you sure you want to delete this connector?")) {
      setDeletedIds(prev => {
        const next = new Set(prev);
        next.add(id);
        return next;
      });
      alert("Connector deleted successfully. (Mocked for demo)");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-black">Sources & Webhooks</h1>
        <p className="mt-1 text-sm text-neutral-600 font-medium">
          Continuous sync from policy sources. GitHub and Local Folder are fully implemented; others are registered behind the same connector interface.
        </p>
      </div>

      <AddConnector onDone={() => connectors.reload()} />

      <Panel title="Connectors">
        <div className="grid gap-4 md:grid-cols-2">
          {(connectors.data?.items || [])
            .filter(c => !deletedIds.has(c.id))
            .map((c) => (
            <div key={c.id} className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition-all hover:border-neutral-300">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div>
                    <div className="text-sm font-bold text-black flex items-center gap-2">
                      {c.name}
                      {(c.error_message || c.status === "ERROR") && (
                        <div className="group relative inline-flex">
                          <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden w-max max-w-xs rounded bg-neutral-900 px-2 py-1 text-xs text-white group-hover:block z-10">
                            {c.error_message || "Configuration error detected."}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="mono text-[0.66rem] text-neutral-500 font-semibold uppercase mt-0.5">{c.type}</div>
                  </div>
                </div>
                <StatusPill status={c.status} />
              </div>
              
              <div className="mt-3 text-xs text-neutral-500 font-medium">
                {c.last_sync ? `Last sync ${new Date(c.last_sync).toLocaleString()}` : "Never synced"}
              </div>
              
              <div className="mt-4 flex items-center justify-between border-t border-neutral-100 pt-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(c.id)}
                    className="rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs text-neutral-600 font-bold transition hover:bg-neutral-100 hover:text-black"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="rounded-lg border border-red-100 bg-red-50 px-3 py-1.5 text-xs text-red-600 font-bold transition hover:bg-red-100 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
                
                <div className="flex gap-2">
                  {c.type === "GITHUB" && c.config?.repo && (
                    <a
                      href={`https://github.com/${c.config.repo}/tree/${c.config.branch || 'main'}/${c.config.path || ''}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs text-neutral-700 font-bold transition hover:bg-neutral-50 flex items-center gap-1.5 shadow-sm"
                    >
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.379.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" /></svg>
                      Browse Repo
                    </a>
                  )}
                  {c.type === "GITHUB" && (
                    <button
                      onClick={() => registerHook(c.id)}
                      disabled={busy === c.id}
                      className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs text-blue-700 font-bold transition hover:bg-blue-100 disabled:opacity-40"
                    >
                      Register hook
                    </button>
                  )}
                  <button
                    onClick={() => sync(c.id)}
                    disabled={busy === c.id || !IMPLEMENTED.has(c.type)}
                    className="rounded-lg bg-neutral-900 px-3 py-1.5 text-xs text-white font-bold transition hover:bg-neutral-800 disabled:opacity-40 shadow-sm"
                  >
                    {busy === c.id ? "Syncing…" : IMPLEMENTED.has(c.type) ? "Sync now" : "Not impl"}
                  </button>
                </div>
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
                <tr key={e.id} className="border-t border-neutral-200 hover:bg-neutral-50 transition-colors">
                  <td className="px-3 py-3 mono text-neutral-600 font-semibold">{e.source}</td>
                  <td className="px-3 py-3 text-black font-medium">{e.event_type}</td>
                  <td className="px-3 py-3"><StatusPill status={e.status} /></td>
                  <td className="px-3 py-3 text-xs text-neutral-500 font-medium">{e.detail}</td>
                  <td className="px-3 py-3 text-xs text-neutral-500 font-medium">{new Date(e.received_at).toLocaleString()}</td>
                </tr>
              ))}
              {events.data && events.data.items.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-neutral-500 font-medium">No webhook events yet.</td></tr>
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
      <div className="grid gap-4 md:grid-cols-4">
        <select value={type} onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm">
          {["GITHUB", "LOCAL_FOLDER", "GITLAB", "BITBUCKET", "GOOGLE_DRIVE", "SHAREPOINT", "SLACK", "TEAMS"].map((t) => (
            <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
          ))}
        </select>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Display name"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400" />
        {type === "GITHUB" ? (
          <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
            className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400" />
        ) : <div />}
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder={type === "GITHUB" ? "policies/ (path)" : "/abs/path"}
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400" />
      </div>
      {err && <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 font-bold">{err}</div>}
      <div className="mt-4 flex justify-end">
        <button onClick={submit} disabled={busy}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50">
          {busy ? "Connecting…" : "Add connector"}
        </button>
      </div>
    </Panel>
  );
}
