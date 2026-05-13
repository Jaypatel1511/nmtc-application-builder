"""Distress level concentration analysis for NMTC pipelines."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def analyze_distress_concentration(pipeline: "Pipeline") -> dict:
    """Compute distress level breakdown for a pipeline.

    Returns a dict with:
    - ``pct_deep`` – fraction of QEI in deep-distress tracts
    - ``pct_severe`` – fraction of QEI in severe-distress tracts
    - ``pct_deep_or_severe`` – combined deep + severe (key competitive metric)
    - ``pct_lic`` – fraction of QEI in standard LIC tracts
    - ``pct_non_lic`` – fraction of QEI in ineligible tracts
    - ``pct_native_area`` – fraction of QEI in NMTC Native Areas
    - ``pct_high_migration_rural`` – fraction of QEI in HMR tracts
    - ``dollars_by_distress`` – absolute QEI dollars in each category
    - ``pct_eligible`` – fraction of QEI in any eligible (LIC) tract
    - ``meets_min_threshold`` – bool, ≥ min_deep_distress competitive threshold
    - ``meets_target_threshold`` – bool, ≥ target_deep_distress threshold
    - ``project_count_by_distress`` – project count per level

    Example::

        result = analyze_distress_concentration(pipeline)
        print(f"Deep/Severe: {result['pct_deep_or_severe']:.0%}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_distress_result()

    total_qei = sum(p.qei_request for p in projects)
    if total_qei == 0:
        return _empty_distress_result()

    buckets = {"deep": 0.0, "severe": 0.0, "lic": 0.0, "ineligible": 0.0, "unknown": 0.0}
    counts = {"deep": 0, "severe": 0, "lic": 0, "ineligible": 0, "unknown": 0}
    native_qei = 0.0
    hmr_qei = 0.0
    us_territory_qei = 0.0
    persistent_poverty_qei = 0.0
    below_market_rate_qei = 0.0
    unrelated_entity_qei = 0.0

    for p in projects:
        level = p.distress_level or "unknown"
        if level not in buckets:
            level = "unknown"
        buckets[level] += p.qei_request
        counts[level] += 1
        if p.is_native_area:
            native_qei += p.qei_request
        if p.is_high_migration_rural:
            hmr_qei += p.qei_request
        if p.is_us_territory:
            us_territory_qei += p.qei_request
        if p.is_persistent_poverty:
            persistent_poverty_qei += p.qei_request
        if p.is_below_market_rate:
            below_market_rate_qei += p.qei_request
        if p.is_unrelated_entity:
            unrelated_entity_qei += p.qei_request

    pct_deep = buckets["deep"] / total_qei
    pct_severe = buckets["severe"] / total_qei
    pct_deep_or_severe = pct_deep + pct_severe
    pct_lic = buckets["lic"] / total_qei
    pct_non_lic = (buckets["ineligible"] + buckets["unknown"]) / total_qei
    pct_eligible = pct_deep + pct_severe + pct_lic

    min_threshold = TARGET_DISTRESS_THRESHOLDS["min_deep_distress"]
    target_threshold = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]

    return {
        "pct_deep": pct_deep,
        "pct_severe": pct_severe,
        "pct_deep_or_severe": pct_deep_or_severe,
        "pct_lic": pct_lic,
        "pct_non_lic": pct_non_lic,
        "pct_native_area": native_qei / total_qei,
        "pct_high_migration_rural": hmr_qei / total_qei,
        "pct_us_territories": us_territory_qei / total_qei,
        "pct_persistent_poverty": persistent_poverty_qei / total_qei,
        "pct_below_market_rate": below_market_rate_qei / total_qei,
        "pct_unrelated_entity": unrelated_entity_qei / total_qei,
        "pct_eligible": pct_eligible,
        "dollars_by_distress": {k: round(v) for k, v in buckets.items()},
        "project_count_by_distress": counts,
        "total_qei": total_qei,
        "meets_min_threshold": pct_deep_or_severe >= min_threshold,
        "meets_target_threshold": pct_deep_or_severe >= target_threshold,
        "vs_historical_winners": _assess_vs_winners(pct_deep_or_severe),
    }


def _assess_vs_winners(pct_deep_or_severe: float) -> str:
    """Qualitative benchmark against historical winning applications."""
    if pct_deep_or_severe >= 0.85:
        return "top_quartile"
    if pct_deep_or_severe >= 0.75:
        return "competitive"
    if pct_deep_or_severe >= 0.50:
        return "below_average"
    return "uncompetitive"


def _empty_distress_result() -> dict:
    buckets = {"deep": 0, "severe": 0, "lic": 0, "ineligible": 0, "unknown": 0}
    return {
        "pct_deep": 0.0,
        "pct_severe": 0.0,
        "pct_deep_or_severe": 0.0,
        "pct_lic": 0.0,
        "pct_non_lic": 0.0,
        "pct_native_area": 0.0,
        "pct_high_migration_rural": 0.0,
        "pct_us_territories": 0.0,
        "pct_persistent_poverty": 0.0,
        "pct_below_market_rate": 0.0,
        "pct_unrelated_entity": 0.0,
        "pct_eligible": 0.0,
        "dollars_by_distress": buckets,
        "project_count_by_distress": dict(buckets),
        "total_qei": 0.0,
        "meets_min_threshold": False,
        "meets_target_threshold": False,
        "vs_historical_winners": "uncompetitive",
    }
