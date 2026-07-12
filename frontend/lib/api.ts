// Thin typed client over the backend REST API. In the browser, requests are
// same-origin ("/api/...") and proxied to the backend by next.config rewrites.

import type {
  AuditEvent,
  ComplianceCoverage,
  Conflict,
  Connector,
  GithubStatus,
  GovernanceScore,
  GraphPayload,
  Policy,
  PolicyVersion,
  Report,
  ReviewItem,
  StalenessFinding,
  TimelineEvent,
  WebhookEvent,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL + "/api/v1"
    : typeof window === "undefined"
      ? (
          process.env.BACKEND_INTERNAL_URL ||
          (process.env.NODE_ENV === "production" ? "http://api:8000" : "http://localhost:8000")
        ) + "/api/v1"
      : "/api/v1";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${path}: ${text.slice(0, 200)}`);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json() as Promise<T>;
}

type List<T> = { items: T[]; total: number };

export const api = {
  overview: () => req<GovernanceScore>("/dashboard/overview"),
  history: () => req<any[]>("/history"),
  timeline: (limit = 30) => req<{ items: TimelineEvent[] }>(`/timeline?limit=${limit}`),
  meta: () => req<Record<string, string[]>>("/meta"),

  policies: (q = "") => req<List<Policy>>(`/policies${q}`),
  policy: (id: string) =>
    req<Policy & { obligations: any[]; conflicts: Conflict[]; staleness: StalenessFinding[] }>(
      `/policies/${id}`,
    ),
  uploadPolicy: (body: Record<string, unknown>) =>
    req<Policy>("/policies/upload", { method: "POST", body: JSON.stringify(body) }),
  deletePolicy: (id: string) =>
    req<void>(`/policies/${id}`, { method: "DELETE" }),

  conflicts: (q = "") => req<List<Conflict>>(`/conflicts${q}`),
  conflict: (id: string) => req<Conflict>(`/conflicts/${id}`),
  suggestResolution: (id: string) => req<{suggestion: string}>(`/conflicts/${id}/suggest-resolution`, { method: "POST" }),
  redundancies: () => req<List<Conflict>>("/redundancies"),
  staleness: () => req<List<StalenessFinding>>("/staleness"),
  reviewQueue: () => req<List<ReviewItem>>("/review-queue"),

  graph: (mode: "POLICY" | "OBLIGATION", extra = "") =>
    req<GraphPayload>(`/graph?mode=${mode}${extra}`),

  compliance: () => req<ComplianceCoverage>("/compliance/coverage"),

  connectors: () => req<List<Connector>>("/connectors"),
  createConnector: (body: Record<string, unknown>) =>
    req<Connector>("/connectors", { method: "POST", body: JSON.stringify(body) }),
  deleteConnector: (id: string) =>
    req<void>(`/connectors/${id}`, { method: "DELETE" }),
  updateConnector: (id: string, body: Record<string, unknown>) =>
    req<Connector>(`/connectors/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  syncConnector: (id: string) =>
    req<Record<string, unknown>>(`/connectors/${id}/sync`, { method: "POST" }),
  webhookEvents: () => req<List<WebhookEvent>>("/webhooks/events"),
  registerWebhook: (connector_id: string, event_types: string[] = ["push", "pull_request"], github_token?: string) =>
    req<Record<string, unknown>>("/webhooks/register", {
      method: "POST",
      body: JSON.stringify({ connector_id, event_types, github_token }),
    }),

  // GitHub automated onboarding
  githubOrgs: (token: string) => 
    req<any[]>("/github/orgs", { headers: { Authorization: `Bearer ${token}` } }),
  githubRepos: (token: string, org?: string) => 
    req<List<any>>(`/github/repos${org ? `?org=${encodeURIComponent(org)}` : ""}`, { headers: { Authorization: `Bearer ${token}` } }),
  githubRepoContents: (token: string, full_name: string) =>
    req<any[]>(`https://api.github.com/repos/${full_name}/contents`, { headers: { Authorization: `Bearer ${token}` } }),
  githubRepoTree: (token: string, full_name: string, branch: string) =>
    req<any>(`https://api.github.com/repos/${full_name}/git/trees/${branch}?recursive=1`, { headers: { Authorization: `Bearer ${token}` } }),
  bulkGitHubConnect: (token: string, repos: any[]) =>
    req<any>("/connectors/bulk-github", { method: "POST", body: JSON.stringify({ github_token: token, repositories: repos }) }),

  // Continuous governance / GitHub integration.
  githubStatus: () => req<GithubStatus>("/github/status"),
  audit: (q = "") => req<List<AuditEvent>>(`/audit${q}`),
  reviewAudit: (id: string, body: Record<string, unknown>) =>
    req<AuditEvent>(`/audit/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  policyVersions: (id: string) =>
    req<List<PolicyVersion>>(`/policies/${id}/versions`),
  blastRadius: (id: string) =>
    req<any>(`/policies/${id}/blast-radius`),
  eventStreamUrl: () => "/api/v1/events/stream",

  runAnalysis: () =>
    req<Record<string, unknown>>("/analysis/run", { method: "POST", body: "{}" }),

  reports: () => req<List<Report>>("/reports"),
  createReport: (report_type: string, format: string) =>
    req<Report>("/reports", {
      method: "POST",
      body: JSON.stringify({ report_type, format }),
    }),
  reportDownloadUrl: (id: string) => `/api/v1/reports/${id}/download`,
};
