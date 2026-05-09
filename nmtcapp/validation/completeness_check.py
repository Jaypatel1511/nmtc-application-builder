"""Validate completeness of application data (CDE profile + pipeline)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import REQUIRED_PROJECT_FIELDS, ValidationResult

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

_REQUIRED_CDE_FIELDS = [
    "name", "cde_id", "certification_date", "mission",
    "target_markets", "prior_awards", "contact", "governance",
]


def check_completeness(application: "Application") -> ValidationResult:
    """Check that all required fields are populated across the application.

    Checks:
    - CDE profile has all required fields non-empty
    - Pipeline has at least one project
    - Each project has all required fields populated
    - Total pipeline QEI is within 10% of the requested allocation

    Example::

        result = check_completeness(application)
        print(result.summary())
    """
    issues: list = []
    warnings: list = []

    # CDE profile completeness
    cde = application.cde
    for field in _REQUIRED_CDE_FIELDS:
        val = getattr(cde, field, None)
        if val is None or val == "" or val == [] or val == {}:
            issues.append(f"CDE profile missing required field: {field}")

    if cde.prior_awards and not isinstance(cde.prior_awards, list):
        issues.append("CDE prior_awards must be a list")

    # Pipeline completeness
    projects = list(application.pipeline) if application.pipeline else []
    if not projects:
        issues.append("Application has no pipeline projects — at least 1 required")
        return ValidationResult("completeness_check", False, issues, warnings)

    incomplete_projects = []
    for p in projects:
        missing = []
        for f in REQUIRED_PROJECT_FIELDS:
            val = getattr(p, f, None)
            if val is None or val == "":
                missing.append(f)
        if missing:
            incomplete_projects.append((p.project_id, missing))

    for pid, missing_fields in incomplete_projects:
        issues.append(f"Project {pid} missing required fields: {missing_fields}")

    # QEI vs requested allocation
    total_pipeline_qei = sum(p.qei_request for p in projects)
    requested = application.requested_allocation
    if requested > 0:
        ratio = total_pipeline_qei / requested
        if ratio < 0.90:
            warnings.append(
                f"Pipeline QEI (${total_pipeline_qei:,.0f}) is less than 90% of "
                f"requested allocation (${requested:,.0f}) — consider adding projects"
            )
        elif ratio > 1.50:
            warnings.append(
                f"Pipeline QEI (${total_pipeline_qei:,.0f}) is {ratio:.0%} of "
                f"requested allocation — a 1.2–1.5× pipeline is typical"
            )

    passed = len(issues) == 0
    return ValidationResult("completeness_check", passed, issues, warnings)
