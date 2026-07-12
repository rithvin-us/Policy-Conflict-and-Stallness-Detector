import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-heading" });

export const metadata: Metadata = {
  title: "Sentinal — Governance Console",
  description:
    "Continuous policy governance & compliance intelligence: conflicts, redundancy, staleness.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body className="font-sans">
        <div className="flex h-screen overflow-hidden bg-ink-900">
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

import { Clock } from "@/components/Clock";

function TopBar() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/5 bg-ink-900/40 px-6">
      <div className="flex items-center gap-2 text-xs text-black">
        <span className="mono text-black">Sentinal</span>
        <span>/</span>
        <span>governance operations console</span>
      </div>
      <div className="flex items-center gap-4 text-xs">
        <Clock />
        <div className="h-4 w-px bg-neutral-200" />
        <span className="flex items-center gap-1.5 text-severity-ok font-bold">
          <span className="h-1.5 w-1.5 animate-pulseline rounded-full bg-current" />
          SYSTEM LIVE
        </span>
        <span className="kbd ml-2">compliance manager</span>
      </div>
    </header>
  );
}
