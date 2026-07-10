"""Analysis + report endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Report
from app.schemas import AnalysisRunRequest, ReportCreateRequest, report_to_dict
from app.services.analysis import run_analysis
from app.services.reports import generate_report

router = APIRouter()

_REPORT_TYPES = {"POLICY_HEALTH", "CONFLICT_AUDIT", "STALENESS", "COMPLIANCE_COVERAGE"}
_FORMATS = {"MARKDOWN", "HTML", "JSON"}


@router.post("/analysis/run")
def analysis_run(body: AnalysisRunRequest | None = None,
                 db: Session = Depends(get_db)) -> dict:
    run = run_analysis(db, policy_ids=body.policy_ids if body else None)
    return {"run_id": run.id, "counts": run.counts, "governance": run.governance}


@router.post("/reports", status_code=201)
def create_report(body: ReportCreateRequest, db: Session = Depends(get_db)) -> dict:
    if body.report_type.upper() not in _REPORT_TYPES:
        raise HTTPException(400, f"Unknown report_type: {body.report_type}")
    if body.format.upper() not in _FORMATS:
        raise HTTPException(400, f"Unknown format: {body.format}")
    report = generate_report(db, body.report_type, body.format, body.generated_by)
    return report_to_dict(report)


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Report).order_by(Report.generated_at.desc()).all()
    return {"items": [report_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/reports/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(404, f"Report {report_id} not found")
    media = {"MARKDOWN": "text/markdown", "HTML": "text/html",
             "JSON": "application/json"}.get(report.format, "text/plain")
    filename = f"{report.report_type.lower()}_{report.id}.{report.format.lower()}"
    return FileResponse(report.file_path, media_type=media, filename=filename)
