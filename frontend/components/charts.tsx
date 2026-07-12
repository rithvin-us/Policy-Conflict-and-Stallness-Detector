"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { severityColor } from "./ui";

export function TrendSpark({ data }: { data: { date: string; overall: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={64}>
      <AreaChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5b8cff" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#5b8cff" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="overall"
          stroke="#5b8cff"
          strokeWidth={2}
          fill="url(#g)"
          isAnimationActive
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ color: "#94a3b8" }}
          cursor={{ stroke: "#5b8cff33" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SeverityBars({
  data,
}: {
  data: { name: string; value: number; sev: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#ffffff08" }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} isAnimationActive>
          {data.map((d, i) => (
            <Cell key={i} fill={severityColor(d.sev)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

const tooltipStyle = {
  background: "#0f1526",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 8,
  fontSize: 12,
  color: "#e2e8f0",
};

export function GovernanceHistoryChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={30} />
        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: "#ffffff1a" }} />
        <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
        <Line type="monotone" dataKey="score" stroke="#5b8cff" strokeWidth={2} dot={false} name="Governance Score" />
        <Line type="monotone" dataKey="finding_count" stroke="#f5a524" strokeWidth={2} dot={false} name="Conflict Trend" />
        <Line type="monotone" dataKey="high_severity_count" stroke="#f0476b" strokeWidth={2} dot={false} name="Critical Findings" />
        <Line type="monotone" dataKey="stale_policies" stroke="#94a3b8" strokeWidth={2} dot={false} name="Staleness Trend" />
      </LineChart>
    </ResponsiveContainer>
  );
}
