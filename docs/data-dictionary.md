# Sentinal — Data Dictionary

> **Status:** FROZEN CONTRACT v1. Owned by Agent A. Agents B, C, D must not add,
> rename, or retype fields without an explicit contract-change note in their
> handoff. This document is the single source of truth for every entity in the
> system. The Pydantic schemas in `backend/app/schemas/` and the TypeScript
> types in `frontend/lib/types.ts` are generated to match this file exactly.

## Conventions

- All IDs are strings. Persisted entities use `ULID`-style prefixes
  (`pol_`, `obl_`, `cfl_`, `stf_`, `con_`, `whk_`, `rpt_`) so IDs are
  self-describing in logs and URLs.
- All timestamps are ISO-8601 UTC strings (`2024-11-20T00:00:00Z`).
- All enums are UPPER_SNAKE_CASE strings, never integers, so payloads are
  human-readable in audit logs.
- Money/score fields are integers 0–100 unless stated otherwise.

---

## Entity: Policy

The top-level governed document.

| Field | Type | Notes |
|---|---|---|
| `id` | string | `pol_*` |
| `title` | string | Human title, e.g. "Password Policy" |
| `source` | string | Connector origin: `local:seed`, `github:org/repo`, `upload` |
| `owner` | string | Owning team, e.g. "IT Security" |
| `author` | string \| null | Last known author handle |
| `version` | string | Policy version label, e.g. "2.1" |
| `status` | `PolicyStatus` | See enum |
| `last_reviewed` | date | Drives staleness |
| `created_at` | datetime | First ingest |
| `updated_at` | datetime | Last change |
| `tags` | string[] | Topic tags |
| `content` | string | Rendered/normalized markdown |
| `raw_text` | string | Verbatim ingested text |
| `summary` | string \| null | AI or author summary |
| `health_score` | int 0–100 | Derived, see Risk Scoring |
| `obligation_count` | int | Derived count |

`PolicyStatus = ACTIVE | DRAFT | DEPRECATED | ARCHIVED`

---

## Entity: Obligation

An atomic requirement extracted from a policy section.

| Field | Type | Notes |
|---|---|---|
| `id` | string | `obl_*` |
| `policy_id` | string | FK → Policy |
| `section` | string \| null | e.g. "3.1" |
| `topic` | `Topic` | Normalized topic |
| `action` | string | Normalized verb lemma, e.g. `rotate`, `encrypt`, `retain` |
| `scope` | `Scope` | Whom/what it applies to |
| `strength` | `Strength` | Obligation strength |
| `polarity` | `Polarity` | AFFIRM (do X) or NEGATE (do not X) |
| `parameters` | object | Extracted params, e.g. `{"duration_days": 90, "min_length": 12}` |
| `evidence_text` | string | Source sentence |
| `confidence` | float 0–1 | Extraction confidence |

```
Topic     = PASSWORD | ENCRYPTION | ACCESS_CONTROL | AUTHENTICATION |
            DATA_RETENTION | DATA_CLASSIFICATION | NETWORK | LOGGING |
            BACKUP | INCIDENT_RESPONSE | GENERAL
Strength  = MANDATORY | RECOMMENDED | OPTIONAL   # must/shall > should > may
Polarity  = AFFIRM | NEGATE
Scope     = { kind: ALL | ROLE | SYSTEM | GEO | SERVICE,
              value: string,           # "all_employees", "developers", "cloud", "eu"
              raw: string }            # source phrase
```

---

## Entity: Conflict

A detected contradiction between two obligations (or their parent policies).

| Field | Type | Notes |
|---|---|---|
| `id` | string | `cfl_*` |
| `policy_a_id` | string | FK → Policy |
| `policy_b_id` | string | FK → Policy |
| `obligation_a_id` | string \| null | FK → Obligation |
| `obligation_b_id` | string \| null | FK → Obligation |
| `conflict_type` | `ConflictType` | See enum |
| `severity` | `Severity` | HIGH / MEDIUM / LOW |
| `explanation` | string | NL description |
| `evidence` | `Evidence` | Both trigger spans |
| `confidence` | float 0–1 | Detector confidence |
| `scope_analysis` | string \| null | Why scope narrows/negates the conflict |
| `resolution_suggestion` | string | Harmonization guidance |
| `compliance_impact` | string[] | e.g. `["ISO 27001 A.5.1", "NIST IA-5"]` |

