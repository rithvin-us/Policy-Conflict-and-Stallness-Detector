import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Policy Guardian AI — Governance Console",
  description:
    "Continuous policy governance & compliance intelligence: conflicts, redundancy, staleness.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar />
            <main className="flex-1 overflow-y-auto px-6 py-6">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}

function TopBar() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/5 bg-ink-900/40 px-6">
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span className="mono text-slate-400">policy-guardian</span>
        <span>/</span>
        <span>governance operations console</span>
      </div>
      <div className="flex items-center gap-3 text-xs">
        <span className="flex items-center gap-1.5 text-severity-ok">
          <span className="h-1.5 w-1.5 animate-pulseline rounded-full bg-current" />
          live
        </span>
        <span className="kbd">compliance manager</span>
      </div>
    </header>
  );
}
