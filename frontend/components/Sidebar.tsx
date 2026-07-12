"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  AlertTriangle, 
  Clock, 
  Network, 
  FileText, 
  ShieldCheck, 
  Webhook, 
  Settings, 
  Download,
  Hexagon
} from "lucide-react";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/conflicts", label: "Conflicts", icon: AlertTriangle },
  { href: "/staleness", label: "Staleness", icon: Clock },
  { href: "/graph", label: "Graph Explorer", icon: Network },
  { href: "/policies", label: "Policies", icon: FileText },
  { href: "/compliance", label: "Compliance", icon: ShieldCheck },
  { href: "/connectors", label: "Sources & Webhooks", icon: Webhook },
  { href: "/governance", label: "Governance", icon: Settings },
  { href: "/reports", label: "Reports", icon: Download },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-ink-800 bg-ink-950 px-3 py-5">
      <div className="mb-8 px-2">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent/10 text-accent shadow-glow">
            <Hexagon size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold leading-none text-slate-900 font-heading tracking-tight">
              Policy Guardian
            </div>
            <div className="mt-1 text-[0.62rem] uppercase tracking-[0.18em] text-slate-500 font-semibold">
              Governance
            </div>
          </div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? path === "/" : path.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`navlink ${active ? "navlink-active" : ""}`}
            >
              <Icon size={16} className={active ? "text-accent" : "text-slate-400"} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8 mb-2">
        <button 
          onClick={() => {
            document.cookie = "demo_auth=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = "/login";
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Sign out
        </button>
      </div>

      <div className="mt-auto rounded-lg border border-ink-800 bg-ink-900/70 p-3 text-[0.7rem] text-slate-500 shadow-sm">
        <div className="mb-1 font-medium text-slate-700">Deterministic Engine</div>
        Findings are reproducible and cite exact source text.
      </div>
    </aside>
  );
}
