"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel } from "@/components/ui";

export default function PolicyVersionsPage({ params }: { params: { id: string } }) {
  const { data, error, loading } = useApi(() => api.policyVersions(params.id), [params.id]);
  const [selectedV1, setSelectedV1] = useState<string | null>(null);
  const [selectedV2, setSelectedV2] = useState<string | null>(null);

  if (loading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (error || !data) return <div className="text-sm text-severity-high">Failed to load policy versions.</div>;

  const versions = data.items || [];
  
  if (versions.length > 0 && selectedV1 === null) {
    setSelectedV1(versions[0]?.id || null);
    setSelectedV2(versions.length > 1 ? versions[1]?.id || null : versions[0]?.id || null);
  }

  const v1 = versions.find(v => v.id === selectedV1);
  const v2 = versions.find(v => v.id === selectedV2);

  return (
    <div className="space-y-6">
      <Link href={`/policies/${params.id}`} className="text-sm text-accent hover:underline">← Back to Policy</Link>

      <div>
        <h1 className="text-xl font-semibold text-slate-100">Version History</h1>
        <p className="mt-1 text-sm text-slate-500">Compare policy changes over time.</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <Panel className="col-span-12 lg:col-span-6" title="Old Version">
          <select 
            className="w-full bg-ink-900 border border-white/10 rounded px-2 py-1 text-sm text-slate-300 mb-4"
            value={selectedV2 || ""}
            onChange={(e) => setSelectedV2(e.target.value)}
          >
            {versions.map(v => (
              <option key={v.id} value={v.id}>Version {v.version} ({v.created_at?.slice(0, 10)})</option>
            ))}
          </select>
          <div className="rounded-lg border border-white/5 bg-ink-850/50 p-4 overflow-auto max-h-[60vh]">
            <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono">
              {v2?.raw_text || "No text available"}
            </pre>
          </div>
        </Panel>
        
        <Panel className="col-span-12 lg:col-span-6" title="New Version">
          <select 
            className="w-full bg-ink-900 border border-white/10 rounded px-2 py-1 text-sm text-slate-300 mb-4"
            value={selectedV1 || ""}
            onChange={(e) => setSelectedV1(e.target.value)}
          >
            {versions.map(v => (
              <option key={v.id} value={v.id}>Version {v.version} ({v.created_at?.slice(0, 10)})</option>
            ))}
          </select>
          <div className="rounded-lg border border-white/5 bg-ink-850/50 p-4 overflow-auto max-h-[60vh]">
            <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono">
              {v1?.raw_text || "No text available"}
            </pre>
          </div>
        </Panel>
      </div>
    </div>
  );
}
