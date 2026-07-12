# Demo Video Script — Policy Guardian AI

**Format:** live screen recording, single take preferred (record in segments and
cut together if easier). **Target length:** 3.5–4 minutes.
**Recording setup:** 1920×1080, browser at 100% zoom, `docker compose up --build`
already running with the seed corpus loaded before you hit record. Close extra
tabs/notifications. Use a clip-on or headset mic — audio quality matters more
than video quality for judges.

Each block below has: **[ON SCREEN]** what to show/click, **"VOICEOVER"** what to
say (read naturally, don't rush), and a **(time)** cue.

---

## 0:00–0:20 — Hook + problem

**[ON SCREEN]** Start on a plain slide or the README on GitHub — title
"Policy Guardian AI." Then cut to the two conflicting policy excerpts side by
side (screenshot or the actual markdown files):
`password_policy.md` Section 3.1 and `cloud_security_policy.md` Section 5.2.

**"VOICEOVER":**
> "Every large company has dozens of security policies, written by different
> teams, over different years. Here's a real example: one policy says 'rotate
> your password every 90 days.' Another says 'don't rotate passwords — MFA
> replaces that.' Nobody notices the contradiction until an auditor does. We
> built Policy Guardian AI to catch this automatically, continuously, before
> the auditor does."

---

## 0:20–0:45 — What it is, in one breath

**[ON SCREEN]** Navigate to `http://localhost:3000`, land on the Governance
Overview page. Let the governance gauge and severity chart render.

**"VOICEOVER":**
> "Policy Guardian AI ingests your whole policy corpus — from GitHub, a local
> folder, or manual upload — extracts every obligation, and detects conflicts,
> redundancy, and staleness. Every finding is explainable: it cites the exact
> triggering text and suggests a resolution. This is the Governance Overview —
> our seed corpus of 10 real-world-style policies is already scoring 69 out of
> 100, with 7 conflicts and 7 stale policies open."

---

## 0:45–1:45 — The core feature: Conflicts & Redundancies

**[ON SCREEN]** Click **Conflicts** in the sidebar. Show the filtered/sorted
list. Filter by Severity = HIGH. Click into the Password Policy ↔ Cloud
Security Policy conflict to open **Conflict Compare**.

**"VOICEOVER":**
> "This is the triage view — every conflict and redundancy, ranked by risk.
> Let's filter to HIGH severity. Here's that password rotation conflict I
> mentioned. Clicking in opens a side-by-side compare: the exact sentence from
> each policy is highlighted, the conflict type is labeled — this one's a
> STRENGTH conflict, one policy requires an action the other explicitly
> forbids — and it gives a suggested resolution: align both policies around
> the MFA-first standard. No black box. A compliance manager can see exactly
> why this fired and act on it in seconds."

---

## 1:45–2:15 — Policy Graph Explorer

**[ON SCREEN]** Click **Graph**. Show whole-policy mode, then toggle to
obligation-level mode. Hover/click a node with several edges (e.g. anything
touching "authentication").

**"VOICEOVER":**
> "Zooming out, the Graph Explorer shows the whole policy corpus as a network —
> which policies conflict, which overlap, which share a topic. Switching to
> obligation-level view breaks it down further, to the individual rule level.
> This is how a governance team spots a whole cluster of policies that all
> need coordinated review — not just one conflict at a time."

---

## 2:15–2:45 — Staleness Surveillance

**[ON SCREEN]** Click **Staleness**. Point out the SHA-1 deprecated-hash
finding on the Password Policy and its "last reviewed 2021" age badge.

**"VOICEOVER":**
> "Conflicts aren't the only risk — policies also just... age. The Password
> Policy here was last reviewed in 2021 and still references SHA-1 for
> password hashing, a deprecated algorithm. Policy Guardian flags review-
> overdue policies, deprecated tech references, superseded standards, and
> orphaned owners automatically, with a recommendation for each."

---

## 2:45–3:10 — Compliance Mapping + Reports

**[ON SCREEN]** Click **Compliance**, show ISO 27001 / NIST / GDPR / COBIT
coverage. Then click **Reports**, generate a Conflict Audit report as Markdown
or HTML, open the generated file briefly.

**"VOICEOVER":**
> "Every finding also maps to the compliance framework it affects — ISO 27001,
> NIST 800-53, GDPR, COBIT — so auditors get direct evidence, not just a
> dashboard. And everything exports as an audit-ready Markdown, HTML, or JSON
> report with one click."

---

## 3:10–3:35 — Live ingestion moment (the "wow")

**[ON SCREEN]** Go to **Policies → + Upload policy**. Paste a short policy with
a 60-day rotation rule (see snippet below). Submit. Show the new conflict
appear within seconds.

```
Title: Remote Access Policy
Owner: Infrastructure
Text: Section 1: All employees must rotate their passwords every 60 days.
```

**"VOICEOVER":**
> "And this isn't a static demo — let's add a brand-new policy live. I'll
> paste in a Remote Access Policy that requires a 60-day password rotation...
> and submit. Within seconds, Policy Guardian re-analyzes the whole corpus and
> — there it is — a new conflict against the existing 90-day rule, fully
> explained, no human had to spot it."

---

## 3:35–3:55 — Architecture + close

**[ON SCREEN]** Cut to the architecture diagram (from `docs/architecture.md`
or the PPT slide). Optionally show `/docs` Swagger UI for one second.

**"VOICEOVER":**
> "Under the hood, this is a deterministic, rule-driven NLP engine — no GPU, no
> model download, runs anywhere — wrapped in a FastAPI backend and a Next.js
> operations console, fully Dockerized with CI and 37 passing tests. It's
> built to collapse the twenty-plus hours compliance teams spend every quarter
> manually reconciling policies into a five-minute review of a ranked findings
> list. That's Policy Guardian AI."

**[ON SCREEN]** End card: project name, GitHub link, team name.

---

## Shot list checklist (for the editor)

- [ ] Hook: two conflicting policy excerpts (0:00)
- [ ] Governance Overview page load (0:20)
- [ ] Conflicts list → filter HIGH → Conflict Compare (0:45)
- [ ] Graph Explorer, both modes (1:45)
- [ ] Staleness page, SHA-1 finding (2:15)
- [ ] Compliance Mapping page (2:45)
- [ ] Reports page, generate + open a report (2:55)
- [ ] Live upload → new conflict appears (3:10)
- [ ] Architecture diagram + end card (3:35)

**Recording tips:** pre-load every page once before recording so there's no
loading-spinner dead air; keep the cursor movements deliberate and slow;
caption the video (auto-caption + manual cleanup) since many judges skim with
sound off.
