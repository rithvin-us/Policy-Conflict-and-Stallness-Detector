"use client";

import { useMemo, useState, useEffect } from "react";
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
import { api } from "@/lib/api";
import { scoreColor, severityColor } from "./ui";

const RELATION_COLOR: Record<string, string> = {
  CONFLICT: "#e11d48",
  REDUNDANT: "#d97706",
  RELATED: "#94a3b8",
  BELONGS_TO: "#cbd5e1",
};

function PolicyNode({ data }: { data: any }) {
  const color = scoreColor(data.health ?? 100);
  return (
    <div className="w-48 rounded-xl border border-neutral-300 bg-neutral-100 p-3 shadow-sm">
      <Handle type="target" position={Position.Left} className="!bg-blue-500" />
      <Handle type="source" position={Position.Right} className="!bg-blue-500" />
      <div className="flex items-center justify-between">
        <span className="text-[0.7rem] uppercase tracking-wide text-black font-semibold">policy</span>
        <span className="text-xs font-bold" style={{ color }}>{data.health}</span>
      </div>
      <div className="mt-1 truncate text-sm font-bold text-black">{data.label}</div>
      <div className="mt-1 flex items-center justify-between text-[0.68rem] text-black font-medium">
        <span>{data.owner}</span>
        <span>{data.obligations} obl.</span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-neutral-200">
        <div className="h-full rounded-full" style={{ width: `${data.health}%`, background: color }} />
      </div>
    </div>
  );
}

const STRENGTH_COLOR: Record<string, string> = {
  MANDATORY: "#e11d48",
  RECOMMENDED: "#d97706",
  OPTIONAL: "#0284c7",
};

function ObligationNode({ data }: { data: any }) {
  return (
    <div className="w-56 rounded-lg border border-neutral-200 bg-white p-3 shadow-sm">
      <Handle type="target" position={Position.Left} className="!bg-blue-500" />
      <Handle type="source" position={Position.Right} className="!bg-blue-500" />
      <div className="flex items-center justify-between">
        <span className="chip bg-neutral-100 text-black font-bold ring-1 ring-neutral-200">{data.topic}</span>
        <span className="mono text-[0.66rem] font-bold" style={{ color: STRENGTH_COLOR[data.strength] }}>
          {data.polarity === "NEGATE" ? "¬" : ""}{data.action}
        </span>
      </div>
      <div className="mt-2 text-xs leading-snug text-black font-medium">{data.label}</div>
      <div className="mono mt-1 text-[0.62rem] text-black">{data.policy}{data.section ? ` §${data.section}` : ""}</div>
    </div>
  );
}

const nodeTypes = { policyNode: PolicyNode, obligationNode: ObligationNode };

export function GraphExplorer({ payload }: { payload: GraphPayload }) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [policyData, setPolicyData] = useState<any>(null);
  const [blastData, setBlastData] = useState<any>(null);

  useEffect(() => {
    if (selectedNode?.type === "policyNode") {
      setPolicyData(null);
      setBlastData(null);
      api.policy(selectedNode.id).then(setPolicyData).catch(console.error);
      api.blastRadius(selectedNode.id).then(setBlastData).catch(console.error);
    } else {
      setPolicyData(null);
      setBlastData(null);
    }
  }, [selectedNode]);

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
            : RELATION_COLOR[rel] || "#94a3b8";
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          type: "smoothstep",
          label: rel === "RELATED" ? undefined : e.label,
          animated: rel === "CONFLICT" && e.data?.severity === "HIGH",
          style: { stroke: color, strokeWidth: rel === "RELATED" ? 1 : 2 },
          labelStyle: { fill: color, fontSize: 10, fontWeight: "bold" },
          labelBgStyle: { fill: "#ffffff" },
        };
      }),
    [payload],
  );

  return (
    <div className="flex gap-4 h-[70vh] w-full">
      <div className="flex-1 overflow-hidden rounded-xl border border-neutral-200 bg-neutral-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.2}
          proOptions={{ hideAttribution: true }}
          onNodeClick={(_, node) => setSelectedNode(node)}
          onPaneClick={() => setSelectedNode(null)}
        >
          <Background color="#cbd5e1" gap={22} />
          <Controls showInteractive={false} className="bg-white border border-neutral-200 shadow-sm" />
        </ReactFlow>
      </div>

      {selectedNode && (
        <div className="w-80 shrink-0 overflow-y-auto rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-black">Node Details</h3>
            <button onClick={() => setSelectedNode(null)} className="text-black hover:text-black">✕</button>
          </div>
          
          {selectedNode.type === "policyNode" ? (
            policyData ? (
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-black font-semibold uppercase">Title</div>
                  <div className="text-sm text-black font-medium">{policyData.title}</div>
                </div>
                <div>
                  <div className="text-xs text-black font-semibold uppercase">Health Score</div>
                  <div className="text-sm font-bold mono" style={{ color: scoreColor(policyData.health_score) }}>{policyData.health_score}</div>
                </div>
                {blastData && (
                  <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 mt-4 space-y-2">
                    <div className="font-bold text-sm text-black">Blast Radius</div>
                    <div className="flex justify-between text-xs">
                      <span className="text-black font-medium">Potential new conflicts:</span>
                      <span className="mono font-bold text-black">{blastData.potential_new_findings}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-black font-medium">Governance impact:</span>
                      <span className="mono font-bold text-black">{blastData.estimated_governance_impact}</span>
                    </div>
                    <div className="text-xs text-black font-medium mt-2">Affected Policies: {blastData.affected_policies?.length || 0}</div>
                  </div>
                )}
              </div>
            ) : <div className="text-sm text-black font-medium">Loading details...</div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-xs text-black font-semibold uppercase">Action</div>
                <div className="text-sm text-black font-medium">{selectedNode.data.action}</div>
              </div>
              <div>
                <div className="text-xs text-black font-semibold uppercase">Topic</div>
                <div className="text-sm text-black font-medium">{selectedNode.data.topic}</div>
              </div>
              <div>
                <div className="text-xs text-black font-semibold uppercase">Text</div>
                <div className="text-xs text-black font-medium mt-1 leading-relaxed">{selectedNode.data.label}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
