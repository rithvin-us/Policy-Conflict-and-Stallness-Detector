// TypeScript mirror of docs/data-dictionary.md. The frontend consumes only
// these shapes — it never invents fields absent from the backend contract.

export type Severity = "HIGH" | "MEDIUM" | "LOW";

export interface GovernanceScore {
  overall: number;
  policy_health: number;
  conflict_pressure: number;
  staleness_index: number;
  coverage: number;
  trend: { date: string; overall: number }[];
  counts: {
    policies: number;
    conflicts: number;
    redundancies: number;
    stale: number;
    obligations: number;
  };
  policy_health_by_id?: Record<string, number>;
}

export interface Policy {
  id: string;
  title: string;
  source: string;
  owner: string;
  author: string | null;
  version: string;
  status: string;
  last_reviewed: string | null;
  created_at: string | null;
  updated_at: string | null;
  tags: string[];
  content: string;
  raw_text: string;
  summary: string | null;
  health_score: number;
  obligation_count: number;
}

export interface Obligation {
  id: string;
  policy_id: string;
  section: string | null;
  topic: string;
  action: string;
  scope: { kind: string; value: string; raw: string };
  strength: string;
  polarity: string;
  parameters: Record<string, unknown>;
  evidence_text: string;
  confidence: number;
}

export interface Conflict {
  id: string;
  policy_a_id: string;
  policy_b_id: string;
  obligation_a_id: string | null;
  obligation_b_id: string | null;
  conflict_type: string;
  severity: Severity;
  explanation: string;
  evidence: {
    a: { policy_id: string; section: string | null; quote: string };
    b: { policy_id: string; section: string | null; quote: string };
    trigger_terms: string[];
  };
  confidence: number;
  confidence_factors: string[];
  scope_analysis: string | null;
  resolution_suggestion: string;
  compliance_impact: string[];
  risk: number;
  policy_a_title?: string;
  policy_b_title?: string;
  explanation_payload?: ExplanationPayload;
}

export interface ExplanationPayload {
  title: string;
  why_flagged: string;
  trigger_terms: string[];
  spans: {
    policy_id: string;
    section: string | null;
    quote: string;
    highlight: [number, number][];
  }[];
  sections_involved: string[];
  likely_resolution: string;
  compliance_refs: string[];
  confidence: number;
  confidence_factors: string[];
}

export interface StalenessFinding {
  id: string;
  policy_id: string;
  stale_reason: string;
  severity: Severity;
  evidence: string[];
  recommendation: string;
  age_months: number | null;
  risk: number;
}

export interface ReviewItem {
  id: string;
  kind: "CONFLICT" | "STALE";
  severity: Severity;
  confidence: number;
  risk: number;
  title: string;
  policies: string[];
  summary: string;
}

export interface Connector {
  id: string;
  type: string;
  name: string;
  status: string;
  last_sync: string | null;
  error_message: string | null;
  config: Record<string, unknown>;
}

export interface WebhookEvent {
  id: string;
  source: string;
  event_type: string;
  payload: Record<string, unknown>;
  received_at: string;
  processed_at: string | null;
  status: string;
  detail: string | null;
}

export interface AuditEvent {
  id: string;
  created_at: string;
  source: string;
  event_type: string;
  repo: string | null;
  branch: string | null;
  commit_sha: string | null;
  commit_url: string | null;
  author: string | null;
  pr_number: number | null;
  pr_url: string | null;
  policy_file: string;
  policy_id: string | null;
  change_type: string;
  old_hash: string | null;
  new_hash: string | null;
  conflict_status: string;
  duplicate_status: string;
  staleness_status: string;
  compliance_impact: string[];
  risk_score: number;
  reviewer_status: string;
  resolution_status: string;
  detail: string | null;
}

export interface LatestCommit {
  sha: string;
  url: string;
  message: string;
  author: string;
  date: string;
}

export interface RepoStatus {
  connector_id: string;
  name: string;
  repo: string | null;
  branch: string;
  path: string;
  status: string;
  last_sync: string | null;
  error_message: string | null;
  webhook_configured: boolean;
  webhook_events: string[];
  latest_commit: LatestCommit | null;
  policy_count: number;
}

export interface GithubStatus {
  connected: boolean;
  signature_verification: boolean;
  webhook_url: string;
  repositories: RepoStatus[];
  recent_changes: AuditEvent[];
  live_subscribers: number;
}

export interface PolicyVersion {
  id: string;
  policy_id: string;
  version: string;
  raw_text?: string;
  content_hash: string;
  created_at: string | null;
  size: number;
}

export interface Report {
  id: string;
  report_type: string;
  generated_at: string;
  generated_by: string;
  file_path: string;
  format: string;
  summary: Record<string, number>;
}

export interface TimelineEvent {
  id: string;
  at: string;
  kind: string;
  policy_id: string | null;
  title: string;
  detail: string | null;
}

export interface GraphPayload {
  mode: "POLICY" | "OBLIGATION";
  nodes: {
    id: string;
    type: string;
    position: { x: number; y: number };
    data: Record<string, any>;
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
    label: string;
    data: Record<string, any>;
  }[];
}

export interface ComplianceCoverage {
  frameworks: {
    framework: string;
    clauses: {
      clause: string;
      title: string;
      covered: boolean;
      policies: string[];
      findings: number;
    }[];
  }[];
  gaps: { topic: string; reason: string }[];
}
