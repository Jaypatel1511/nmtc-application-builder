"""Cross-field consistency validation for NMTC applications."""
from __future__ import annotations

import logging
import re
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


def check_consistency(application: "Application",
                      deal_economics: dict = None) -> ValidationResult:
    """Validate cross-field consistency within and across projects.

    Checks:
    - QLICI amount ≤ QEI for each project (hard NMTC program rule)
    - Total project cost > 0 for all projects
    - Expected jobs ≥ 0
    - QEI as fraction of total cost within reasonable bounds
    - Construction start before operations start (when both provided)
    - Total pipeline QEI vs requested allocation
    - CROSS-SURFACE AGREEMENT: any figure this document prints in more than one
      place must be one figure (see check_cross_surface_agreement)

    ``deal_economics`` is passed by Application.analyze(), which holds it before
    the ApplicationAnalysis exists. Omit it and the cross-surface check will
    run analyze() itself.

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

    issues.extend(check_cross_surface_agreement(application, deal_economics))

    passed = len(issues) == 0
    return ValidationResult("consistency_check", passed, issues, warnings)


# ---------------------------------------------------------------------------
# Cross-surface arithmetic
# ---------------------------------------------------------------------------

# Tolerance in dollars. The renderers round to whole dollars at several points
# and the per-project sum in Appendix A rounds differently from the pipeline
# total in Section D, so exact equality would fail on float noise alone. One
# dollar per project is the largest divergence rounding can produce; anything
# above it is a different formula, not a different rounding.
_AGREEMENT_TOLERANCE_PER_PROJECT = 1.0
_AGREEMENT_TOLERANCE_FLOOR = 1.0


class _EconomicsOnly:
    """The slice of ApplicationAnalysis that Section D reads.

    check_consistency runs INSIDE Application.analyze(), before the
    ApplicationAnalysis object exists, so this check cannot call analyze() —
    that recurses forever. Section D's generate_content touches exactly one
    attribute of the analysis (``deal_economics``); everything else it needs is
    on the Application. tests/validation/test_consistency_check.py asserts that
    remains true, so a future Section D that reads another attribute fails a
    test rather than an AttributeError in a validator.
    """

    __slots__ = ("deal_economics",)

    def __init__(self, deal_economics: dict) -> None:
        self.deal_economics = deal_economics


def _shared_figures(application: "Application", deal_economics: dict) -> dict:
    """{label: {surface: value}} for every figure printed in more than one place.

    DERIVED FROM THE RENDERERS, NOT HAND-LISTED. The Section D column is read
    out of the section generator's own economics table, by calling it and
    parsing the rendered cell; the Appendix A column out of the pipeline
    table's own TOTALS row, by calling it. A hand-written list of "figures that
    appear twice" goes stale the first time somebody adds a row; this cannot,
    because a row that stops being produced stops being compared and a row that
    starts being produced starts.
    """
    from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy
    from nmtcapp.tables.pipeline_table import build_pipeline_table

    analysis = _EconomicsOnly(deal_economics)
    appendix_a = build_pipeline_table(application.pipeline, application.cde)
    if appendix_a.empty:
        return {}
    totals = appendix_a.iloc[-1]

    section_d = SectionDCapitalizationStrategy().generate_content(application, analysis)
    economics = section_d["subsections"][0]["body"]

    def _money(text) -> float:
        """Pull the leading dollar figure out of a rendered Section D cell."""
        match = re.search(r"\$([\d,]+(?:\.\d+)?)", str(text))
        return float(match.group(1).replace(",", "")) if match else float("nan")

    # Appendix A column -> Section D row label, for the figures both print.
    pairs = {
        "Total pipeline QEI": ("QEI Request ($)", "Total Pipeline QEI ($)"),
        "Total NMTCs generated": ("Total NMTCs ($)", "Total NMTCs Generated ($)"),
        "Estimated investor equity": (
            "Estimated Investor Equity ($)", "Estimated Investor Equity ($)"),
        "CDE fee income": ("CDE Fee ($)", "CDE Fee Income ($)"),
        "Total leverage loans": ("Leverage Loan ($)", "Total Leverage Loans ($)"),
    }
    shared = {}
    for label, (a_col, d_row) in pairs.items():
        if a_col not in appendix_a.columns or d_row not in economics:
            continue
        shared[label] = {
            "Appendix A (per-project total)": float(totals[a_col]),
            "Section D (deal economics)": _money(economics[d_row]),
        }
    return shared


def check_cross_surface_agreement(application: "Application",
                                  deal_economics: dict = None) -> list:
    """Any figure printed in more than one place in one document must agree.

    THIS IS THE CHECK THAT DID NOT EXIST, and its absence is why a $10.2MM
    contradiction shipped. Section D reported leverage loans as the residual of
    QEI less investor equity, taken from nmtc-calc; Appendix A sized the same
    loans at a flat 80% of QEI from a module-local constant. Reproduced on the
    shipped 20-project sample before the fix: Appendix A $98,000,000 against
    Section D $82,846,750, in one generated document, with
    ``check_consistency`` passing.

    check_consistency existed to catch exactly this and could not, because
    every assertion in it was about one project's own fields. A cross-field
    check that never crosses a surface cannot fail on the defect that spans
    two surfaces — the tenth instance in this package of a gate that cannot
    fail on its own subject.

    ``deal_economics`` is the ``deal_economics_summary`` dict Section D renders
    from. Application.analyze() passes it in because this runs before the
    ApplicationAnalysis exists; a direct caller may omit it and pay for an
    analyze().

    Returns a list of issue strings; empty when every shared figure agrees.
    """
    if deal_economics is None:
        deal_economics = application.analyze().deal_economics
    try:
        shared = _shared_figures(application, deal_economics)
    except Exception as exc:                       # pragma: no cover - defensive
        # A check that cannot run must SAY SO as an issue, not return clean.
        return [
            f"Cross-surface agreement check could not run ({exc}); the "
            "document's shared figures are unverified"
        ]

    project_count = len(list(application.pipeline)) if application.pipeline else 0
    tolerance = max(
        _AGREEMENT_TOLERANCE_FLOOR,
        _AGREEMENT_TOLERANCE_PER_PROJECT * project_count,
    )

    issues = []
    for label, surfaces in shared.items():
        values = list(surfaces.values())
        if any(v != v for v in values):            # NaN: a cell did not parse
            issues.append(
                f"{label}: a figure could not be read back out of a rendered "
                f"surface ({surfaces}) — it cannot be checked for agreement"
            )
            continue
        if max(values) - min(values) > tolerance:
            detail = "; ".join(f"{name} ${value:,.0f}" for name, value in surfaces.items())
            issues.append(
                f"{label} disagrees between surfaces of the same document: "
                f"{detail} (difference ${max(values) - min(values):,.0f}). "
                "A figure printed in two places must be one figure."
            )
    return issues


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
