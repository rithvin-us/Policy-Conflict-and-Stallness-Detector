"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { Conflict, ExplanationPayload } from "@/lib/types";
import { api } from "@/lib/api";
import { Panel, SeverityChip, TypeTag } from "./ui";
import { CheckCircle2, ShieldAlert } from "lucide-react";

// Renders a quote with trigger terms highlighted, using the [start,end] spans
// from the explanation payload (server-computed so highlighting is exact).
function Highlighted({ quote, spans }: { quote: string; spans: [number, number][] }) {
  if (!spans?.length) return <>{quote}</>;
  const sorted = [...spans].sort((a, b) => a[0] - b[0]);
  const out: React.ReactNode[] = [];
  let cursor = 0;
  sorted.forEach(([s, e], i) => {
    if (s > cursor) out.push(<span key={`t${i}`}>{quote.slice(cursor, s)}</span>);
    out.push(
      <mark key={`m${i}`} className="rounded bg-severity-high/20 px-0.5 font-medium text-severity-high">
        {quote.slice(s, e)}
      </mark>,
    );
    cursor = Math.max(cursor, e);
  });
  if (cursor < quote.length) out.push(<span key="tail">{quote.slice(cursor)}</span>);
  return <>{out}</>;
}

function PolicySide({
  title,
  policyId,
  section,
  quote,
  spans,
}: {
  title?: string;
  policyId: string;
  section: string | null;
  quote: string;
  spans: [number, number][];
}) {
  return (
    <div className="flex-1 rounded-lg border border-ink-800 bg-ink-950 p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-bold text-slate-900">{title || policyId}</span>
        {section && <span className="kbd">§{section}</span>}
      </div>
      <p className="text-sm leading-relaxed text-slate-700">
        <Highlighted quote={quote} spans={spans} />
      </p>
      <div className="mono mt-3 text-[0.66rem] text-slate-500">{policyId}</div>
    </div>
  );
}

export function ConflictCompare({ conflict }: { conflict: Conflict }) {
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const getSuggestion = async () => {
    setLoadingAi(true);
    try {
      const res = await api.suggestResolution(conflict.id);
      setAiSuggestion(res.suggestion);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAi(false);
    }
  };

  const ep: ExplanationPayload | undefined = conflict.explanation_payload;
  const spanA = ep?.spans?.[0];
  const spanB = ep?.spans?.[1];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <SeverityChip severity={conflict.severity} />
        <TypeTag label={conflict.conflict_type} />
        <span className="chip bg-ink-900 text-slate-600 ring-1 ring-ink-800">
          confidence {Math.round(conflict.confidence * 100)}%
        </span>
        <span className="chip bg-ink-900 text-slate-600 ring-1 ring-ink-800">
          risk {Math.round(conflict.risk)}
        </span>
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
        <PolicySide
          title={conflict.policy_a_title}
          policyId={conflict.evidence.a.policy_id}
          section={conflict.evidence.a.section}
          quote={conflict.evidence.a.quote}
          spans={spanA?.highlight || []}
        />
        <div className="grid place-items-center px-1">
          <span className="flex items-center gap-1 rounded-full bg-severity-high/15 px-2.5 py-1 text-xs font-bold uppercase tracking-widest text-severity-high">
            <ShieldAlert size={14} /> VS
          </span>
        </div>
        <PolicySide
          title={conflict.policy_b_title}
          policyId={conflict.evidence.b.policy_id}
          section={conflict.evidence.b.section}
          quote={conflict.evidence.b.quote}
          spans={spanB?.highlight || []}
        />
      </div>

      <Panel title="Analysis Details">
        <p className="text-sm leading-relaxed text-slate-700 font-medium">
          {ep?.why_flagged || conflict.explanation}
        </p>
        {conflict.scope_analysis && (
          <p className="mt-3 rounded-lg border border-severity-medium/30 bg-severity-medium/10 p-3 text-sm text-severity-medium font-medium">
            <span className="font-bold">Scope analysis: </span>
            {conflict.scope_analysis}
          </p>
        )}
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <div className="stat-label mb-1 flex items-center justify-between">
              <span>Likely resolution</span>
              <button 
                onClick={getSuggestion} 
                disabled={loadingAi}
                className="text-accent text-[0.65rem] hover:underline bg-accent/10 px-2 py-1 rounded transition disabled:opacity-50 font-semibold"
              >
                {loadingAi ? "Analyzing dependencies..." : "Generate Remediation Strategy"}
              </button>
            </div>
            {aiSuggestion ? (
              <div className="text-sm text-accent bg-accent/5 p-3 rounded-lg border border-accent/20 font-medium leading-relaxed">
                {aiSuggestion}
              </div>
            ) : (
              <p className="text-sm text-slate-700 font-medium">{conflict.resolution_suggestion}</p>
            )}
          </div>
          <div>
            <div className="stat-label mb-1">Compliance impact</div>
            <div className="flex flex-wrap gap-1.5">
              {(conflict.compliance_impact || []).map((r) => (
                <span key={r} className="chip bg-accent/10 text-accent font-semibold ring-1 ring-accent/20">
                  {r}
                </span>
              ))}
            </div>
          </div>
        </div>
        {ep?.trigger_terms?.length ? (
          <div className="mt-4">
            <div className="stat-label mb-1">Trigger terms</div>
            <div className="flex flex-wrap gap-1.5">
              {ep.trigger_terms.map((t) => (
                <span key={t} className="mono rounded bg-severity-high/15 px-1.5 py-0.5 font-bold text-severity-high">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ) : null}
        {ep?.confidence_factors?.length ? (
          <div className="mt-4">
            <div className="stat-label mb-1">Confidence Breakdown</div>
            <ul className="text-sm text-slate-700 space-y-1.5 font-medium">
              {ep.confidence_factors.map((factor) => (
                <li key={factor} className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-severity-low" /> {factor}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Panel>
    </motion.div>
  );
}
