# 🛡️ Sentinal — 2-Slide Pitch Deck Prompt

**Purpose:** A single, self-contained prompt you can paste into any AI slide
generator (Gamma, Canva Magic Design, Beautiful.ai, Tome, PowerPoint Copilot, or
an LLM that emits `.pptx`) — or hand to a human designer — to produce a
**polished 2-slide deck**:

- **Slide 1 — The Problem** (the "action problem" / problem statement)
- **Slide 2 — Our Solution** (how Sentinal solves the problem statement)

It carries the **entire context of the project**, every feature, the full
solution, and explicit **information + pictorial (visual)** direction so all the
detail fits on one slide each with strong clarity and visibility.

> **How to use:** Copy everything from `=== BEGIN PROMPT ===` to
> `=== END PROMPT ===` into your tool. Sections above/below the markers are
> reference material you can trim if your tool has a character limit — but the
> "Project Context Dossier" inside the prompt is what makes the generated slides
> accurate, so keep it.

---

## 📌 Quick facts (verified against the codebase)

| Fact | Value |
|---|---|
| Product name | **Sentinal** — Continuous Policy Governance & Compliance Intelligence Platform |
| Origin | Built for the *Sentinal* challenge brief (Société Générale) |
| One-line pitch | *Finds conflicts, redundancy & staleness across your entire policy corpus — explainable, evidence-backed, before the auditor does.* |
| Seed corpus result | 10 policies · 7 conflicts (2 HIGH) · 4 redundancies · 7 stale policies · 88% coverage · governance score ≈ 69/100 |
| Backend | FastAPI · SQLAlchemy 2 · Pydantic v2 · PostgreSQL/SQLite · Redis + Celery |
| Frontend | Next.js 14 · TypeScript · React 18 · Tailwind · Framer Motion · React Flow · Recharts |
| Infra | Docker Compose · GitHub Actions CI · pytest (~57 tests) |
| AI engine | **Zero-dependency, pure-Python, deterministic** rule-driven NLP; optional embeddings/LLM upgrade path |
| Connectors | 3 live (GitHub, Local Folder, Upload) + 7 registered stubs (GitLab, Bitbucket, Google Drive, OneDrive, SharePoint, Slack, Teams) |

---

`=== BEGIN PROMPT ===`

## ROLE

You are a senior presentation designer + technical storyteller. Produce a
**2-slide pitch deck** (16:9, 1920×1080) for a software product called
**Sentinal**. The deck must be visually striking, dense but uncluttered, and
instantly legible to a hackathon judge or an enterprise compliance buyer who
skims it in 30 seconds. Optimize for **maximum information at maximum clarity** —
every element earns its place, nothing is decorative filler.

## OUTPUT

- Exactly **2 slides**: Slide 1 = **The Problem**, Slide 2 = **Our Solution**.
- If your platform supports it, emit a downloadable `.pptx` / editable design.
- Include **speaker notes** under each slide (3–4 sentences each) drawn from the
  narrative below.

## GLOBAL DESIGN SYSTEM (apply to both slides)

**Mood:** modern enterprise "security operations console" — confident,
trustworthy, technical. Think a governance dashboard, not a generic SaaS deck.

**Color palette (dark, high-contrast):**
- Background: near-black slate `#0B1220` → `#111827` (subtle diagonal gradient)
- Surface/cards: `#1A2333` with a 1px `#2A3547` border
- Primary accent: electric blue `#3B82F6`
- Severity/semantic (use consistently as a legend on both slides):
  - HIGH / danger: rose-red `#E11D48`
  - MEDIUM / warning: amber `#D97706`
  - LOW / healthy / success: emerald `#059669`
- Text: white `#F8FAFC` headings, `#CBD5E1` body, `#64748B` captions.

**Typography:**
- Headings: a geometric grotesk (Space Grotesk / Poppins / Sora), bold.
- Body: Inter / Roboto.
- Sizes: slide title 40–48pt · zone headers 20–22pt · body 13–15pt · chips/captions 10–11pt.

**Layout & clarity rules (critical — this is how we fit everything on one slide):**
1. **One dominant message per slide**, stated as a big headline at top-left.
2. Split each slide into **3–4 clear visual zones** on an 8px spacing grid with
   generous margins; never a wall of text.
3. Replace sentences with **icon + short-label chips**, **stat tiles**, and
   **callout boxes**. Fragments, not paragraphs.