```
ConflictType = DIRECT | TEMPORAL | SCOPE | STRENGTH | PARAMETER |
               PARTIAL_REDUNDANCY | REDUNDANCY
Severity     = HIGH | MEDIUM | LOW
Evidence     = { a: { policy_id, section, quote },
                 b: { policy_id, section, quote },
                 trigger_terms: string[] }
```

> Note: `REDUNDANCY` / `PARTIAL_REDUNDANCY` are carried on the Conflict entity
> (not a separate table) because they share the pairwise obligation-comparison
> shape. The UI filters by `conflict_type` to render the "Duplicates" panel.

---

## Entity: StalenessFinding

| Field | Type | Notes |
|---|---|---|
| `id` | string | `stf_*` |
| `policy_id` | string | FK → Policy |
| `stale_reason` | `StaleReason` | See enum |
| `severity` | `Severity` | |
| `evidence` | string[] | Trigger phrases / dates |
| `recommendation` | string | |
| `age_months` | int \| null | Months since `last_reviewed` |

```
StaleReason = REVIEW_OVERDUE | DEPRECATED_TECH | SUPERSEDED_STANDARD |
              ORPHANED_OWNER | NO_VERSION_HISTORY
```

---

## Entity: Connector

| Field | Type | Notes |
|---|---|---|
| `id` | string | `con_*` |
| `type` | `ConnectorType` | |
| `name` | string | Display name |
| `status` | `ConnectorStatus` | |
| `last_sync` | datetime \| null | |
| `error_message` | string \| null | |
| `config` | object | Type-specific (path, repo, token ref — secrets never returned) |

```
ConnectorType   = GITHUB | GITLAB | BITBUCKET | GOOGLE_DRIVE | ONEDRIVE |
                  SHAREPOINT | SLACK | TEAMS | LOCAL_FOLDER | UPLOAD
ConnectorStatus = CONNECTED | SYNCING | ERROR | DISCONNECTED | NOT_CONFIGURED
```

Implemented in this build: `GITHUB`, `LOCAL_FOLDER`, `UPLOAD`. All others are
registered in the `ConnectorManager` registry as `NOT_CONFIGURED` stubs behind
the same `BaseConnector` interface (see architecture.md → Connector Framework).

---

## Entity: WebhookEvent

| Field | Type | Notes |
|---|---|---|
| `id` | string | `whk_*` |
| `source` | `ConnectorType` | Origin |
| `event_type` | string | e.g. `push`, `policy.updated` |
| `payload` | object | Raw event body (redacted secrets) |
| `received_at` | datetime | |
| `processed_at` | datetime \| null | |
| `status` | `WebhookStatus` | |

`WebhookStatus = RECEIVED | PROCESSING | PROCESSED | FAILED | IGNORED`

---

## Entity: Report

| Field | Type | Notes |
|---|---|---|
| `id` | string | `rpt_*` |
| `report_type` | `ReportType` | |
| `generated_at` | datetime | |
| `generated_by` | string | User / "system" |
| `file_path` | string | Server path to artifact |
| `format` | `ReportFormat` | |
| `summary` | object | Headline counts embedded for list views |

```
ReportType   = POLICY_HEALTH | CONFLICT_AUDIT | STALENESS | COMPLIANCE_COVERAGE
ReportFormat = MARKDOWN | JSON | HTML
```

---

## Derived: GovernanceScore (dashboard headline)

Not persisted as a row; computed by the risk engine and returned by
`GET /api/v1/dashboard/overview`.

```
GovernanceScore = {
  overall: int 0-100,
  policy_health: int 0-100,
  conflict_pressure: int 0-100,   # inverse — higher is worse, UI shows as risk
  staleness_index: int 0-100,
  coverage: int 0-100,
  trend: [{ date, overall }],     # for the sparkline
  counts: { policies, conflicts, redundancies, stale, obligations }
}
```

---

## Derived: GraphPayload (React Flow contract)

```
GraphPayload = {
  mode: "POLICY" | "OBLIGATION",
  nodes: [{ id, type, position:{x,y}, data:{ label, kind, health?, topic?, severity? } }],
  edges: [{ id, source, target, label, data:{ relation, severity?, confidence? } }]
}
relation = CONFLICT | REDUNDANT | RELATED | BELONGS_TO
```

This is the exact shape React Flow consumes — Agent D renders it without
transformation.
