"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ConflictCompare } from "@/components/ConflictCompare";

export default function ConflictDetailPage({ params }: { params: { id: string } }) {
  const { data, error, loading } = useApi(() => api.conflict(params.id), [params.id]);

  return (
    <div className="space-y-5">
      <Link href="/conflicts" className="text-sm text-accent hover:underline">
        ← Back to conflicts
      </Link>
      <h1 className="text-xl font-semibold text-black">Conflict Comparison</h1>
      {loading && <div className="text-sm text-black">Loading…</div>}
      {error && <div className="text-sm text-severity-high">Failed to load: {error}</div>}
      {data && <ConflictCompare conflict={data} />}
    </div>
  );
}
