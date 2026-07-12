"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, TypeTag } from "@/components/ui";

const TYPES = ["POLICY_HEALTH", "CONFLICT_AUDIT", "STALENESS", "COMPLIANCE_COVERAGE"];
const FORMATS = ["MARKDOWN", "HTML", "JSON"];

export default function ReportsPage() {
  const reports = useApi(() => api.reports(), []);
  const [type, setType] = useState(TYPES[0]);
  const [format, setFormat] = useState(FORMATS[0]);
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try {
      await api.createReport(type, format);
      reports.reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-black">Audit Reports</h1>
        <p className="mt-1 text-sm text-black">
          Self-contained governance evidence for auditors — Markdown, HTML, or JSON.
        </p>
      </div>

      <Panel title="Generate report">
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Report type">
            <select value={type} onChange={(e) => setType(e.target.value)}
              className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-black focus:border-accent focus:outline-none">
              {TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
            </select>
          </Field>
          <Field label="Format">
            <select value={format} onChange={(e) => setFormat(e.target.value)}
              className="rounded-lg border border-white/10 bg-ink-850 px-3 py-2 text-sm text-black focus:border-accent focus:outline-none">
              {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </Field>
          <button onClick={generate} disabled={busy}
            className="rounded-lg bg-accent/20 px-4 py-2 text-sm text-accent-soft transition hover:bg-accent/30 disabled:opacity-40">
            {busy ? "Generating…" : "Generate"}
          </button>
        </div>
      </Panel>

      <Panel title="Generated reports">
        <div className="space-y-2">
          {(reports.data?.items || []).map((r) => (
            <div key={r.id} className="flex items-center gap-3 rounded-lg border border-white/5 bg-ink-850/50 px-3 py-2.5">
              <TypeTag label={r.report_type} />
              <span className="chip bg-white/5 text-black ring-1 ring-white/10">{r.format}</span>
              <span className="text-xs text-black">{new Date(r.generated_at).toLocaleString()}</span>
              <span className="mono ml-auto text-[0.66rem] text-black">{r.id}</span>
              <a href={api.reportDownloadUrl(r.id)} target="_blank" rel="noreferrer"
                className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-1.5 text-xs text-accent-soft transition hover:bg-accent/20">
                ⭳ Download
              </a>
            </div>
          ))}
          {reports.data && reports.data.items.length === 0 && (
            <div className="py-6 text-center text-sm text-black">No reports generated yet.</div>
          )}
        </div>
      </Panel>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="stat-label mb-1">{label}</div>
      {children}
    </div>
  );
}
