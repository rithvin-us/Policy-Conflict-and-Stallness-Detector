"use client";

import { motion } from "framer-motion";
import type { Conflict, ExplanationPayload } from "@/lib/types";
import { Panel, SeverityChip, TypeTag } from "./ui";

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
      <mark key={`m${i}`} className="rounded bg-severity-high/25 px-0.5 text-severity-high">
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
    <div className="flex-1 rounded-lg border border-white/5 bg-ink-850/60 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-slate-200">{title || policyId}</span>
        {section && <span className="kbd">§{section}</span>}
      </div>
      <p className="text-sm leading-relaxed text-slate-300">
        <Highlighted quote={quote} spans={spans} />
      </p>
      <div className="mono mt-3 text-[0.66rem] text-slate-600">{policyId}</div>
    </div>
  );
}

export function ConflictCompare({ conflict }: { conflict: Conflict }) {
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
        <span className="chip bg-white/5 text-slate-400 ring-1 ring-white/10">
          confidence {Math.round(conflict.confidence * 100)}%
        </span>
        <span className="chip bg-white/5 text-slate-400 ring-1 ring-white/10">
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
          <span className="rounded-full bg-severity-high/15 px-2 py-1 text-xs font-semibold text-severity-high">
            ⚡ vs
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

      <Panel title="Why this was flagged">
        <p className="text-sm leading-relaxed text-slate-300">
          {ep?.why_flagged || conflict.explanation}
        </p>
        {conflict.scope_analysis && (
          <p className="mt-3 rounded-lg border border-severity-medium/20 bg-severity-medium/5 p-3 text-sm text-severity-medium">
            <span className="font-medium">Scope analysis: </span>
            {conflict.scope_analysis}
          </p>
        )}
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <div className="stat-label mb-1">Likely resolution</div>
            <p className="text-sm text-slate-300">{conflict.resolution_suggestion}</p>
          </div>
          <div>
            <div className="stat-label mb-1">Compliance impact</div>
            <div className="flex flex-wrap gap-1.5">
              {(conflict.compliance_impact || []).map((r) => (
                <span key={r} className="chip bg-accent/10 text-accent-soft ring-1 ring-accent/20">
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
                <span key={t} className="mono rounded bg-severity-high/10 px-1.5 py-0.5 text-severity-high">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </Panel>
    </motion.div>
  );
}
