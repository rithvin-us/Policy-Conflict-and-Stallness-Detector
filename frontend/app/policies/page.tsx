"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel, scoreColor } from "@/components/ui";

export default function PoliciesPage() {
  const { data, reload } = useApi(() => api.policies(), []);
  const [open, setOpen] = useState(false);
  
  // Filter States
  const [search, setSearch] = useState("");
  const [healthFilter, setHealthFilter] = useState("ALL");
  const [dateFilter, setDateFilter] = useState("ALL");

  const filteredItems = useMemo(() => {
    let items = data?.items || [];
    
    if (search) {
      items = items.filter(p => p.title.toLowerCase().includes(search.toLowerCase()) || p.owner?.toLowerCase().includes(search.toLowerCase()));
    }
    
    if (healthFilter === "HEALTHY") items = items.filter(p => p.health_score >= 80);
    if (healthFilter === "AT_RISK") items = items.filter(p => p.health_score < 80);
    
    if (dateFilter === "RECENT") {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      items = items.filter(p => p.last_reviewed && new Date(p.last_reviewed) >= thirtyDaysAgo);
    }
    
    return items;
  }, [data, search, healthFilter, dateFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold text-black">Policy Library</h1>
          <p className="mt-1 text-sm text-neutral-600 font-medium">
            {data?.total ?? 0} policies under continuous governance. Sorted by health.
          </p>
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm text-blue-700 font-semibold transition hover:bg-blue-100 shadow-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload Policy
        </button>
      </div>

      {open && <UploadForm onDone={() => { setOpen(false); reload(); }} />}

      <Panel>
        <div className="p-4 border-b border-neutral-200 bg-neutral-50 flex flex-col sm:flex-row gap-3 rounded-t-xl">
          <input 
            type="text" 
            placeholder="Search policies..." 
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium focus:border-blue-500 focus:outline-none shadow-sm"
          />
          <select 
            value={healthFilter} 
            onChange={e => setHealthFilter(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium focus:border-blue-500 focus:outline-none shadow-sm bg-white"
          >
            <option value="ALL">All Health Scores</option>
            <option value="HEALTHY">Healthy (≥80)</option>
            <option value="AT_RISK">At Risk (&lt;80)</option>
          </select>
          <select 
            value={dateFilter} 
            onChange={e => setDateFilter(e.target.value)}
            className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium focus:border-blue-500 focus:outline-none shadow-sm bg-white"
          >
            <option value="ALL">All Dates</option>
            <option value="RECENT">Reviewed Recently</option>
          </select>
        </div>
        
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
              {filteredItems.map((p) => (
                <tr key={p.id} className="border-t border-neutral-200 hover:bg-neutral-50 transition-colors">
                  <td className="px-3 py-3">
                    <Link href={`/policies/${p.id}`} className="font-bold text-black hover:text-blue-600 transition-colors">
                      {p.title}
                    </Link>
                    <div className="mono text-[0.66rem] text-neutral-500 font-semibold mt-0.5">{p.id}</div>
                  </td>
                  <td className="px-3 py-3 text-neutral-700 font-medium">{p.owner || "—"}</td>
                  <td className="px-3 py-3 mono text-neutral-600 font-medium">v{p.version}</td>
                  <td className="px-3 py-3 text-neutral-600 font-medium">{p.last_reviewed?.slice(0, 10) || "—"}</td>
                  <td className="px-3 py-3 text-right mono text-neutral-700 font-bold">{p.obligation_count}</td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-neutral-200">
                        <div className="h-full rounded-full" style={{ width: `${p.health_score}%`, background: scoreColor(p.health_score) }} />
                      </div>
                      <span className="mono text-xs font-bold" style={{ color: scoreColor(p.health_score) }}>{p.health_score}</span>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-neutral-500 font-medium">
                    No policies match your filters.
                  </td>
                </tr>
              )}
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
  const [fileName, setFileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setFileName(file.name);
    if (!title) setTitle(file.name.replace(/\.[^/.]+$/, "")); // Auto-fill title
    
    if (file.name.endsWith('.pdf')) {
      setErr("PDF parsing requires the premium OCR plugin. For this demo, please upload a .md or .txt file.");
      setRaw("");
      return;
    }
    
    setErr(null);
    const reader = new FileReader();
    reader.onload = (event) => {
      setRaw(event.target?.result as string);
    };
    reader.onerror = () => {
      setErr("Failed to read file contents.");
    };
    reader.readAsText(file);
  };

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
    <Panel title="Upload a policy document">
      <div className="grid gap-3 md:grid-cols-2 mb-4">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Policy Title"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400" />
        <input value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="Owner / Team"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400" />
      </div>
      
      <div className="mt-2 w-full rounded-xl border-2 border-dashed border-neutral-300 bg-neutral-50 p-6 flex flex-col items-center justify-center relative hover:bg-neutral-100 transition-colors cursor-pointer">
        <input 
          type="file" 
          accept=".md,.txt,.pdf,.csv" 
          onChange={handleFileUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
        />
        <svg className="w-8 h-8 text-neutral-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <span className="text-sm font-bold text-black">
          {fileName ? `Selected: ${fileName}` : "Click to select a file"}
        </span>
        <span className="text-xs text-neutral-500 font-medium mt-1">
          Supported formats: .md, .txt, .pdf
        </span>
      </div>
      
      {err && <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 font-bold">{err}</div>}
      
      <div className="mt-4 flex justify-end">
        <button onClick={submit} disabled={busy || !title || !raw}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
          {busy ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : "Analyze & Ingest"}
        </button>
      </div>
    </Panel>
  );
}
