"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview", glyph: "◈" },
  { href: "/conflicts", label: "Conflicts", glyph: "⚡" },
  { href: "/staleness", label: "Staleness", glyph: "◷" },
  { href: "/graph", label: "Graph Explorer", glyph: "⟁" },
  { href: "/policies", label: "Policies", glyph: "▤" },
  { href: "/compliance", label: "Compliance", glyph: "✓" },
  { href: "/connectors", label: "Sources & Webhooks", glyph: "⇄" },
  { href: "/reports", label: "Reports", glyph: "⭳" },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-white/5 bg-ink-900/60 px-3 py-5">
      <div className="mb-8 px-2">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent/20 text-accent-soft shadow-glow">
            <span className="text-lg">⬡</span>
          </div>
          <div>
            <div className="text-sm font-semibold leading-none text-slate-100">
              Policy Guardian
            </div>
            <div className="mt-1 text-[0.62rem] uppercase tracking-[0.18em] text-slate-500">
              AI Governance
            </div>
          </div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? path === "/" : path.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`navlink ${active ? "navlink-active" : ""}`}
            >
              <span className="w-4 text-center text-slate-500">{item.glyph}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg border border-white/5 bg-ink-850/70 p-3 text-[0.7rem] text-slate-500">
        <div className="mb-1 font-medium text-slate-400">Deterministic engine</div>
        Findings are reproducible and cite exact source text.
      </div>
    </aside>
  );
}
