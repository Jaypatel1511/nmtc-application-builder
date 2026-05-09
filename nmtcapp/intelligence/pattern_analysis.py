"""
Pattern analysis: characterize historical winner patterns and compare a
pipeline result against them.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from nmtcapp.data.historical_awards import (
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
    get_overall_acceptance_rate,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult


def analyze_winning_patterns() -> dict:
    """Return a structured summary of historical NMTC winner patterns.

    Aggregates data from CDFI Fund award announcements (CY2020–CY2024) into a
    single dict. Useful for display tables, quick benchmarking, and notebook
    exploration.

    Returns:
        dict with keys: ``distress``, ``geographic``, ``sector``, ``impact``,
        ``acceptance_rate``.

    Example::

        from nmtcapp.intelligence.pattern_analysis import analyze_winning_patterns
        patterns = analyze_winning_patterns()
        print(f"Winner median distress: {patterns['distress']['p50_pct_deep_or_severe']:.0%}")
    """
    return {
        "distress": {
            "mean_pct_deep_or_severe": WINNER_DISTRESS_PATTERNS["mean_pct_deep_or_severe"],
            "p25_pct_deep_or_severe": WINNER_DISTRESS_PATTERNS["p25_pct_deep_or_severe"],
            "p50_pct_deep_or_severe": WINNER_DISTRESS_PATTERNS["p50_pct_deep_or_severe"],
            "p75_pct_deep_or_severe": WINNER_DISTRESS_PATTERNS["p75_pct_deep_or_severe"],
            "p90_pct_deep_or_severe": WINNER_DISTRESS_PATTERNS["p90_pct_deep_or_severe"],
            "floor_min_pct": WINNER_DISTRESS_PATTERNS["min_pct_deep_or_severe"],
            "mean_pct_native_area": WINNER_DISTRESS_PATTERNS["mean_pct_native_area"],
            "mean_pct_eligible": WINNER_DISTRESS_PATTERNS["mean_pct_eligible"],
        },
        "geographic": {
            "mean_states": WINNER_GEOGRAPHIC_PATTERNS["mean_states"],
            "p25_states": WINNER_GEOGRAPHIC_PATTERNS["p25_states"],
            "p50_states": WINNER_GEOGRAPHIC_PATTERNS["p50_states"],
            "p75_states": WINNER_GEOGRAPHIC_PATTERNS["p75_states"],
            "min_states": WINNER_GEOGRAPHIC_PATTERNS["min_states"],
            "mean_projects": WINNER_GEOGRAPHIC_PATTERNS["mean_projects"],
            "p50_projects": WINNER_GEOGRAPHIC_PATTERNS["p50_projects"],
            "mean_hhi": WINNER_GEOGRAPHIC_PATTERNS["mean_hhi"],
            "rural_pct_mean": WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"],
        },
        "sector": {
            "healthcare": WINNER_SECTOR_PATTERNS["healthcare"],
            "affordable_housing": WINNER_SECTOR_PATTERNS["affordable_housing"],
            "small_business": WINNER_SECTOR_PATTERNS["small_business"],
            "education": WINNER_SECTOR_PATTERNS["education"],
            "community_facility": WINNER_SECTOR_PATTERNS["community_facility"],
            "mixed_use": WINNER_SECTOR_PATTERNS["mixed_use"],
            "clean_energy": WINNER_SECTOR_PATTERNS["clean_energy"],
            "other": WINNER_SECTOR_PATTERNS["other"],
            "mean_sectors_represented": WINNER_SECTOR_PATTERNS["mean_sectors_represented"],
            "max_single_sector_pct": WINNER_SECTOR_PATTERNS["max_single_sector_pct"],
        },
        "impact": {
            "mean_jobs_per_mm_qei": WINNER_IMPACT_BENCHMARKS["mean_jobs_per_mm_qei"],
            "p25_jobs_per_mm_qei": WINNER_IMPACT_BENCHMARKS["p25_jobs_per_mm_qei"],
            "p50_jobs_per_mm_qei": WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"],
            "p75_jobs_per_mm_qei": WINNER_IMPACT_BENCHMARKS["p75_jobs_per_mm_qei"],
            "top_decile_jobs_per_mm_qei": WINNER_IMPACT_BENCHMARKS["top_decile_jobs_per_mm_qei"],
            "mean_units_per_mm_qei": WINNER_IMPACT_BENCHMARKS["mean_units_per_mm_qei"],
            "mean_cost_per_job": WINNER_IMPACT_BENCHMARKS["mean_cost_per_job"],
        },
        "acceptance_rate": get_overall_acceptance_rate(rounds=4),
    }


def compare_to_winners(pipeline_result: "PipelineAnalysisResult") -> dict:
    """Compare a pipeline analysis result to historical winner pattern distributions.

    Returns a dict with one entry per major dimension. Each entry contains the
    pipeline's observed value, the winner distribution statistics, and a human-
    readable gap label ("above_winner_median", "at_winner_p25", etc.).

    Args:
        pipeline_result: Result from :class:`~nmtcapp.intelligence.pipeline_analyzer.PipelineAnalyzer`.

    Returns:
        dict with keys: ``distress``, ``geographic``, ``impact``, ``sector``.

    Example::

        from nmtcapp.intelligence.pattern_analysis import compare_to_winners
        comparison = compare_to_winners(result)
        print(comparison["distress"]["gap_label"])
    """
    d = pipeline_result.distress_breakdown
    g = pipeline_result.geographic_diversity
    s = pipeline_result.sector_mix
    i = pipeline_result.aggregate_impact

    def _gap_label_pct(value: float, p25: float, p50: float, p75: float) -> str:
        if value >= p75:
            return "above_winner_p75"
        if value >= p50:
            return "between_winner_p50_and_p75"
        if value >= p25:
            return "between_winner_p25_and_p50"
        return "below_winner_p25"

    def _gap_label_count(value: float, p25: float, p50: float, p75: float) -> str:
        if value >= p75:
            return "above_winner_p75"
        if value >= p50:
            return "between_winner_p50_and_p75"
        if value >= p25:
            return "between_winner_p25_and_p50"
        return "below_winner_p25"

    deep = d.get("pct_deep_or_severe", 0.0)
    states = float(g.get("states_count", 0))
    jpm = float(i.get("jobs_per_million_qei", 0.0))
    max_sector = float(s.get("max_single_sector_pct", 1.0))

    return {
        "distress": {
            "observed_pct_deep_or_severe": deep,
            "winner_p25": WINNER_DISTRESS_PATTERNS["p25_pct_deep_or_severe"],
            "winner_p50": WINNER_DISTRESS_PATTERNS["p50_pct_deep_or_severe"],
            "winner_p75": WINNER_DISTRESS_PATTERNS["p75_pct_deep_or_severe"],
            "winner_mean": WINNER_DISTRESS_PATTERNS["mean_pct_deep_or_severe"],
            "gap_to_winner_median": round(
                WINNER_DISTRESS_PATTERNS["p50_pct_deep_or_severe"] - deep, 3
            ),
            "gap_label": _gap_label_pct(
                deep,
                WINNER_DISTRESS_PATTERNS["p25_pct_deep_or_severe"],
                WINNER_DISTRESS_PATTERNS["p50_pct_deep_or_severe"],
                WINNER_DISTRESS_PATTERNS["p75_pct_deep_or_severe"],
            ),
        },
        "geographic": {
            "observed_states": int(states),
            "winner_p25_states": WINNER_GEOGRAPHIC_PATTERNS["p25_states"],
            "winner_p50_states": WINNER_GEOGRAPHIC_PATTERNS["p50_states"],
            "winner_p75_states": WINNER_GEOGRAPHIC_PATTERNS["p75_states"],
            "winner_mean_states": WINNER_GEOGRAPHIC_PATTERNS["mean_states"],
            "gap_to_winner_median_states": int(
                WINNER_GEOGRAPHIC_PATTERNS["p50_states"] - states
            ),
            "gap_label": _gap_label_count(
                states,
                WINNER_GEOGRAPHIC_PATTERNS["p25_states"],
                WINNER_GEOGRAPHIC_PATTERNS["p50_states"],
                WINNER_GEOGRAPHIC_PATTERNS["p75_states"],
            ),
        },
        "impact": {
            "observed_jobs_per_mm_qei": jpm,
            "winner_p25": WINNER_IMPACT_BENCHMARKS["p25_jobs_per_mm_qei"],
            "winner_p50": WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"],
            "winner_p75": WINNER_IMPACT_BENCHMARKS["p75_jobs_per_mm_qei"],
            "winner_mean": WINNER_IMPACT_BENCHMARKS["mean_jobs_per_mm_qei"],
            "gap_to_winner_median": round(
                WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"] - jpm, 2
            ),
            "gap_label": _gap_label_pct(
                jpm,
                WINNER_IMPACT_BENCHMARKS["p25_jobs_per_mm_qei"],
                WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"],
                WINNER_IMPACT_BENCHMARKS["p75_jobs_per_mm_qei"],
            ),
        },
        "sector": {
            "observed_max_single_sector_pct": max_sector,
            "winner_ceiling": WINNER_SECTOR_PATTERNS["max_single_sector_pct"],
            "above_ceiling": max_sector > WINNER_SECTOR_PATTERNS["max_single_sector_pct"],
            "observed_sectors": s.get("sectors_represented", 0),
            "winner_mean_sectors": WINNER_SECTOR_PATTERNS["mean_sectors_represented"],
        },
    }