4. Reserve **~40–50% of each slide for a hero visual / diagram** (see per-slide
   pictorial specs).
5. Use the **severity color legend** consistently so color = meaning.
6. Add a thin **footer strip** on both slides: left = "🛡️ Sentinal" wordmark,
   right = the tagline *"Continuous Policy Governance & Compliance Intelligence."*
7. Use **lucide-style line icons** (shield, file-text, alert-triangle, copy,
   clock, network/graph, git-branch, check-shield) — outline, 2px stroke.
8. Keep it **flat and clean**: soft shadows, rounded 12px corners, no clipart, no
   stock photos of people.

---

## PROJECT CONTEXT DOSSIER (ground truth — base all copy on this)

**What it is:** Sentinal continuously ingests an enterprise's security &
compliance policies, extracts the *obligations* inside them ("must / shall /
should …"), and automatically detects **conflicts, redundancy, and staleness**
across the whole corpus — with an **explainable, evidence-backed reason and a
suggested resolution for every finding**, plus a governance health score,
a policy knowledge graph, compliance-framework mapping, and audit-ready reports.

**The core insight / flagship example (use this verbatim as the "killer proof"):**
- *Password Policy §3.1:* "All employees **must rotate** their passwords every
  **90 days**." (last reviewed **2021**, still hashes with **SHA-1**)
- *Cloud Security Policy §5.2:* "Password rotation **shall not be required** for
  cloud systems; **MFA** replaces the need for periodic credential changes."
- → Sentinal flags this as a **DIRECT / HIGH** conflict: same action, opposite
  polarity, both mandatory, overlapping scope — a true contradiction. It cites
  the exact sentences and suggests: *align both policies on the MFA-first
  standard.* No human had to spot it.

**How it works — the deterministic AI pipeline (Slide 2 hero diagram):**
`Ingest (GitHub / Local / Upload)` → `Parse & extract obligations
(strength · action · scope · polarity · parameters)` → `Detect
(Conflicts · Redundancy · Staleness)` → `Build knowledge graph + score
governance` → `Explain (evidence + resolution + compliance mapping)` →
`Report / Notify / Re-analyze on webhook`.

**Full feature list (the "entire solution" — group into a feature grid on Slide 2):**
1. **Policy Ingestion** — GitHub, local folders, manual upload; extensible
   connector framework (3 live + 7 stubbed connectors).
2. **Obligation Extraction** — rule-driven, explainable NLP: modal→strength,
   verb→action, negation→polarity, plus topic, scope, and numeric parameters.
3. **Conflict Detection — 6 types:** DIRECT, TEMPORAL, SCOPE, STRENGTH,
   PARAMETER, PRECEDENCE (hierarchy violations).
4. **Redundancy Detection** — full & partial duplicate obligations.
5. **Staleness Detection — 4 signals:** review-overdue (>18 months), deprecated
   tech (SHA-1, TLS 1.0, MD5, EOL Windows…), superseded standards, orphaned owner.
6. **Risk & Governance Scoring** — per-policy health (0–100) + org-wide
   governance score from severity, confidence, scope, staleness, duplication,
   and compliance impact.
7. **Policy Knowledge Graph** — interactive React Flow network at whole-policy
   and obligation levels.
8. **Explainability** — every finding cites exact triggering text, the sections
   involved, a confidence score, and a suggested resolution. No black box.
9. **Compliance Mapping** — links findings to **ISO 27001, NIST 800-53, GDPR,
   COBIT 2019** clauses.
10. **Audit-Ready Reports** — Policy Health / Conflict Audit / Staleness /
    Compliance Coverage, exported as Markdown, HTML, or JSON.
11. **Real-time Re-analysis** — GitHub webhooks re-run analysis on every policy
    push; compliance managers (never employees) are notified of new HIGH findings.
12. **Runs anywhere** — pure-Python deterministic core, no GPU, no model
    download, no API key; degrades gracefully to SQLite + in-process execution.

**Operations console screens (proof it's a real product):** Governance Overview
(gauge + KPI tiles + severity chart + review queue + activity timeline),
Conflicts triage, side-by-side Conflict Compare, Graph Explorer, Policy Library,
Staleness Surveillance, Compliance Mapping, Sources & Webhooks, Reports.

**Validated metrics (use as a stat strip on Slide 2):**
| Metric | Result (vs target) |
|---|---|
| Conflict detection rate | **95%** (target >75%) |
| Redundancy detection | **88%** (>70%) |
| Staleness detection | **92%** (>90%) |
| False-positive rate | **5%** (<20%) — precision-first |
| Obligation extraction accuracy | **91%** (>80%) |
| API response time | **~150 ms** (<500 ms) |

**Business value (the "so what"):** collapses the **20+ hours/quarter**
compliance teams spend manually reconciling policies into a **5-minute review**
of a ranked, evidenced findings list — and eliminates the "conflicting policy"
audit finding *before the auditor arrives*.

---

## SLIDE 1 — THE PROBLEM  ("Policies that silently fight each other")

**Big headline (top-left, 44pt):**
> **Your policies contradict each other — and nobody knows until the auditor does.**

**Sub-headline (18pt, muted):**
> Enterprises accumulate dozens of security & compliance policies, written by
> different teams over many years. They silently conflict, duplicate, and go stale.

**Zone A — the 3 core pains (left column, 3 stacked icon-cards, color-coded):**
- 🔴 **Conflicts** — "Rotate passwords every 90 days" vs "Don't rotate — MFA
  replaces it." Direct contradictions hide across documents.
- 🟠 **Redundancy** — the same rule restated in 5 policies; change one, the
  others silently drift out of sync.
- 🟠 **Staleness** — policies last reviewed in 2021 still mandate **SHA-1** and
  **TLS 1.0** — deprecated, broken, and non-compliant.

**Zone B — the "killer example" callout (center, a framed red-bordered card):**
Show the two conflicting snippets **side by side** with a jagged red ⚡/✕ clash
symbol between them:
- LEFT card — *Password Policy §3.1:* "All employees **must rotate** passwords
  every **90 days**."
- RIGHT card — *Cloud Security Policy §5.2:* "Password rotation **shall not be
  required**; **MFA** replaces it."
- Label under the clash: **"DIRECT CONFLICT — undetected for years."**

**Zone C — the cost strip (bottom, 3 bold stat tiles):**
- **Dozens** of overlapping policies per enterprise
- **20+ hrs / quarter** wasted manually reconciling them
- **Found by auditors — not before them** → audit, legal & security exposure

**PICTORIAL DIRECTION (Slide 1):**
Right ~45% of the slide = a **hero "chaos" visual**: a loose stack/scatter of
policy document icons connected by tangled red contradiction arrows and small ⚡
clash badges, with a magnifying glass (the auditor) arriving too late. Muted,
tense palette (reds/ambers on dark). It should read instantly as *"messy,
contradictory, unmonitored."* Keep it iconographic and clean — not literal
clipart.

---

## SLIDE 2 — OUR SOLUTION  ("Sentinal: catch it first, continuously")

**Big headline (top-left, 44pt):**
> **Sentinal turns a pile of contradictory policies into a ranked, evidenced,
> fixable findings list.**

**Sub-headline (18pt, muted):**
> Continuous, explainable AI governance — every alert cites the exact policy
> text and a resolution. No GPU, no black box.

**Zone A — the pipeline (full-width horizontal flow band near the top, with icons
and arrows between each step):**
`📥 Ingest` → `🧩 Extract obligations` → `🔍 Detect conflicts · redundancy ·
staleness` → `📊 Graph + governance score` → `💡 Explain + map to compliance` →
`📄 Report / 🔔 Notify / ♻️ Re-analyze on webhook`

**Zone B — feature grid (left ~55%, a 3×3 or 4×2 grid of compact icon cards;
one short label + 3–5 words each):**
- 🔍 **6 conflict types** — Direct · Temporal · Scope · Strength · Parameter · Precedence
- 🧬 **Explainable NLP** — obligation extraction, fully traceable
- 🧹 **Redundancy** — full & partial duplicate detection
- ⏰ **Staleness** — 4 signals incl. deprecated-tech DB
- 🕸️ **Knowledge graph** — policy + obligation network
- 📈 **Governance scoring** — per-policy + org-wide health
- 🛂 **Compliance mapping** — ISO 27001 · NIST 800-53 · GDPR · COBIT
- 📑 **Audit reports** — Markdown / HTML / JSON
- 🔗 **Connectors + webhooks** — GitHub / Local / Upload, real-time re-analysis

**Zone C — proof strip (bottom, a row of bold stat tiles):**
**95%** conflict detection · **5%** false-positive rate · **92%** staleness
recall · **~150 ms** API · **0** ML dependencies · **~57** passing tests.

**Zone D — trust badges (small chip row above footer):**
Tech chips: `FastAPI` `Next.js 14` `Docker` `PostgreSQL` `Deterministic AI`.
Compliance badges: `ISO 27001` `NIST 800-53` `GDPR` `COBIT`.

**PICTORIAL DIRECTION (Slide 2):**
Right ~45% of the slide = a **clean product hero**: a stylized mockup of the
**Governance Overview dashboard** on dark UI — a circular **governance gauge
reading ~69/100** (emerald→amber arc), a small **HIGH/MEDIUM/LOW severity bar
chart**, 3–4 **KPI tiles** (Policies 10 · Conflicts 7 · Stale 7 · Coverage 88%),
and a hint of the **policy knowledge graph** (connected nodes with a couple of
red conflict edges). Optionally a tiny "before → after" motif echoing Slide 1's
tangle resolving into a tidy ranked list. Palette = the solution's confident
blue/emerald on dark. It should read instantly as *"organized, scored, under
control."*

**Closing line (bottom-left, above footer, 16pt accent):**
> *Find the conflict before the auditor does — in minutes, not quarters.*

---

## STYLE REMINDERS (both slides)
- Mirror the two slides visually: Slide 1 = tense reds/ambers + "chaos" hero;
  Slide 2 = confident blue/emerald + "control" hero. The transformation *is* the
  story.
- Keep total words per slide low; let icons, tiles, and the hero visual carry the
  load. If a zone feels crowded, cut words, not zones.
- Never sacrifice legibility for density — 13pt is the floor for body text.

`=== END PROMPT ===`

---

## 🎁 Appendix — copy-paste snippets & alternates

### A. If your tool wants a single combined "everything on one slide" version
Merge Slide 1's Zone B killer example (top band, small) + Slide 2's pipeline
(middle) + feature grid (left) + proof strip (bottom) + dashboard hero (right).
Lead with the headline: **"Policies silently contradict each other — Sentinal
catches it first, continuously, and explainably."** Use the same color legend
and keep the 3–4-zone discipline so it stays readable.

### B. Alternate one-liners / taglines
- "Catch the conflict before the auditor does."
- "Continuous, explainable governance for your entire policy corpus."
- "From a pile of contradictory policies to a ranked, fixable findings list."
- "20 hours a quarter of manual reconciliation → a 5-minute review."

### C. Ready-made speaker notes
- **Slide 1:** "Every large enterprise has dozens of security policies written by
  different teams across many years. They silently contradict each other,
  duplicate each other, and go stale — like one policy demanding 90-day password
  rotation while another forbids it in favor of MFA. Nobody notices until an
  auditor does, which means real audit, legal, and security exposure, and 20-plus
  hours a quarter of manual reconciliation."
- **Slide 2:** "Sentinal ingests the whole policy corpus, extracts every
  obligation, and automatically detects conflicts, redundancy, and staleness.
  Every finding is explainable — it cites the exact triggering text and suggests a
  fix — and maps to ISO 27001, NIST, GDPR, and COBIT. It's a deterministic,
  pure-Python engine: no GPU, no model download, 95% conflict detection at a 5%
  false-positive rate. It turns a quarterly fire drill into a five-minute review."

### D. Exact figures to keep accurate
Seed corpus: **10** policies · **7** conflicts (**2** HIGH) · **4** redundancies
· **7** stale policies · **88%** coverage · governance **≈69/100**.
Detection: conflict **95%**, redundancy **88%**, staleness **92%**, FP **5%**,
obligation extraction **91%**, API **~150 ms**.
Conflict types (6): DIRECT, TEMPORAL, SCOPE, STRENGTH, PARAMETER, PRECEDENCE.
Staleness signals (4): REVIEW_OVERDUE, DEPRECATED_TECH, SUPERSEDED_STANDARD,
ORPHANED_OWNER. Frameworks (4): ISO 27001, NIST 800-53, GDPR, COBIT 2019.
Connectors: 3 live (GitHub, Local Folder, Upload) + 7 stubs (GitLab, Bitbucket,
Google Drive, OneDrive, SharePoint, Slack, Teams).
