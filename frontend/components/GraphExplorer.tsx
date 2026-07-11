"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";
import type { GraphPayload } from "@/lib/types";
import { scoreColor, severityColor } from "./ui";

const RELATION_COLOR: Record<string, string> = {
  CONFLICT: "#f0476b",
  REDUNDANT: "#f5a524",
  RELATED: "#3a466b",
  BELONGS_TO: "#26304f",
};

function PolicyNode({ data }: { data: any }) {
  const color = scoreColor(data.health ?? 100);
  return (
    <div className="w-48 rounded-xl border border-white/10 bg-ink-850/95 p-3 shadow-panel">
      <Handle type="target" position={Position.Left} className="!bg-accent" />
      <Handle type="source" position={Position.Right} className="!bg-accent" />
      <div className="flex items-center justify-between">
        <span className="text-[0.7rem] uppercase tracking-wide text-slate-500">policy</span>
        <span className="text-xs font-semibold" style={{ color }}>{data.health}</span>
      </div>
      <div className="mt-1 truncate text-sm font-medium text-slate-100">{data.label}</div>
      <div className="mt-1 flex items-center justify-between text-[0.68rem] text-slate-500">
        <span>{data.owner}</span>
        <span>{data.obligations} obl.</span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/5">
        <div className="h-full rounded-full" style={{ width: `${data.health}%`, background: color }} />
      </div>
    </div>
  );
}

const STRENGTH_COLOR: Record<string, string> = {
  MANDATORY: "#f0476b",
  RECOMMENDED: "#f5a524",
  OPTIONAL: "#3aa0ff",
};

function ObligationNode({ data }: { data: any }) {
  return (
    <div className="w-56 rounded-lg border border-white/10 bg-ink-850/95 p-3 shadow-panel">
      <Handle type="target" position={Position.Left} className="!bg-accent" />
      <Handle type="source" position={Position.Right} className="!bg-accent" />
      <div className="flex items-center justify-between">
        <span className="chip bg-white/5 text-slate-300 ring-1 ring-white/10">{data.topic}</span>
        <span className="mono text-[0.66rem]" style={{ color: STRENGTH_COLOR[data.strength] }}>
          {data.polarity === "NEGATE" ? "¬" : ""}{data.action}
        </span>
      </div>
      <div className="mt-2 text-xs leading-snug text-slate-300">{data.label}</div>
      <div className="mono mt-1 text-[0.62rem] text-slate-600">{data.policy}{data.section ? ` §${data.section}` : ""}</div>
    </div>
  );
}

const nodeTypes = { policyNode: PolicyNode, obligationNode: ObligationNode };

export function GraphExplorer({ payload }: { payload: GraphPayload }) {
  const nodes: Node[] = useMemo(
    () => payload.nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
    [payload],
  );

  const edges: Edge[] = useMemo(
    () =>
      payload.edges.map((e) => {
        const rel = e.data?.relation || "RELATED";
        const color =
          rel === "CONFLICT" && e.data?.severity
            ? severityColor(e.data.severity)
            : RELATION_COLOR[rel] || "#3a466b";
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          label: rel === "RELATED" ? undefined : e.label,
          animated: rel === "CONFLICT" && e.data?.severity === "HIGH",
          style: { stroke: color, strokeWidth: rel === "RELATED" ? 1 : 2 },
          labelStyle: { fill: color, fontSize: 10 },
          labelBgStyle: { fill: "#0b1020" },
        };
      }),
    [payload],
  );

  return (
    <div className="h-[70vh] w-full overflow-hidden rounded-xl border border-white/5">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1c2540" gap={22} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
