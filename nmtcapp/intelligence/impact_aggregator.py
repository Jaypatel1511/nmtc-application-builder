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
    - ``total_units_built`` – sum of housing/mixed-use units
    - ``total_sq_ft`` – sum of commercial/facility sq ft
    - ``total_qei`` – sum of QEI requested
    - ``cost_per_job`` – total project cost per job created
    - ``qei_per_job`` – QEI dollars per job created
    - ``jobs_per_million_qei`` – jobs created per $1MM QEI
    - ``projects_with_units`` – count of housing projects

    Example::

        result = aggregate_impact(pipeline)
        print(f"Total jobs: {result['total_jobs_created']:,}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_impact_result()

    total_jobs_created = sum(p.expected_jobs_created for p in projects)
    total_jobs_retained = sum(p.expected_jobs_retained for p in projects)
    total_units = sum(p.expected_units_built or 0 for p in projects)
    total_sq_ft = sum(p.expected_sq_ft or 0.0 for p in projects)
    total_qei = sum(p.qei_request for p in projects)
    total_cost = sum(p.total_project_cost for p in projects)
    projects_with_units = sum(1 for p in projects if p.expected_units_built)

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
        "projects_with_units": projects_with_units,
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
        "total_units_built": 0,
        "total_sq_ft": 0.0,
        "total_qei": 0.0,
        "total_project_cost": 0.0,
        "cost_per_job": 0.0,
        "qei_per_job": 0.0,
        "jobs_per_million_qei": 0.0,
        "projects_with_units": 0,
    }
