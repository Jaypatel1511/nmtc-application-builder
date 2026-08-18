"""Validate completeness of application data (CDE profile + pipeline)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import REQUIRED_PROJECT_FIELDS, ValidationResult

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

# READ THE LIST, DO NOT RETYPE IT (FIX-2 G-5).
#
# This was the THIRD hand-maintained copy of the same eight field names, after
# core/cde._FIELD_GUIDANCE and the `required` set inside CDEProfile.from_yaml.
# Measured on the branch head: deleting "governance" from this list passed all
# 955 tests. A required field stopped being validated and no gate saw it,
# because every gate that could have compared the lists was itself reading one
# of them. Second live instance of M5's class, after the pipeline columns
# consistency_check retyped.
#
# The import is the fix: there is now one list, and this module has no opinion
# about its contents.
from nmtcapp.core.cde import (
    CDE_FIELDS_WHERE_EMPTY_IS_AN_ANSWER as _EMPTY_IS_AN_ANSWER,
    REQUIRED_CDE_FIELDS as _REQUIRED_CDE_FIELDS,
)


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
    # AN EMPTY VALUE IS NOT ALWAYS A MISSING ONE (1.3.0 B3).
    #
    # This loop rejected `val == []` for every required field, including
    # prior_awards — which the shipped scaffold explicitly instructs a CDE to
    # leave as [], and which CDEProfile.from_yaml has always accepted as []. So
    # a first-time CDE following the template loaded cleanly and was then told
    # its profile was missing prior NMTC allocations: a scored track-record
    # item, with the obvious remedy being to invent one.
    #
    # from_yaml knew this and this module did not, because the exception was a
    # local literal in from_yaml. It is now one importable constant that both
    # read. See core/cde.CDE_FIELDS_WHERE_EMPTY_IS_AN_ANSWER.
    for field in _REQUIRED_CDE_FIELDS:
        val = getattr(cde, field, None)
        if field in _EMPTY_IS_AN_ANSWER:
            if val is None:
                issues.append(f"CDE profile missing required field: {field}")
            continue
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
