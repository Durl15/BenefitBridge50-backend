from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic

from .models import ActionPlanResponse, AssessmentRecord

DISCLAIMER = (
    "This plan is educational and preparatory. It does not confirm eligibility and does not provide legal, financial, medical, or tax advice. "
    "Use official program websites or trusted counselors before submitting applications."
)

FRAUD_WARNINGS = [
    "Do not pay an upfront fee to apply for public benefits.",
    "Do not share Social Security, Medicare, or bank information with unsolicited callers, texts, emails, or unofficial websites.",
    "Start from official government, AARP, NCOA, or local Area Agency on Aging links when applying.",
]


def _fallback_plan(record: AssessmentRecord) -> ActionPlanResponse:
    matches = record.matches_json
    primary_names = [m["program_name"] for m in matches[:4]]
    checklist: list[str] = [
        "Print or save this BenefitBridge 50+ checklist before opening application websites.",
        "Gather photo ID, proof of address, proof of income, rent or mortgage amount, utility bills, and insurance or Medicare information if applicable.",
        "Use only official links from the resource list below.",
    ]
    for match in matches:
        checklist.append(f"Review {match['program_name']}: {match['next_steps'][0]}")

    summary = (
        "Based on the information provided, BenefitBridge 50+ found likely next-step programs to review: "
        + ", ".join(primary_names)
        + ". These are screening suggestions, not final eligibility decisions."
    )
    official_links = [{"name": m["program_name"], "url": m["official_url"]} for m in matches]
    return ActionPlanResponse(
        assessment_id=record.id,
        summary=summary,
        checklist=checklist,
        official_links=official_links,
        fraud_warnings=FRAUD_WARNINGS,
        disclaimer=DISCLAIMER,
        ai_generated=False,
    )


def generate_action_plan(record: AssessmentRecord, reading_level: str = "plain", language: str = "en") -> ActionPlanResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_plan(record)

    matches = record.matches_json
    official_links = [{"name": m["program_name"], "url": m["official_url"]} for m in matches]
    client = Anthropic(api_key=api_key)
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
    prompt = {
        "assessment_id": record.id,
        "reading_level": reading_level,
        "language": language,
        "matches": matches,
        "risk_flags": record.risk_flags_json,
        "rules": [
            "Do not invent eligibility requirements.",
            "Do not ask for Social Security numbers, Medicare IDs, bank information, document uploads, or diagnosis details.",
            "Do not claim the user is eligible; say programs are worth checking.",
            "Use plain, respectful language for adults 50+ and caregivers.",
            "Return exactly five checklist items, using only the provided official links and match reasons."
        ]
    }
    message = client.messages.create(
        model=model,
        max_tokens=900,
        temperature=0.2,
        system="You create safe, plain-language benefits navigation action plans. You explain structured screening results without adding new eligibility facts.",
        messages=[{"role": "user", "content": f"Create a concise BenefitBridge 50+ action plan from this JSON: {prompt}"}],
    )
    text = "\n".join(block.text for block in message.content if getattr(block, "type", "") == "text").strip()
    if not text:
        return _fallback_plan(record)

    checklist = [line.strip("-• 1234567890. ") for line in text.splitlines() if line.strip()][:5]
    if len(checklist) < 3:
        fallback = _fallback_plan(record)
        fallback.summary = text
        fallback.ai_generated = True
        return fallback

    return ActionPlanResponse(
        assessment_id=record.id,
        summary=text.splitlines()[0] if text.splitlines() else text,
        checklist=checklist,
        official_links=official_links,
        fraud_warnings=FRAUD_WARNINGS,
        disclaimer=DISCLAIMER,
        ai_generated=True,
    )
