# Making the Problem Statement Self-Explanatory — Submission Format Recommendations

You already have (or are producing): the codebase + `README.md`, a detailed
PPT, a `HOW_TO_USE.md`, a demo video script, and an explainer video script.
Below are additional formats worth considering so a judge who only has 5
minutes can understand the project without reading code — roughly ordered by
effort-to-impact ratio.

## High impact, low effort

**One-page PDF summary ("one-pager").** A single page: problem (2 sentences),
solution (2 sentences), architecture diagram (thumbnail), the 5 success metrics
table from the SRS, and links to the repo/demo video/live deck. Judges often
screen dozens of submissions in seconds — this is the single highest-leverage
artifact after the demo video. You already have all the content in
`docs/SRS.md` §6; the `pdf` skill can produce this directly.

**Architecture / data-flow poster (single image, PNG/SVG).** One clean diagram
combining the system context, the AI pipeline (`parser → obligations →
conflicts/redundancy/staleness → graph → risk`), and the deployment shape
(Docker Compose). Useful standalone on a submission page and reusable inside
the PPT.

**Annotated screenshots folder.** 8–10 PNGs of the actual running console
(Overview, Conflict Compare, Graph, Staleness, Compliance, Reports) with 1-line
captions. Cheap to produce, and gives judges visual proof the product actually
runs — pairs well with the PPT and works even if they never watch the demo
video.

## Medium effort, strong differentiation

**Hosted/live demo link.** If the challenge platform allows it, deploy the
Docker Compose stack to a free-tier host (Render, Railway, Fly.io) so judges
can click through the real console themselves rather than only watching a
video. This is usually the single biggest differentiator in hackathon judging.

**Sample generated report (Markdown/HTML) committed to the repo.** Run
`POST /api/v1/reports` once and commit the actual output — e.g.
`sample_output/conflict_audit_report.html` — so judges see a real audit
artifact without running the stack themselves.

**Short written "judge FAQ" (`docs/FAQ.md` or a PPT appendix slide).**
Anticipate the 5 questions judges always ask: "what's actually AI here vs.
rules?", "does it scale beyond the seed data?", "what's stubbed vs. real?",
"how is this different from a linter/grep?", "what's the business case?" —
answer each in 2–3 sentences. This preempts the Q&A round and shows
self-awareness about scope (which is exactly what `docs/roadmap.md` already
does — just surface it more prominently).

## Optional / higher effort

**Interactive Jupyter/Colab notebook** walking through the deterministic AI
engine on the sample corpus (`parser → obligations → conflicts`) with printed
intermediate output — appeals to technical judges who want to see the
"reasoning," not just the UI, and reinforces the "explainable, not a black
box" claim.

**GitHub Pages / static landing page** built from the same content as the
one-pager, so the repo has a proper "front door" instead of just a README.
Low effort if you already have the one-pager copy.

**Badge row in `README.md`** (build passing, test count, license, tech stack)
— purely cosmetic but signals engineering maturity at a glance.

## What to skip

Given the scope of a hackathon submission, things like a full RBAC/multi-tenant
demo, a second live-hosted environment, or a fully voiced/edited 5+ minute
cinematic video are diminishing returns — the SRS itself already scopes these
as roadmap items, and over-investing in polish there takes time away from the
one-pager + live demo link, which judges actually weight most heavily.

## Suggested final zip / submission structure

```
submission/
├── README.md                       (already in repo)
├── HOW_TO_USE.md
├── Policy_Guardian_AI_Explanation.pptx
├── DEMO_VIDEO_SCRIPT.md
├── EXPLAINER_VIDEO_SCRIPT.md
├── SUBMISSION_FORMATS.md           (this file)
├── one_pager.pdf                   (recommended addition)
├── architecture_poster.png         (recommended addition)
└── screenshots/                    (recommended addition)
```
