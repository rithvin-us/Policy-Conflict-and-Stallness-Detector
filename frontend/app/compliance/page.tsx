"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Panel } from "@/components/ui";

export default function CompliancePage() {
  const { data } = useApi(() => api.compliance(), []);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Compliance Mapping</h1>
        <p className="mt-1 text-sm text-slate-500">
          Framework coverage across ISO 27001, NIST SP 800-53, GDPR, and COBIT 2019 — audit evidence at a glance.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 space-y-6 lg:col-span-8">
          {(data?.frameworks || []).map((f) => (
            <Panel key={f.framework} title={f.framework}>
              <div className="space-y-2">
                {f.clauses.map((cl) => (
                  <div key={cl.clause} className="flex items-center gap-3 rounded-lg border border-white/5 bg-ink-850/50 px-3 py-2.5">
                    <span className={`grid h-6 w-6 place-items-center rounded-full text-xs ${
                      cl.covered ? "bg-severity-ok/15 text-severity-ok" : "bg-severity-high/15 text-severity-high"
                    }`}>
                      {cl.covered ? "✓" : "!"}
                    </span>
                    <div className="flex-1">
                      <span className="mono text-xs text-slate-400">{cl.clause}</span>
                      <span className="ml-2 text-sm text-slate-300">{cl.title}</span>
                    </div>
                    {cl.findings > 0 && (
                      <span className="chip bg-severity-high/15 text-severity-high ring-1 ring-severity-high/30">
                        {cl.findings} finding{cl.findings > 1 ? "s" : ""}
                      </span>
                    )}
                    <span className="mono text-[0.66rem] text-slate-600">{cl.policies.length} policies</span>
                  </div>
                ))}
              </div>
            </Panel>
          ))}
        </div>

        <Panel className="col-span-12 lg:col-span-4" title="Coverage Gaps">
          <div className="space-y-2">
            {(data?.gaps || []).map((g) => (
              <div key={g.topic} className="rounded-lg border border-severity-medium/20 bg-severity-medium/5 p-3">
                <div className="text-sm font-medium text-severity-medium">{g.topic}</div>
                <div className="text-xs text-slate-500">{g.reason}</div>
              </div>
            ))}
            {data && data.gaps.length === 0 && (
              <div className="py-6 text-center text-sm text-severity-ok">Full topic coverage.</div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
