from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


class AssessmentInput(BaseModel):
    user_alias: str = Field(min_length=2, max_length=80)
    age: int = Field(ge=50, le=120)
    state: str = Field(min_length=2, max_length=2)
    county: str | None = Field(default=None, max_length=80)
    household_size: int = Field(ge=1, le=12)
    monthly_income: int = Field(ge=0, le=50000)
    housing_status: Literal["stable", "rent_burdened", "unhoused", "risk_of_eviction", "homeowner"]
    food_insecurity: bool
    medicare_status: Literal["not_enrolled", "enrolled", "approaching", "unknown"]
    disability_status: bool
    veteran_status: bool
    caregiving_role: Literal["none", "caregiver", "care_recipient", "both"]
    utility_help_needed: bool = False
    consent_to_process: bool

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("user_alias")
    @classmethod
    def normalize_alias(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("Alias is required.")
        return cleaned


class BenefitMatch(BaseModel):
    code: str
    program_name: str
    category: str
    confidence: Literal["High", "Medium", "Low"]
    reason: str
    next_steps: list[str]
    official_url: str


class AssessmentResponse(BaseModel):
    assessment_id: str
    matches: list[BenefitMatch]
    risk_flags: list[str]
    disclaimer: str


class ActionPlanRequest(BaseModel):
    assessment_id: str
    reading_level: Literal["plain", "detailed"] = "plain"
    language: Literal["en", "es"] = "en"


class ActionPlanResponse(BaseModel):
    assessment_id: str
    summary: str
    checklist: list[str]
    official_links: list[dict[str, str]]
    fraud_warnings: list[str]
    disclaimer: str
    ai_generated: bool


class AssessmentRecord(BaseModel):
    id: str
    created_at: str
    user_alias_hash: str
    state: str
    county: str | None
    input_json: dict[str, Any]
    matches_json: list[dict[str, Any]]
    risk_flags_json: list[str]
