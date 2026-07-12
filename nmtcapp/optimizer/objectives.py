"""Objective functions for the NMTC pipeline optimizer.

All objectives return a float in [0, 1] where 1.0 is perfect alignment
with historical NMTC winner patterns.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

from nmtcapp.data.historical_awards import (
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
)

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import PipelineProject

# Default composite weights (must sum to 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "distress": 0.35,
    "geographic": 0.20,
    "impact": 0.25,
    "sector": 0.15,
    "pipeline": 0.05,
}

# Components that consume verified eligibility data. When eligibility is
# unverified they are excluded from the composite (never estimated).
ELIGIBILITY_COMPONENTS = ("distress",)


def eligibility_components_available(projects: List["PipelineProject"]) -> bool:
    """True when every project carries verified eligibility data.

    A distress-concentration claim over a pipeline containing unverified
    projects is itself unverifiable, so the eligibility-dependent alignment
    components are only computed when the whole set is verified.
    """
    return bool(projects) and all(p.is_nmtc_eligible is not None for p in projects)


def score_distress_alignment(
    projects: List["PipelineProject"],
    requested_allocation: float,
) -> float:
    """Score distress concentration alignment vs. historical winners.

    Returns 0.0–1.0 where 1.0 = above winner p75 deep/severe distress.

    Example::

        score = score_distress_alignment(projects, 55_000_000)
    """
    if not projects:
        return 0.0
    total_qei = sum(p.qei_request for p in projects)
    if total_qei <= 0:
        return 0.0
    deep_qei = sum(
        p.qei_request for p in projects
        if p.distress_level in ("deep", "severe")
    )
    deep_pct = deep_qei / total_qei
    winner_p75 = WINNER_DISTRESS_PATTERNS["p75_pct_deep_or_severe"]
    winner_floor = WINNER_DISTRESS_PATTERNS["min_pct_deep_or_severe"]
    if deep_pct >= winner_p75:
        return 1.0
    if deep_pct < winner_floor:
        return deep_pct / winner_floor * 0.3
    return 0.3 + (deep_pct - winner_floor) / (winner_p75 - winner_floor) * 0.7


def score_geographic_alignment(projects: List["PipelineProject"]) -> float:
    """Score geographic diversity alignment vs. historical winners.

    Returns 0.0–1.0 where 1.0 = above winner p75 state count + low HHI.

    Example::

        score = score_geographic_alignment(projects)
    """
    if not projects:
        return 0.0
    states = {p.state for p in projects}
    n_states = len(states)
    winner_p75 = WINNER_GEOGRAPHIC_PATTERNS["p75_states"]
    winner_p25 = WINNER_GEOGRAPHIC_PATTERNS["p25_states"]
    state_score = min(1.0, n_states / winner_p75)

    # HHI computation
    total_qei = sum(p.qei_request for p in projects)
    if total_qei > 0:
        state_shares = {}
        for p in projects:
            state_shares[p.state] = state_shares.get(p.state, 0.0) + p.qei_request / total_qei
        hhi = sum(s * s for s in state_shares.values()) * 10_000
        hhi_score = max(0.0, (2_000 - hhi) / 2_000)
    else:
        hhi_score = 0.0

    return min(1.0, state_score * 0.6 + hhi_score * 0.4)


def score_impact_alignment(
    projects: List["PipelineProject"],
    requested_allocation: float,
) -> float:
    """Score impact intensity (jobs/MM QEI) alignment vs. historical winners.

    Returns 0.0–1.0 where 1.0 = at/above winner top decile.

    Example::

        score = score_impact_alignment(projects, 55_000_000)
    """
    if not projects:
        return 0.0
    total_qei = sum(p.qei_request for p in projects)
    if total_qei <= 0:
        return 0.0
    total_jobs = sum(getattr(p, "expected_jobs_created", 0) for p in projects)
    jpm = total_jobs / (total_qei / 1_000_000)
    top_decile = WINNER_IMPACT_BENCHMARKS["top_decile_jobs_per_mm_qei"]
    p50 = WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"]
    if jpm >= top_decile:
        return 1.0
    if jpm >= p50:
        return 0.5 + (jpm - p50) / (top_decile - p50) * 0.5
    return max(0.0, jpm / p50 * 0.5)


def score_sector_alignment(projects: List["PipelineProject"]) -> float:
    """Score sector diversity alignment vs. historical winners.

    Returns 0.0–1.0 where 1.0 = winner-typical sector mix with no over-concentration.

    Example::

        score = score_sector_alignment(projects)
    """
    if not projects:
        return 0.0
    total_qei = sum(p.qei_request for p in projects)
    if total_qei <= 0:
        return 0.0
    sector_shares: Dict[str, float] = {}
    for p in projects:
        sector = getattr(p, "sector", "other")
        sector_shares[sector] = sector_shares.get(sector, 0.0) + p.qei_request / total_qei

    n_sectors = len(sector_shares)
    max_single = max(sector_shares.values()) if sector_shares else 1.0

    # Sector count score
    winner_mean_sectors = WINNER_SECTOR_PATTERNS["mean_sectors_represented"]
    sector_count_score = min(1.0, n_sectors / winner_mean_sectors)

    # Concentration penalty
    winner_ceiling = WINNER_SECTOR_PATTERNS["max_single_sector_pct"]
    if max_single > winner_ceiling:
        conc_penalty = min(0.5, (max_single - winner_ceiling) * 2.0)
    else:
        conc_penalty = 0.0

    return min(1.0, max(0.0, sector_count_score * 0.8 - conc_penalty))


def score_pipeline_quality(
    projects: List["PipelineProject"],
    requested_allocation: float,
    include_eligibility: bool = True,
) -> float:
    """Score overall pipeline quality (eligibility, project count, size fit).

    Returns 0.0–1.0. With ``include_eligibility=False`` (eligibility data
    unverified) the eligibility sub-score is excluded and the remaining
    sub-scores are renormalized — unverified is never counted as eligible
    or ineligible.

    Example::

        score = score_pipeline_quality(projects, 55_000_000)
    """
    if not projects:
        return 0.0

    n = len(projects)
    winner_median_n = WINNER_GEOGRAPHIC_PATTERNS["p50_projects"]
    count_score = min(1.0, n / winner_median_n)

    if 35_000_000 <= requested_allocation <= 65_000_000:
        size_score = 1.0
    elif 25_000_000 <= requested_allocation < 35_000_000:
        size_score = 0.75
    elif requested_allocation > 65_000_000:
        size_score = 0.80
    else:
        size_score = 0.50

    if not include_eligibility:
        return count_score * 0.5 + size_score * 0.5

    eligible = sum(1 for p in projects if p.is_nmtc_eligible is True)
    elig_pct = eligible / len(projects)
    winner_elig = WINNER_DISTRESS_PATTERNS["mean_pct_eligible"]
    elig_score = min(1.0, elig_pct / winner_elig)

    return elig_score * 0.4 + count_score * 0.3 + size_score * 0.3


def composite_alignment_score(
    projects: List["PipelineProject"],
    requested_allocation: float,
    weights: Optional[Dict[str, float]] = None,
    include_eligibility: Optional[bool] = None,
) -> float:
    """Compute a weighted composite alignment score for a project set.

    Args:
        projects: List of candidate projects.
        requested_allocation: CDE's requested allocation in dollars.
        weights: Optional override for dimension weights. Default weights sum to 1.0.
        include_eligibility: Component basis. ``None`` (default) auto-derives
            it from *projects* via :func:`eligibility_components_available`.
            Callers that compare scores across DIFFERENT project sets (e.g.
            the optimizer's before/after) must compute the basis once from
            the full input set and pass it explicitly, so every score shares
            one component basis.

    Returns:
        Float in [0, 1] where 1.0 is perfect historical winner alignment.
        When the eligibility basis is excluded, the eligibility components
        (see ``ELIGIBILITY_COMPONENTS``) are dropped and the remaining
        weights renormalized — the result is a PARTIAL score; callers should
        label it via :func:`eligibility_components_available`.

    Example::

        score = composite_alignment_score(projects, 55_000_000)
        print(f"Composite: {score:.2f}")
    """
    w = weights or DEFAULT_WEIGHTS
    if include_eligibility is None:
        include_eligibility = eligibility_components_available(projects)
    scores = {
        "geographic": score_geographic_alignment(projects),
        "impact": score_impact_alignment(projects, requested_allocation),
        "sector": score_sector_alignment(projects),
        "pipeline": score_pipeline_quality(
            projects, requested_allocation, include_eligibility=include_eligibility
        ),
    }
    if include_eligibility:
        scores["distress"] = score_distress_alignment(projects, requested_allocation)
    total_w = sum(w.get(k, 0.0) for k in scores)
    if total_w <= 0:
        return 0.0
    return sum(scores[k] * w.get(k, 0.0) for k in scores) / total_w
