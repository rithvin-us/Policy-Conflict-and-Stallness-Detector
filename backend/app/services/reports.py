"""Audit-ready report generation.

Produces policy-health, conflict-audit, staleness, and compliance-coverage
reports as Markdown / HTML / JSON artifacts written to ``REPORT_DIR``. Reports are
self-contained evidence a compliance manager can attach to an audit file.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ids import new_id
from app.models import Conflict, Policy, Report, StalenessFinding
from app.services.analysis import latest_run

_SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _policy_titles(db: Session) -> dict[str, str]:
    return {p.id: p.title for p in db.query(Policy).all()}


def _build_markdown(db: Session, report_type: str) -> tuple[str, dict]:
    titles = _policy_titles(db)
    run = latest_run(db)
    gov = run.governance if run else {}
    lines: list[str] = [f"# Sentinal — {report_type.replace('_', ' ').title()} Report",
                        "", f"_Generated: {_now()}_", ""]
    summary: dict = {}

    if gov:
        lines += ["## Governance Snapshot", "",
                  f"- **Overall governance score:** {gov.get('overall')}/100",
                  f"- **Average policy health:** {gov.get('policy_health')}/100",
                  f"- **Conflict pressure:** {gov.get('conflict_pressure')}",
                  f"- **Staleness index:** {gov.get('staleness_index')}",
                  f"- **Topic coverage:** {gov.get('coverage')}%", ""]
        summary = dict(gov.get("counts", {}))

    if report_type in ("POLICY_HEALTH", "CONFLICT_AUDIT"):
        conflicts = sorted(db.query(Conflict).all(),
                           key=lambda c: (_SEV_ORDER.get(c.severity, 3), -c.risk))
        lines += ["## Conflicts & Redundancies", ""]
        if not conflicts:
            lines.append("_No conflicts detected._")
        for c in conflicts:
            a = titles.get(c.policy_a_id, c.policy_a_id)
            b = titles.get(c.policy_b_id, c.policy_b_id)
            lines += [
                f"### [{c.severity}] {c.conflict_type} — {a} ↔ {b}",
                f"- **Explanation:** {c.explanation}",
                f"- **Confidence:** {c.confidence:.0%} | **Risk:** {c.risk}",
            ]
            if c.scope_analysis:
                lines.append(f"- **Scope analysis:** {c.scope_analysis}")
            lines += [f"- **Resolution:** {c.resolution_suggestion}",
                      f"- **Compliance impact:** {', '.join(c.compliance_impact or [])}",
                      ""]

    if report_type in ("POLICY_HEALTH", "STALENESS"):
        stale = sorted(db.query(StalenessFinding).all(),
                       key=lambda s: (_SEV_ORDER.get(s.severity, 3), -s.risk))
        lines += ["## Staleness Findings", ""]
        if not stale:
            lines.append("_No stale policies detected._")
        for s in stale:
            p = titles.get(s.policy_id, s.policy_id)
            lines += [
                f"### [{s.severity}] {s.stale_reason} — {p}",
                f"- **Evidence:** {'; '.join(s.evidence or [])}",
                f"- **Recommendation:** {s.recommendation}", ""]

    if report_type == "COMPLIANCE_COVERAGE":
        lines += ["## Compliance Coverage", "",
                  "See `/api/v1/compliance/coverage` for the live framework map.", ""]

    return "\n".join(lines), summary


def _markdown_to_html(md: str) -> str:
    body = html.escape(md).replace("\n", "<br>\n")
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>Sentinal Report</title>"
            f"<style>body{{font-family:ui-sans-serif,system-ui;max-width:820px;"
            f"margin:40px auto;color:#111;line-height:1.5}}</style></head>"
            f"<body>{body}</body></html>")


def generate_report(db: Session, report_type: str, fmt: str,
                    generated_by: str = "system") -> Report:
    report_type = report_type.upper()
    fmt = fmt.upper()
    md, summary = _build_markdown(db, report_type)

    rid = new_id("rpt")
    ext = {"MARKDOWN": "md", "HTML": "html", "JSON": "json"}.get(fmt, "md")
    path = settings.REPORT_DIR / f"{rid}.{ext}"

    if fmt == "HTML":
        path.write_text(_markdown_to_html(md), encoding="utf-8")
    elif fmt == "JSON":
        path.write_text(json.dumps(
            {"report_type": report_type, "generated_at": _now(),
             "summary": summary, "markdown": md}, indent=2), encoding="utf-8")
    else:
        path.write_text(md, encoding="utf-8")

    report = Report(id=rid, report_type=report_type, generated_by=generated_by,
                    file_path=str(path), format=fmt, summary=summary)
    db.add(report)
    db.commit()
    return report
