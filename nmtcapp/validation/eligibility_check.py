"""Validate NMTC eligibility status across the pipeline."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS, ValidationResult

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
            + ", ".join(p.project_id for p in not_enriched[:5])
        )

    ineligible = [p for p in projects if p.is_nmtc_eligible is False]
    for p in ineligible:
        issues.append(
            f"Project {p.project_id} ({p.project_name}) is NOT NMTC-eligible "
            f"— tract {p.census_tract or 'unknown'} does not qualify as a LIC"
        )

    eligible_qei = sum(p.qei_request for p in projects if p.is_nmtc_eligible)
    total_qei = sum(p.qei_request for p in projects)
    if total_qei > 0:
        elig_pct = eligible_qei / total_qei
        if elig_pct < 0.90:
            warnings.append(
                f"Only {elig_pct:.0%} of QEI is in eligible tracts — "
                "CDFI Fund expects near-100% eligibility"
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
                f"Deep/severe distress concentration ({deep_pct:.0%}) is below "
                f"the competitive minimum of {min_thresh:.0%}"
            )

    passed = len(issues) == 0
    return ValidationResult("eligibility_check", passed, issues, warnings)
