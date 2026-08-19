"""Validate NMTC eligibility status across the pipeline."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS, ValidationResult
from nmtcapp.renderers._disclosure import join_truncated

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def check_eligibility(pipeline: "Pipeline") -> ValidationResult:
    """Verify all projects have eligibility data and flag any non-eligible ones.

    Issues (blocking):
    - Projects with ``is_nmtc_eligible = False``

    Warnings (non-blocking):
    - Projects not yet enriched (``is_nmtc_eligible = None``)
    - Projects in ineligible tracts but retained in pipeline
    - Pipeline below minimum distress threshold

    Example::

        result = check_eligibility(pipeline)
        print(result.summary())
    """
    projects = list(pipeline)
    issues: list = []
    warnings: list = []

    if not projects:
        issues.append("Pipeline is empty — no projects to check")
        return ValidationResult("eligibility_check", False, issues, warnings)

    not_enriched = [p for p in projects if not p.is_enriched]
    if not_enriched:
        warnings.append(
            f"{len(not_enriched)} project(s) lack eligibility data: "
            + join_truncated([p.project_id for p in not_enriched])
        )

    ineligible = [p for p in projects if p.is_nmtc_eligible is False]
    for p in ineligible:
        issues.append(
            f"Project {p.project_id} ({p.project_name}) is NOT NMTC-eligible "
            f"— tract {p.census_tract or 'unknown'} does not qualify as a LIC"
        )

    # `is True` / `is False`, never truthiness: an unverified project is None,
    # and counting None as ineligible reports "0% of QEI is in eligible tracts"
    # on a pipeline where nothing was checked. Verified and indeterminate QEI
    # are tracked separately so the percentage has an honest denominator.
    eligible_qei = sum(p.qei_request for p in projects if p.is_nmtc_eligible is True)
    unverified_qei = sum(p.qei_request for p in projects if p.is_nmtc_eligible is None)
    total_qei = sum(p.qei_request for p in projects)
    verified_qei = total_qei - unverified_qei
    if verified_qei > 0:
        elig_pct = eligible_qei / verified_qei
        if elig_pct < 0.90:
            unverified_note = (
                f" (of the {verified_qei / total_qei:.0%} of QEI that could be "
                f"verified; {unverified_qei / total_qei:.0%} is unverified)"
                if unverified_qei else ""
            )
            warnings.append(
                # D6 (1.2.2 round 2). This read "— CDFI Fund expects near-100%
                # eligibility": a bare Fund expectation with no citation,
                # sixteen lines above a warning in this same function that
                # carries a full FIX-3 disclosure. The file was half-swept in
                # 1.2.1 and this was the half left behind. Round 2 re-checked
                # the rest of the file: lines 1-62 and 72-104 attribute nothing
                # else, so this was the only one remaining.
                #
                # FIXED BY CITATION, NOT WITHDRAWN — the weakest of the six and
                # substantively right. "near-100%" appears in none of the three
                # primary documents, but the underlying constraint is statutory
                # rather than a scoring expectation, and stating it that way is
                # both true and more useful: it is a condition of the CREDIT,
                # not a competitive threshold a CDE can trade off.
                #
                # The 90% trigger is this tool's own and now says so. It is a
                # screening band, not a bar anyone publishes.
                f"Only {elig_pct:.0%} of verified QEI is in eligible tracts"
                f"{unverified_note}. Flagged at this tool's own 90% screening "
                "band — not a CDFI Fund threshold. What is federal here is "
                "structural, not a scoring expectation: IRC §45D(d) requires "
                "each QLICI to be made in a qualified active low-income "
                "community business, which must be located in a Low-Income "
                "Community, and Treas. Reg. §1.45D-1(c)(5)(i) requires "
                "substantially all — at least 85 percent — of QEI proceeds to "
                "be invested in QLICIs. QEI attributed to ineligible tracts "
                "cannot count toward that test"
            )
    elif total_qei > 0:
        warnings.append(
            "Tract eligibility could not be verified for any project — no "
            "eligibility percentage can be computed. This is not a finding of "
            "ineligibility; restore eligibility data access and re-run."
        )

    # Check distress concentration vs minimum threshold
    deep_qei = sum(
        p.qei_request for p in projects if p.distress_level in ("deep", "severe")
    )
    if total_qei > 0:
        deep_pct = deep_qei / total_qei
        min_thresh = TARGET_DISTRESS_THRESHOLDS["min_deep_distress"]
        if deep_pct < min_thresh:
            warnings.append(
                # FIX-3: the published bar named here is a share of QLICIs and
                # deep_pct is a share of QEI, so the two are not comparable and
                # the warning used to invite exactly that comparison — it named
                # the 85% with no denominator, two clauses after printing a QEI
                # share. The house-heuristic disclosure was already right; the
                # Fund figure beside it was the half that was missing its basis.
                f"Deep/severe distress concentration ({deep_pct:.0%} of QEI) is "
                f"below this tool's internal screening band of {min_thresh:.0%} "
                "(a house heuristic, not a CDFI Fund threshold). The published "
                "CY 2024-2025 severe-distress bar for full credit is 85% of "
                "QLICIs, which this tool does not compute — do not read the "
                "figure above as an answer to it"
            )

    passed = len(issues) == 0
    return ValidationResult("eligibility_check", passed, issues, warnings)
