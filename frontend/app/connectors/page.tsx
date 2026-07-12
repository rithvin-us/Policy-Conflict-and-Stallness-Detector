"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useEventStream } from "@/lib/useEventStream";
import { Panel, StatusPill } from "@/components/ui";

const IMPLEMENTED = new Set(["LOCAL_FOLDER", "GITHUB", "UPLOAD"]);

export default function ConnectorsPage() {
  const connectors = useApi(() => api.connectors(), []);
  const events = useApi(() => api.webhookEvents(), []);
  const [busy, setBusy] = useState<string | null>(null);
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set());

  useEventStream(
    useCallback((type) => {
      // Refresh the connectors and events tables whenever a background event occurs
      connectors.reload();
      events.reload();
    }, [connectors, events])
  );

  const totalConnectors = connectors.data?.items.length || 0;
  const healthyConnectors = connectors.data?.items.filter(c => c.status === "CONNECTED").length || 0;
  const healthPercent = totalConnectors > 0 ? Math.round((healthyConnectors / totalConnectors) * 100) : 100;
  
  const totalEvents = events.data?.items.length || 0;
  const processedEvents = events.data?.items.filter(e => e.status === "PROCESSED").length || 0;
  const webhookPercent = totalEvents > 0 ? Math.round((processedEvents / totalEvents) * 100) : 100;

  async function sync(id: string) {
    setBusy(id);
    try {
      await api.syncConnector(id);
      connectors.reload();
    } finally {
      setBusy(null);
    }
  }

  async function registerHook(c: any) {
    const token = prompt(
      "Enter a GitHub Personal Access Token (with repo_hook scope) to automatically set up the webhook on GitHub.\n\nLeave blank if you prefer to set it up manually."
    );
    if (token === null) return; // user cancelled the prompt

    setBusy(c.id);
    try {
      const res = await api.registerWebhook(c.id, ["push", "pull_request"], token || undefined);
      connectors.reload();
      if (token) {
        alert("Webhook successfully configured on GitHub!");
      } else {
        alert(`Webhook registered locally.\nPOST payloads to: ${res.url}\nEvents: push, pull_request`);
      }
    } catch (err: any) {
      alert("Failed to register webhook: " + err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleEdit(c: any) {
    if (c.type !== "GITHUB") {
      alert("Only GITHUB connectors can be edited in this demo.");
      return;
    }
    const newPath = prompt("Edit repository path (e.g. 'policies/'):", (c.config?.path as string) || "");
    if (newPath !== null) {
      setBusy(c.id);
      try {
        await api.updateConnector(c.id, { config: { ...c.config, path: newPath } });
        connectors.reload();
      } catch (err: any) {
        alert("Failed to edit: " + err.message);
      } finally {
        setBusy(null);
      }
    }
  }

  async function handleDelete(id: string) {
    if (confirm("Are you sure you want to delete this connector? This action cannot be undone.")) {
      setBusy(id);
      try {
        await api.deleteConnector(id);
        connectors.reload();
      } catch (err: any) {
        alert("Failed to delete: " + err.message);
      } finally {
        setBusy(null);
      }
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-black">Sources & Webhooks</h1>
        <p className="mt-1 text-sm text-black font-medium">
          Continuous sync from policy sources. GitHub and Local Folder are fully implemented; others are registered behind the same connector interface.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm flex flex-col items-center justify-center">
          <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-1">Repo Health</div>
          <div className={`text-2xl font-black ${healthPercent === 100 ? "text-green-600" : "text-amber-600"}`}>{healthPercent}%</div>
          <div className="text-[10px] font-semibold text-black mt-1">{healthyConnectors} / {totalConnectors} healthy</div>
        </div>
        <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm flex flex-col items-center justify-center">
          <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-1">Webhook Health</div>
          <div className={`text-2xl font-black ${webhookPercent === 100 ? "text-green-600" : "text-amber-600"}`}>{webhookPercent}%</div>
          <div className="text-[10px] font-semibold text-black mt-1">{processedEvents} / {totalEvents} processed</div>
        </div>
        <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm flex flex-col items-center justify-center">
          <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-1">Total Sources</div>
          <div className="text-2xl font-black text-black">{totalConnectors}</div>
        </div>
        <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm flex flex-col items-center justify-center">
          <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mb-1">Total Events</div>
          <div className="text-2xl font-black text-black">{totalEvents}</div>
        </div>
      </div>

      <GitHubOnboarding onDone={() => connectors.reload()} />

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
                    <div className="mono text-[0.66rem] text-black font-semibold uppercase mt-0.5">{c.type}</div>
                  </div>
                </div>
                <StatusPill status={c.status} />
              </div>
              
              <div className="mt-3 text-xs text-black font-medium">
                {c.last_sync ? `Last sync ${new Date(c.last_sync).toLocaleString()}` : "Never synced"}
              </div>
              
              <div className="mt-4 flex items-center justify-between border-t border-neutral-100 pt-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(c)}
                    className="rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs text-black font-bold transition hover:bg-neutral-100 hover:text-black"
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
                  {c.type === "GITHUB" && typeof c.config?.repo === "string" && (
                    <a
                      href={`https://github.com/${c.config.repo as string}/tree/${(c.config.branch as string) || 'main'}/${(c.config.path as string) || ''}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs text-black font-bold transition hover:bg-neutral-50 flex items-center gap-1.5 shadow-sm"
                    >
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.379.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" /></svg>
                      Browse Repo
                    </a>
                  )}
                  {c.type === "GITHUB" && (
                    <button
                      onClick={() => registerHook(c)}
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
                  <td className="px-3 py-3 mono text-black font-semibold">{e.source}</td>
                  <td className="px-3 py-3 text-black font-medium">{e.event_type}</td>
                  <td className="px-3 py-3"><StatusPill status={e.status} /></td>
                  <td className="px-3 py-3 text-xs text-black font-medium">{e.detail}</td>
                  <td className="px-3 py-3 text-xs text-black font-medium">{new Date(e.received_at).toLocaleString()}</td>
                </tr>
              ))}
              {events.data && events.data.items.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-black font-medium">No webhook events yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

import { RepoPicker } from "@/components/github/RepoPicker";

function GitHubOnboarding({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState<"SELECT_TYPE" | "GITHUB_AUTH" | "GITHUB_PICKER" | "LEGACY">("SELECT_TYPE");
  const [token, setToken] = useState("");
  const [type, setType] = useState("GITHUB");

  if (step === "SELECT_TYPE") {
    return (
      <Panel title="Connect a new source">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="w-full sm:w-1/3">
            <label className="block text-xs font-bold text-black uppercase mb-1">Source Type</label>
            <select 
              value={type} 
              onChange={(e) => setType(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm"
            >
              {["GITHUB", "LOCAL_FOLDER", "GITLAB", "BITBUCKET", "GOOGLE_DRIVE", "SHAREPOINT"].map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <button 
            onClick={() => setStep(type === "GITHUB" ? "GITHUB_AUTH" : "LEGACY")}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700"
          >
            Continue
          </button>
        </div>
      </Panel>
    );
  }

  if (step === "GITHUB_AUTH") {
    return (
      <Panel title="Connect GitHub">
        <div className="max-w-xl">
          <p className="text-sm text-black font-medium mb-4">
            Provide a GitHub Personal Access Token (PAT) with <code className="bg-neutral-100 px-1 rounded">repo</code> scope. We will securely fetch your organizations and repositories so you can configure them with zero manual typing.
          </p>
          <input 
            type="password"
            value={token} 
            onChange={e => setToken(e.target.value)}
            placeholder="ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm font-mono text-black focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400 mb-4"
          />
          <div className="flex gap-3">
            <button 
              onClick={() => setStep("SELECT_TYPE")}
              className="rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm font-bold text-black transition hover:bg-neutral-50"
            >
              Back
            </button>
            <button 
              onClick={() => { if (token.length > 10) setStep("GITHUB_PICKER"); }}
              disabled={token.length < 10}
              className="rounded-lg bg-black px-6 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-neutral-800 disabled:opacity-50"
            >
              Authenticate
            </button>
          </div>
        </div>
      </Panel>
    );
  }

  if (step === "GITHUB_PICKER") {
    return (
      <RepoPicker 
        token={token} 
        onSuccess={() => { setStep("SELECT_TYPE"); setToken(""); onDone(); }}
        onCancel={() => setStep("SELECT_TYPE")}
      />
    );
  }

  return <LegacyConnector type={type} onDone={() => { setStep("SELECT_TYPE"); onDone(); }} onCancel={() => setStep("SELECT_TYPE")} />;
}


function LegacyConnector({ type, onDone, onCancel }: { type: string, onDone: () => void, onCancel: () => void }) {
  const [name, setName] = useState("");
  const [repo, setRepo] = useState("");
  const [path, setPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      let parsedRepo = repo;
      if (type === "GITHUB" && repo.includes("github.com/")) {
        const parts = repo.split("github.com/")[1].split("/");
        if (parts.length >= 2) {
          parsedRepo = `${parts[0]}/${parts[1]}`.replace(/\.git$/, "");
        }
      }

      const config =
        type === "GITHUB"
          ? { repo: parsedRepo, branch: "main", path }
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
    <Panel title={`Add ${type.replace(/_/g, " ")} source`}>
      <div className="grid gap-4 md:grid-cols-3">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Display name"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-black" />
        {type === "GITHUB" ? (
          <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="GitHub Repo URL (or owner/repo)"
            className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-black" />
        ) : <div />}
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder={type === "GITHUB" ? "Folder (e.g. policies/)" : "/abs/path"}
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-black" />
      </div>
      {err && <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 font-bold">{err}</div>}
      <div className="mt-4 flex justify-end gap-3">
        <button onClick={onCancel} className="rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm font-bold text-black transition hover:bg-neutral-50">Cancel</button>
        <button onClick={submit} disabled={busy}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50">
          {busy ? "Connecting…" : "Add connector"}
        </button>
      </div>
    </Panel>
  );
}
