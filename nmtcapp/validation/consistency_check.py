"""Cross-field consistency validation for NMTC applications."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import ValidationResult

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

# Rough cost-per-sq-ft bounds by project type for sanity checking
_COST_PER_SQFT_BOUNDS = {
    "real_estate":        (50,   600),   # $50–$600/sq ft
    "operating_business": (0,    100),   # lower capital intensity
    "mixed_use":          (100,  600),
}

# QEI as fraction of total project cost — typical NMTC range
_QEI_COVERAGE_BOUNDS = (0.30, 0.95)


def check_consistency(application: "Application") -> ValidationResult:
    """Validate cross-field consistency within and across projects.

    Checks:
    - QLICI amount ≤ QEI for each project (hard NMTC program rule)
    - Total project cost > 0 for all projects
    - Expected jobs ≥ 0
    - QEI as fraction of total cost within reasonable bounds
    - Construction start before operations start (when both provided)
    - Total pipeline QEI vs requested allocation

    Example::

        result = check_consistency(application)
        print(result.summary())
    """
    issues: list = []
    warnings: list = []

    projects = list(application.pipeline) if application.pipeline else []
    if not projects:
        warnings.append("No projects to validate — add pipeline projects")
        return ValidationResult("consistency_check", True, issues, warnings)

    for p in projects:
        pid = p.project_id

        # QLICI must not exceed QEI — CDFI Fund hard rule
        if p.qlici_amount > p.qei_request:
            issues.append(
                f"Project {pid}: QLICI amount (${p.qlici_amount:,.0f}) exceeds "
                f"QEI (${p.qei_request:,.0f}) — not permitted"
            )

        # QEI as fraction of total cost
        if p.total_project_cost > 0:
            coverage = p.qei_request / p.total_project_cost
            lo, hi = _QEI_COVERAGE_BOUNDS
            if coverage < lo:
                warnings.append(
                    f"Project {pid}: QEI ({coverage:.0%} of project cost) seems low — "
                    f"typical NMTC deals are {lo:.0%}–{hi:.0%}"
                )
            elif coverage > hi:
                warnings.append(
                    f"Project {pid}: QEI ({coverage:.0%} of project cost) is very high — "
                    f"review leverage structure"
                )
        else:
            issues.append(f"Project {pid}: total_project_cost must be > 0")

        # Jobs must be non-negative
        if p.expected_jobs_created < 0:
            issues.append(f"Project {pid}: expected_jobs_created must be ≥ 0")
        if p.expected_jobs_retained < 0:
            issues.append(f"Project {pid}: expected_jobs_retained must be ≥ 0")

        # Date consistency
        if p.construction_start and p.operations_start:
            if p.construction_start > p.operations_start:
                warnings.append(
                    f"Project {pid}: construction_start ({p.construction_start}) "
                    f"is after operations_start ({p.operations_start})"
                )

        # Geographic claim consistency — if enriched and state doesn't match
        if p.census_tract and len(p.census_tract) >= 2:
            # FIPS prefix: first 2 digits of tract = state FIPS
            # We do a basic state FIPS check for a few states
            state_fips = _STATE_FIPS.get(p.state.upper())
            if state_fips and not p.census_tract.startswith(state_fips):
                warnings.append(
                    f"Project {pid}: census tract {p.census_tract} may not match "
                    f"state {p.state} (expected FIPS prefix {state_fips})"
                )

    # Pipeline QEI sum vs allocation
    total_qei = sum(p.qei_request for p in projects)
    requested = application.requested_allocation
    if requested > 0 and total_qei > 0:
        ratio = total_qei / requested
        if ratio < 1.0:
            warnings.append(
                f"Total pipeline QEI (${total_qei:,.0f}) is below the requested "
                f"allocation (${requested:,.0f}) — pipeline undersized"
            )

    passed = len(issues) == 0
    return ValidationResult("consistency_check", passed, issues, warnings)


# State abbreviation → FIPS code prefix (2-digit)
_STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11",
}
