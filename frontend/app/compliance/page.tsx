"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel } from "@/components/ui";

export default function CompliancePage() {
  const { data } = useApi(() => api.compliance(), []);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState<Record<string, boolean>>({});

  const toggleClause = (clauseId: string) => {
    setExpandedClauses(prev => ({ ...prev, [clauseId]: !prev[clauseId] }));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-black">Compliance Mapping</h1>
          <p className="mt-1 text-sm text-neutral-600 font-medium">
            Framework coverage across ISO 27001, NIST SP 800-53, GDPR, and COBIT 2019 — audit evidence at a glance.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSyncModal(true)}
            className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700 font-bold transition hover:bg-blue-100 shadow-sm flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Auto-Sync
          </button>
          <button
            onClick={() => setShowSyncModal(true)}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm text-white font-bold transition hover:bg-neutral-800 shadow-sm"
          >
            + Add Framework
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 space-y-6 lg:col-span-8">
          {(data?.frameworks || []).map((f) => (
            <Panel key={f.framework} title={f.framework}>
              <div className="space-y-3 mt-4">
                {f.clauses.map((cl) => {
                  const isExpanded = expandedClauses[cl.clause];
                  return (
                    <div key={cl.clause} className="rounded-xl border border-neutral-200 bg-white overflow-hidden shadow-sm transition-all hover:border-neutral-300">
                      <div 
                        onClick={() => toggleClause(cl.clause)}
                        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-neutral-50 transition-colors"
                      >
                        <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold ${
                          cl.covered ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}>
                          {cl.covered ? "✓" : "!"}
                        </span>
                        <div className="flex-1">
                          <span className="mono text-xs text-neutral-500 font-bold">{cl.clause}</span>
                          <span className="ml-2 text-sm text-black font-semibold">{cl.title}</span>
                        </div>
                        {cl.findings > 0 && (
                          <Link 
                            href="/conflicts" 
                            onClick={(e) => e.stopPropagation()}
                            className="chip bg-red-50 text-red-700 ring-1 ring-red-200 hover:bg-red-100 transition-colors"
                          >
                            {cl.findings} finding{cl.findings > 1 ? "s" : ""} ➔
                          </Link>
                        )}
                        <span className="mono text-[0.66rem] text-neutral-500 font-medium bg-neutral-100 px-2 py-1 rounded-md">{cl.policies.length} policies</span>
                        <svg className={`w-4 h-4 text-neutral-400 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                      
                      {isExpanded && (
                        <div className="px-12 py-3 bg-neutral-50 border-t border-neutral-100 text-sm">
                          <h4 className="text-xs uppercase tracking-wider text-neutral-500 font-bold mb-2">Fulfilling Policies</h4>
                          {cl.policies.length > 0 ? (
                            <ul className="list-disc pl-4 space-y-1">
                              {cl.policies.map(pid => (
                                <li key={pid}>
                                  <Link href={`/policies/${pid}`} className="text-blue-600 hover:underline font-medium">
                                    {pid}
                                  </Link>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-neutral-500 italic">No policies currently map to this clause. This represents a compliance gap.</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Panel>
          ))}
        </div>

        <Panel className="col-span-12 lg:col-span-4" title="Coverage Gaps & Risks">
          <div className="space-y-3 mt-4">
            {(data?.gaps || []).map((g) => (
              <Link 
                href="/conflicts" 
                key={g.topic} 
                className="block rounded-xl border border-amber-200 bg-amber-50 p-4 transition-transform hover:-translate-y-1 hover:shadow-md cursor-pointer group"
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="text-sm font-bold text-amber-800">{g.topic}</div>
                  <svg className="w-4 h-4 text-amber-500 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </div>
                <div className="text-xs text-amber-700/80 font-medium leading-relaxed">{g.reason}</div>
                <div className="mt-3 text-[0.65rem] uppercase tracking-wider font-bold text-amber-600 bg-amber-100 inline-block px-2 py-1 rounded">
                  View Risk Details
                </div>
              </Link>
            ))}
            {data && data.gaps.length === 0 && (
              <div className="py-8 text-center text-sm font-bold text-green-600 bg-green-50 rounded-xl border border-green-200">
                Full topic coverage achieved. No active gaps!
              </div>
            )}
          </div>
        </Panel>
      </div>

      {showSyncModal && <SyncModal onClose={() => setShowSyncModal(false)} />}
    </div>
  );
}

function SyncModal({ onClose }: { onClose: () => void }) {
  const [syncing, setSyncing] = useState(false);
  const [done, setDone] = useState(false);

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      setDone(true);
      setTimeout(onClose, 2000);
    }, 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-neutral-100">
          <h2 className="text-xl font-bold text-black">Integrations & Frameworks</h2>
          <p className="text-sm text-neutral-500 mt-1">Connect your compliance providers to auto-sync control mappings.</p>
        </div>
        
        <div className="p-6 space-y-4 bg-neutral-50">
          {[
            { name: "Vanta", desc: "Sync SOC2 & ISO27001 controls", icon: "V" },
            { name: "Drata", desc: "Continuous compliance monitoring", icon: "D" },
            { name: "AWS Security Hub", desc: "Cloud security posture mappings", icon: "aws" }
          ].map(provider => (
            <div key={provider.name} className="flex items-center justify-between p-4 bg-white rounded-xl border border-neutral-200 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center font-bold text-neutral-400 border border-neutral-200">
                  {provider.icon}
                </div>
                <div>
                  <div className="font-bold text-sm text-black">{provider.name}</div>
                  <div className="text-xs text-neutral-500">{provider.desc}</div>
                </div>
              </div>
              <button 
                onClick={handleSync}
                disabled={syncing || done}
                className="px-3 py-1.5 text-xs font-bold bg-neutral-100 text-neutral-700 rounded-lg hover:bg-neutral-200 transition-colors disabled:opacity-50"
              >
                {syncing ? "Connecting..." : done ? "Connected ✓" : "Connect"}
              </button>
            </div>
          ))}
        </div>
        
        <div className="p-4 border-t border-neutral-100 flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-bold text-neutral-600 hover:text-black transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
