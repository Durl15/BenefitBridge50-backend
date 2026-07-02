from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .claude_agent import generate_action_plan
from .database import init_db, list_assessments, load_assessment, save_assessment
from .eligibility import DISCLAIMER, run_benefit_screening
from .models import ActionPlanRequest, ActionPlanResponse, AssessmentInput, AssessmentRecord, AssessmentResponse
from .resources import OFFICIAL_RESOURCES

app = FastAPI(
    title="BenefitBridge 50+ API",
    version="1.0.0",
    description="AI-assisted benefits navigation and fraud-safe checklist API for adults 50+, caregivers, and community navigators.",
)

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Lightweight API-key guard --------------------------------------------
# Protects endpoints that write data or spend Claude/Anthropic credits from
# anonymous abuse. Set BENEFITBRIDGE_API_KEY in the environment; clients send
# it in the X-API-Key header. If unset, the guard is disabled (local dev).
_API_KEY = os.getenv("BENEFITBRIDGE_API_KEY", "").strip()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not _API_KEY:
        return  # dev mode: no key configured
    if not x_api_key or x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "BenefitBridge 50+", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/resources")
def resources() -> list[dict[str, str]]:
    return OFFICIAL_RESOURCES


@app.get("/api/assessments")
def recent_assessments(limit: int = 10) -> list[dict[str, object]]:
    records = list_assessments(limit)
    return [
        {
            "assessment_id": item.id,
            "created_at": item.created_at,
            "state": item.state,
            "county": item.county,
            "match_count": len(item.matches_json),
            "risk_flag_count": len(item.risk_flags_json),
        }
        for item in records
    ]


@app.post("/api/assessments", response_model=AssessmentResponse)
def create_assessment(payload: AssessmentInput, _: None = Depends(require_api_key)) -> AssessmentResponse:
    try:
        matches, risk_flags = run_benefit_screening(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    assessment_id = str(uuid.uuid4())
    alias_hash = hashlib.sha256(payload.user_alias.lower().encode("utf-8")).hexdigest()
    record = AssessmentRecord(
        id=assessment_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        user_alias_hash=alias_hash,
        state=payload.state,
        county=payload.county,
        input_json=payload.model_dump(exclude={"user_alias"}),
        matches_json=[match.model_dump() for match in matches],
        risk_flags_json=risk_flags,
    )
    save_assessment(record)
    return AssessmentResponse(assessment_id=assessment_id, matches=matches, risk_flags=risk_flags, disclaimer=DISCLAIMER)


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: str) -> AssessmentRecord:
    record = load_assessment(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return record


@app.post("/api/action-plan", response_model=ActionPlanResponse)
def action_plan(payload: ActionPlanRequest, _: None = Depends(require_api_key)) -> ActionPlanResponse:
    record = load_assessment(payload.assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return generate_action_plan(record, payload.reading_level, payload.language)


@app.get("/api/export/{assessment_id}")
def export_checklist(assessment_id: str, _: None = Depends(require_api_key)) -> dict[str, str]:
    record = load_assessment(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    plan = generate_action_plan(record)
    lines = [
        "# BenefitBridge 50+ Checklist",
        "",
        plan.summary,
        "",
        "## Checklist",
    ]
    lines.extend([f"- {item}" for item in plan.checklist])
    lines.append("\n## Official Links")
    lines.extend([f"- [{link['name']}]({link['url']})" for link in plan.official_links])
    lines.append("\n## Fraud Warnings")
    lines.extend([f"- {item}" for item in plan.fraud_warnings])
    lines.append(f"\n> {plan.disclaimer}")
    return {"assessment_id": assessment_id, "markdown": "\n".join(lines)}
