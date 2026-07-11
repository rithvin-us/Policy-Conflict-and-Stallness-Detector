"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, scoreColor } from "@/components/ui";

export default function PoliciesPage() {
  const { data, reload } = useApi(() => api.policies(), []);
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Policy Library</h1>
          <p className="mt-1 text-sm text-slate-500">
            {data?.total ?? 0} policies under continuous governance. Sorted by health.
          </p>
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-1.5 text-sm text-accent-soft transition hover:bg-accent/20"
        >
          + Upload policy
        </button>
      </div>

      {open && <UploadForm onDone={() => { setOpen(false); reload(); }} />}

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-head">
              <tr>
                <th className="px-3 py-2 text-left">Policy</th>
                <th className="px-3 py-2 text-left">Owner</th>
                <th className="px-3 py-2 text-left">Version</th>
                <th className="px-3 py-2 text-left">Reviewed</th>
                <th className="px-3 py-2 text-right">Obl.</th>
                <th className="px-3 py-2 text-left">Health</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((p) => (
                <tr key={p.id} className="border-t border-white/5 hover:bg-white/[0.03]">
                  <td className="px-3 py-3">
                    <Link href={`/policies/${p.id}`} className="font-medium text-slate-200 hover:text-accent-soft">
                      {p.title}
                    </Link>
                    <div className="mono text-[0.66rem] text-slate-600">{p.id}</div>
                  </td>
                  <td className="px-3 py-3 text-slate-400">{p.owner || "—"}</td>
                  <td className="px-3 py-3 mono text-slate-400">v{p.version}</td>
                  <td className="px-3 py-3 text-slate-400">{p.last_reviewed?.slice(0, 10) || "—"}</td>
                  <td className="px-3 py-3 text-right mono text-slate-400">{p.obligation_count}</td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-white/5">
                        <div className="h-full rounded-full" style={{ width: `${p.health_score}%`, background: scoreColor(p.health_score) }} />
                      </div>
                      <span className="mono text-xs" style={{ color: scoreColor(p.health_score) }}>{p.health_score}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function UploadForm({ onDone }: { onDone: () => void }) {
  const [title, setTitle] = useState("");
  const [owner, setOwner] = useState("");
  const [raw, setRaw] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      await api.uploadPolicy({ title, owner, raw_text: raw });
      onDone();
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title="Upload a policy">
      <div className="grid gap-3 md:grid-cols-2">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title"
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
        <input value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="Owner / team"
          className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
      </div>
      <textarea value={raw} onChange={(e) => setRaw(e.target.value)} rows={6}
        placeholder="Section 3.1: All employees must rotate their passwords every 90 days."
        className="mt-3 w-full rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-slate-200 focus:border-accent focus:outline-none" />
      {err && <div className="mt-2 text-sm text-severity-high">{err}</div>}
      <div className="mt-3 flex justify-end">
        <button onClick={submit} disabled={busy || !title || !raw}
          className="rounded-lg bg-accent/20 px-4 py-2 text-sm text-accent-soft transition hover:bg-accent/30 disabled:opacity-40">
          {busy ? "Analyzing…" : "Ingest & analyze"}
        </button>
      </div>
    </Panel>
  );
}
