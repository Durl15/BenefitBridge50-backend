from __future__ import annotations

from .models import AssessmentInput, BenefitMatch
from .resources import RESOURCE_BY_CODE

DISCLAIMER = (
    "BenefitBridge 50+ is an educational navigation tool. It does not make final eligibility "
    "decisions and does not provide legal, financial, medical, or tax advice. Use official "
    "program websites or a trusted benefits counselor before applying."
)


def _match(code: str, confidence: str, reason: str, next_steps: list[str]) -> BenefitMatch:
    resource = RESOURCE_BY_CODE[code]
    return BenefitMatch(
        code=code,
        program_name=resource["program_name"],
        category=resource["category"],
        confidence=confidence,  # type: ignore[arg-type]
        reason=reason,
        next_steps=next_steps,
        official_url=resource["official_url"],
    )


def income_ratio(monthly_income: int, household_size: int) -> float:
    # Conservative national screening proxy for MVP triage, not a final eligibility test.
    baseline = 1580 + max(household_size - 1, 0) * 550
    return monthly_income / baseline if baseline else 999.0


def run_benefit_screening(data: AssessmentInput) -> tuple[list[BenefitMatch], list[str]]:
    if not data.consent_to_process:
        raise ValueError("Consent is required before BenefitBridge 50+ can process an assessment.")

    matches: list[BenefitMatch] = []
    risk_flags: list[str] = []
    ratio = income_ratio(data.monthly_income, data.household_size)

    if data.food_insecurity or ratio <= 1.65:
        matches.append(_match(
            "SNAP",
            "High" if data.food_insecurity and ratio <= 1.65 else "Medium",
            "Food support may be worth checking because the household reported food strain or income near common screening thresholds.",
            [
                "Use the official USDA state directory to reach the correct state SNAP application page.",
                "Gather proof of identity, address, household income, rent or mortgage, utilities, and medical costs if applicable.",
                "Ask a local Area Agency on Aging, library, or trusted nonprofit for application support if the form feels difficult."
            ],
        ))

    if data.age >= 65 and ratio <= 1.45:
        matches.append(_match(
            "SSI",
            "Medium",
            "SSI may be relevant for older adults with very limited income and resources. BenefitBridge does not screen assets, so official review is required.",
            [
                "Review the Social Security Administration SSI page before sharing personal information.",
                "Prepare income, resource, living arrangement, and citizenship or eligible-status information.",
                "Do not provide your Social Security number to unofficial websites or callers."
            ],
        ))

    if data.medicare_status in {"enrolled", "approaching", "unknown"} and ratio <= 1.75:
        matches.append(_match(
            "MSP",
            "High" if data.medicare_status == "enrolled" and ratio <= 1.45 else "Medium",
            "Medicare Savings Programs may help with premiums or cost sharing for Medicare beneficiaries with limited income.",
            [
                "Review the official Medicare Savings Programs page.",
                "Contact the State Health Insurance Assistance Program or state Medicaid office for exact rules.",
                "Prepare Medicare card information only on official government pages or with trusted counselors."
            ],
        ))

    if data.utility_help_needed or data.housing_status in {"rent_burdened", "risk_of_eviction", "unhoused"}:
        matches.append(_match(
            "LIHEAP",
            "Medium",
            "Utility or housing pressure suggests home energy assistance may be worth checking.",
            [
                "Use the HHS LIHEAP page to locate the state office.",
                "Gather recent utility bills, proof of income, address, and household information.",
                "Apply through official state or local agencies, not paid lead-generation sites."
            ],
        ))

    if data.housing_status in {"rent_burdened", "risk_of_eviction", "unhoused"}:
        matches.append(_match(
            "HUD-HOUSING",
            "Medium",
            "Housing burden or eviction risk makes HUD rental assistance and housing counseling a relevant next step.",
            [
                "Review HUD rental assistance and housing counseling resources.",
                "Contact the local public housing authority or HUD-approved counselor.",
                "Ask for written confirmation before paying any housing-placement or application-related fee."
            ],
        ))

    if data.caregiving_role != "none" or data.disability_status or data.age >= 60:
        matches.append(_match(
            "ELDERCARE",
            "High",
            "The Eldercare Locator can connect older adults and caregivers to Area Agencies on Aging and local services.",
            [
                "Use the official Eldercare Locator to find local aging-services contacts.",
                "Ask about benefits counseling, transportation, meals, caregiving respite, and legal assistance.",
                "Bring the BenefitBridge checklist to the call or appointment."
            ],
        ))

    matches.append(_match(
        "BCU",
        "High",
        "BenefitsCheckUp is a recognized benefits screening resource for older adults and people with disabilities.",
        [
            "Use BenefitsCheckUp as a second-pass screening resource.",
            "Compare any results with official state and federal application sites.",
            "Save a copy of the checklist before beginning applications."
        ],
    ))

    matches.append(_match(
        "FRAUD-WATCH",
        "High",
        "Benefit applications can attract impostor websites, calls, and messages. Fraud prevention guidance is relevant for every user.",
        [
            "Do not pay an upfront fee to apply for public benefits.",
            "Do not share Social Security, Medicare, or bank information with unsolicited callers or texts.",
            "Use AARP Fraud Watch Network guidance if a benefit-related message feels suspicious."
        ],
    ))

    if data.monthly_income == 0:
        risk_flags.append("Income entered as $0. Confirm whether this reflects current monthly income or missing information.")
    if data.housing_status in {"unhoused", "risk_of_eviction"}:
        risk_flags.append("Housing instability reported. Prioritize local emergency housing and legal-aid resources.")
    if data.food_insecurity:
        risk_flags.append("Food insecurity reported. Prioritize food assistance and local meal resources.")
    if data.veteran_status:
        risk_flags.append("Veteran status reported. Consider checking VA, state veterans affairs, and county veteran-service offices.")

    return matches, risk_flags
