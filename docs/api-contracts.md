# API Contracts — Policy Guardian AI

> **Status:** FROZEN CONTRACT v1. Base path `/api/v1`. Every response is JSON.
> Agent D consumes these exact shapes; Agent B implements them; Agent C's engine
> feeds them. Entity field definitions live in `docs/data-dictionary.md`.

## Conventions
- Success: `200/201` with the resource or `{ items: [...], total: n }` for lists.
- Error: `{ error: { code, message, request_id } }` with appropriate 4xx/5xx.
- Every response header carries `X-Request-ID`.
- Pagination: `?limit=&offset=` (defaults 50/0).

---

## Health & meta
```
GET  /health           -> { status: "ok", version }
GET  /ready            -> { status: "ready", db, analysis_engine }
GET  /api/v1/meta      -> { topics[], conflict_types[], severities[], connectors[] }
```

## Dashboard
```
GET /api/v1/dashboard/overview
-> GovernanceScore   # see data-dictionary → GovernanceScore
```

## Policies
```
GET  /api/v1/policies?limit=&offset=&status=&topic=
-> { items: Policy[], total }

GET  /api/v1/policies/{id}
-> Policy & { obligations: Obligation[], conflicts: Conflict[], staleness: StalenessFinding[] }

POST /api/v1/policies/upload      (multipart or { title, raw_text, owner?, ... })
-> Policy                          # ingests + triggers analysis

DELETE /api/v1/policies/{id}      -> { deleted: true }
```

## Obligations
```
GET /api/v1/policies/{id}/obligations   -> { items: Obligation[], total }
```

## Findings (conflicts / redundancy / staleness)
```
GET /api/v1/conflicts?type=&severity=&policy_id=
-> { items: Conflict[], total }

GET /api/v1/conflicts/{id}
-> Conflict & { explanation_payload: ExplanationPayload }

GET /api/v1/redundancies            # conflicts filtered to REDUNDANCY|PARTIAL_REDUNDANCY
-> { items: Conflict[], total }

GET /api/v1/staleness?severity=
-> { items: StalenessFinding[], total }

GET /api/v1/review-queue            # unified, ranked by risk (severity × confidence × impact)
-> { items: ReviewItem[], total }
   ReviewItem = { id, kind: CONFLICT|STALE, severity, confidence, risk, title, policies[], summary }
```

## Graph
```
GET /api/v1/graph?mode=POLICY|OBLIGATION&topic=&policy_id=
-> GraphPayload      # React-Flow-ready; see data-dictionary → GraphPayload
```

## Timeline
```
GET /api/v1/timeline?limit=
-> { items: TimelineEvent[] }
   TimelineEvent = { id, at, kind: INGESTED|UPDATED|CONFLICT_FOUND|RESOLVED|SYNCED,
                     policy_id?, title, detail }
```

## Compliance mapping
```
GET /api/v1/compliance/coverage
-> { frameworks: [{ framework, clauses: [{ clause, title, covered: bool,
                                            policies[], findings[] }] }],
     gaps: [{ topic, reason }] }
```

## Connectors
```
GET  /api/v1/connectors                       -> { items: Connector[] }
POST /api/v1/connectors                       ({ type, name, config }) -> Connector
POST /api/v1/connectors/{id}/sync             -> { job_id, status }
GET  /api/v1/connectors/{id}/health           -> { status, last_sync, error_message }
```

## Webhooks
```
POST /api/v1/webhooks/register   ({ connector_id, event_types[] }) -> { id, secret_ref, url }
POST /api/v1/webhooks/{connector}    (raw provider payload)        -> { received: true, event_id }
GET  /api/v1/webhooks/events?status=                               -> { items: WebhookEvent[] }
```

## Analysis
```
POST /api/v1/analysis/run    ({ policy_ids?: [] })   # omit -> whole corpus
-> { run_id, counts: { conflicts, redundancies, stale, obligations }, governance: GovernanceScore }
```

## Reports
```
POST /api/v1/reports    ({ report_type, format })
-> Report
GET  /api/v1/reports                 -> { items: Report[] }
GET  /api/v1/reports/{id}/download   -> file stream (Content-Disposition attachment)
```

---

## Shared payload: ExplanationPayload  (Agent C → B → D)
```
ExplanationPayload = {
  title: string,
  why_flagged: string,
  trigger_terms: string[],
  spans: [{ policy_id, section, quote, highlight: [start, end][] }],
  sections_involved: string[],
  likely_resolution: string,
  compliance_refs: string[],
  confidence: float
}
```

## Shared payload: sample webhook (GitHub push, normalized)
```
POST /api/v1/webhooks/github
{
  "ref": "refs/heads/main",
  "repository": { "full_name": "acme/security-policies" },
  "commits": [{ "modified": ["policies/password_policy.md"], "added": [], "removed": [] }]
}
-> { received: true, event_id: "whk_...", affected_paths: ["policies/password_policy.md"] }
```
