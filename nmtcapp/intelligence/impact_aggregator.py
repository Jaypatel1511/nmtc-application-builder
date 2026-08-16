"""Aggregate impact projections across the pipeline."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def aggregate_impact(pipeline: "Pipeline") -> dict:
    """Aggregate community impact projections across all pipeline projects.

    Returns a dict with:
    - ``total_jobs_created`` – sum of expected direct job creation
    - ``total_jobs_retained`` – sum of expected job retention
    - ``total_jobs`` – created + retained
    - ``total_units_built`` – sum of housing/mixed-use units over the projects
      that SUPPLIED a figure, or ``None`` when no project supplied one
    - ``total_sq_ft`` – sum of commercial/facility sq ft over the projects that
      supplied a figure, or ``None`` when no project supplied one
    - ``total_qei`` – sum of QEI requested
    - ``cost_per_job`` – total project cost per job created
    - ``qei_per_job`` – QEI dollars per job created
    - ``jobs_per_million_qei`` – jobs created per $1MM QEI
    - ``projects_reporting_units`` – count of projects that supplied a units
      figure at all, a supplied 0 included
    - ``projects_with_units`` – count of projects whose supplied units are > 0
    - ``projects_reporting_sq_ft`` – count of projects that supplied a sq ft
      figure at all

    A SUPPLIED ZERO AND AN ABSENT VALUE ARE NOT THE SAME AND MUST NOT SUM THE
    SAME (1.2.1 B-2). ``sum(p.expected_units_built or 0 …)`` returned 0 for
    both, and Section B rendered it as "0 affordable or mixed-income housing
    units developed" — a claim about the pipeline — over a column no CDE had
    filled in, while Appendix A of the same document printed "—" for every one
    of those cells. renderers/_cell_format states the rule this violated, in
    code added in the same release: "numeric: '0 affordable units' is a claim,
    '—' is not."

    ``None`` rather than a sentinel so a consumer that formats it without
    thinking raises instead of printing a number nobody supplied.

    Example::

        result = aggregate_impact(pipeline)
        print(f"Total jobs: {result['total_jobs_created']:,}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_impact_result()

    total_jobs_created = sum(p.expected_jobs_created for p in projects)
    total_jobs_retained = sum(p.expected_jobs_retained for p in projects)
    # Sum over what was SUPPLIED; None when nothing was. `is not None` rather
    # than truthiness on purpose — a CDE that types 0 has answered the
    # question, and that answer must survive to the page.
    supplied_units = [p.expected_units_built for p in projects
                      if p.expected_units_built is not None]
    supplied_sq_ft = [p.expected_sq_ft for p in projects
                      if p.expected_sq_ft is not None]
    total_units = sum(supplied_units) if supplied_units else None
    total_sq_ft = float(sum(supplied_sq_ft)) if supplied_sq_ft else None
    total_qei = sum(p.qei_request for p in projects)
    total_cost = sum(p.total_project_cost for p in projects)
    projects_reporting_units = len(supplied_units)
    projects_with_units = sum(1 for u in supplied_units if u > 0)
    projects_reporting_sq_ft = len(supplied_sq_ft)

    cost_per_job = (total_cost / total_jobs_created) if total_jobs_created > 0 else 0.0
    qei_per_job = (total_qei / total_jobs_created) if total_jobs_created > 0 else 0.0
    jobs_per_million = (total_jobs_created / (total_qei / 1_000_000)) if total_qei > 0 else 0.0

    return {
        "total_jobs_created": total_jobs_created,
        "total_jobs_retained": total_jobs_retained,
        "total_jobs": total_jobs_created + total_jobs_retained,
        "total_units_built": total_units,
        "total_sq_ft": total_sq_ft,
        "total_qei": total_qei,
        "total_project_cost": total_cost,
        "cost_per_job": round(cost_per_job),
        "qei_per_job": round(qei_per_job),
        "jobs_per_million_qei": round(jobs_per_million, 2),
        "projects_reporting_units": projects_reporting_units,
        "projects_with_units": projects_with_units,
        "projects_reporting_sq_ft": projects_reporting_sq_ft,
    }


# ``vs_historical_benchmarks`` / ``_benchmark_label`` were REMOVED in 1.2.0.
# Third instance of the same shape, after distress_analysis._assess_vs_winners
# and sector_analysis._assess_vs_winners — and the only one that reached a
# submitted document. It rendered into Section B, the scored Community
# Outcomes section:
#
#     • 7.0 jobs per $1MM of QEI deployed (average vs. CDFI Fund historical
#       average)
#
# Two independent reasons, either sufficient:
#
# 1. A THRESHOLD CANNOT YIELD A QUARTILE. The function returned the literal
#    "top_quartile" from a single >= comparison against one number. No
#    distribution of anything is loaded. That is the reasoning that removed
#    _assess_vs_winners, and it holds whatever the number turns out to be.
#
# 2. PROVENANCE. IMPACT_BENCHMARKS (data/schema.py) carries a section comment,
#    not a citation, and this package's own historical_awards.py says its
#    winner-pattern figures are approximations because application-level
#    microdata is not public.
#
# _empty_impact_result() also returned "below_average" for a pipeline with zero
# projects — a tier assigned where nothing was measured.
#
# jobs_per_million_qei itself is KEPT. It is computed from the CDE's own inputs
# and is a fact about this pipeline. Only the comparative label goes: Section B
# now reports the number without ranking it.


def _empty_impact_result() -> dict:
    return {
        "total_jobs_created": 0,
        "total_jobs_retained": 0,
        "total_jobs": 0,
        # An empty pipeline supplied nothing, so these are absent, not zero —
        # the same distinction the populated path now makes.
        "total_units_built": None,
        "total_sq_ft": None,
        "total_qei": 0.0,
        "total_project_cost": 0.0,
        "cost_per_job": 0.0,
        "qei_per_job": 0.0,
        "jobs_per_million_qei": 0.0,
        "projects_reporting_units": 0,
        "projects_with_units": 0,
        "projects_reporting_sq_ft": 0,
    }
