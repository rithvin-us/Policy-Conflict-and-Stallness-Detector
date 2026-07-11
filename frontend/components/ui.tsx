// Small shared UI primitives used across the console.
import type { Severity } from "@/lib/types";

const SEV_STYLES: Record<string, string> = {
  HIGH: "bg-severity-high/15 text-severity-high ring-1 ring-severity-high/30",
  MEDIUM: "bg-severity-medium/15 text-severity-medium ring-1 ring-severity-medium/30",
  LOW: "bg-severity-low/15 text-severity-low ring-1 ring-severity-low/30",
};

export function SeverityChip({ severity }: { severity: Severity | string }) {
  return (
    <span className={`chip ${SEV_STYLES[severity] || SEV_STYLES.LOW}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  CONNECTED: "bg-severity-ok/15 text-severity-ok ring-severity-ok/30",
  SYNCING: "bg-severity-medium/15 text-severity-medium ring-severity-medium/30",
  ERROR: "bg-severity-high/15 text-severity-high ring-severity-high/30",
  DISCONNECTED: "bg-slate-500/15 text-slate-400 ring-slate-500/30",
  NOT_CONFIGURED: "bg-slate-600/15 text-slate-500 ring-slate-600/30",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span className={`chip ring-1 ${STATUS_STYLES[status] || STATUS_STYLES.NOT_CONFIGURED}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function TypeTag({ label }: { label: string }) {
  return (
    <span className="chip bg-white/5 text-slate-300 ring-1 ring-white/10">
      {label.replace(/_/g, " ")}
    </span>
  );
}

export function Panel({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-white/5 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
          {action}
        </header>
      )}
      <div className="panel-pad">{children}</div>
    </section>
  );
}

export function severityColor(sev: string): string {
  return (
    { HIGH: "#f0476b", MEDIUM: "#f5a524", LOW: "#3aa0ff" }[sev] || "#3aa0ff"
  );
}

export function scoreColor(score: number): string {
  if (score >= 75) return "#2dd4a7";
  if (score >= 50) return "#f5a524";
  return "#f0476b";
}
