"""
Win alignment scoring for NMTC applications.

CRITICAL HONESTY REQUIREMENT: This module intentionally uses the term
"alignment score" rather than "win probability." The CDFI Fund publishes only
winner-level data; loser-level distributions are not available. Without both
winner and loser data it is not possible to compute a true probability of
selection. All scores in this module reflect how closely an application aligns
with patterns observed in historical winners (CY2020–CY2024), not the
likelihood of receiving an allocation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import BENCHMARK_METRIC_WEIGHTS
from nmtcapp.data.historical_awards import (
    APPLICATION_VOLUME_TRENDS,
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
    get_overall_acceptance_rate,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

_METHODOLOGY = (
    "IMPORTANT: This score measures alignment with patterns observed in historical "
    "NMTC award winners (CY2020–CY2024), not probability of selection. The CDFI Fund "
    "does not publish non-winner application data, so a true win probability cannot be "
    "computed. A high alignment score improves competitiveness but does not guarantee "
    "an award. Alignment score ≠ win probability."
)


@dataclass
class WinProbabilityScore:
    """Alignment score for an NMTC application vs. historical winners.

    The ``methodology_disclosure`` field is always populated and explains
    the limitations of interpreting this score as a win probability.

    Example::

        model = WinProbabilityModel()
        score = model.score(pipeline_result, 55_000_000)
        print(score.summary())
    """
    composite_score: float          # 0–100 alignment score
    dimensional_scores: dict        # per-dimension scores (0–100 each)
    acceptance_rate_baseline: float  # historical acceptance rate (e.g. 0.34)
    competitive_tier: str           # "strong", "competitive", "marginal", "weak"
    peer_comparison: str            # narrative vs. typical winners
    methodology_disclosure: str = field(default=_METHODOLOGY)

    def summary(self) -> str:
        """Return a formatted alignment score report."""
        lines = [
            "=" * 68,
            "  APPLICATION ALIGNMENT SCORE (vs. Historical NMTC Winners)",
            f"  Composite Score:    {self.composite_score:.1f} / 100",
            f"  Competitive Tier:   {self.competitive_tier.upper()}",
            f"  Acceptance Baseline:{self.acceptance_rate_baseline:.1%} "
            f"(recent 4-round average)",
            "=" * 68,
            "",
            "  Dimensional Scores:",
        ]
        for dim, sc in self.dimensional_scores.items():
            label = dim.replace("_", " ").title()
            bar = _mini_bar(sc)
            lines.append(f"  {label:<30} {sc:5.1f}  {bar}")
        lines.extend([
            "",
            f"  Assessment: {self.peer_comparison}",
            "",
            "  *** METHODOLOGY NOTE ***",
            f"  {self.methodology_disclosure}",
            "=" * 68,
        ])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score,
            "dimensional_scores": self.dimensional_scores,
            "acceptance_rate_baseline": self.acceptance_rate_baseline,
            "competitive_tier": self.competitive_tier,
            "peer_comparison": self.peer_comparison,
            "methodology_disclosure": self.methodology_disclosure,
        }


class WinProbabilityModel:
    """Score a NMTC application's alignment with historical winner patterns.

    Example::

        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        model = WinProbabilityModel()
        score = model.score(pipeline_result, 55_000_000)
        print(score.summary())
    """

    def score(
        self,
        pipeline_result: "PipelineAnalysisResult",
        requested_allocation: float,
        application_round: str = "CY2025",
    ) -> WinProbabilityScore:
        """Compute alignment score against historical NMTC winners.

        Args:
            pipeline_result: Result from :class:`~nmtcapp.intelligence.pipeline_analyzer.PipelineAnalyzer`.
            requested_allocation: CDE's requested allocation in dollars.
            application_round: Target application round label (informational).

        Returns:
            :class:`WinProbabilityScore` with composite score and per-dimension breakdown.

        Example::

            score = WinProbabilityModel().score(result, 55_000_000)
            print(f"Alignment score: {score.composite_score:.1f}/100")
        """
        d = pipeline_result.distress_breakdown
        g = pipeline_result.geographic_diversity
        s = pipeline_result.sector_mix
        i = pipeline_result.aggregate_impact

        # --- Dimension: distress (weight 0.35 — matches NOFA emphasis) ---
        distress_score = self._score_distress(d)

        # --- Dimension: geographic diversity (weight 0.20) ---
        geo_score = self._score_geography(g)

        # --- Dimension: impact intensity (weight 0.25) ---
        impact_score = self._score_impact(i)

        # --- Dimension: sector diversity (weight 0.15) ---
        sector_score = self._score_sector(s)

        # --- Dimension: pipeline quality (weight 0.05) ---
        pipeline_score = self._score_pipeline(pipeline_result, requested_allocation)

        dimensional_scores = {
            "distress_concentration": round(distress_score, 1),
            "geographic_diversity": round(geo_score, 1),
            "impact_intensity": round(impact_score, 1),
            "sector_diversity": round(sector_score, 1),
            "pipeline_quality": round(pipeline_score, 1),
        }

        weights = {
            "distress_concentration": 0.35,
            "geographic_diversity": 0.20,
            "impact_intensity": 0.25,
            "sector_diversity": 0.15,
            "pipeline_quality": 0.05,
        }

        composite = sum(
            dimensional_scores[k] * weights[k] for k in weights
        )
        composite = round(min(100.0, max(0.0, composite)), 1)

        baseline = get_overall_acceptance_rate(rounds=4)
        tier = self._classify_tier(composite)
        peer_note = self._peer_comparison(composite, dimensional_scores)

        return WinProbabilityScore(
            composite_score=composite,
            dimensional_scores=dimensional_scores,
            acceptance_rate_baseline=baseline,
            competitive_tier=tier,
            peer_comparison=peer_note,
        )

    # ------------------------------------------------------------------
    # Dimension scorers — each returns 0–100
    # ------------------------------------------------------------------

    def _score_distress(self, d: dict) -> float:
        deep = d.get("pct_deep_or_severe", 0.0)
        # Reference distribution: mean 0.81, std 0.11, floor 0.50
        mean = WINNER_DISTRESS_PATTERNS["mean_pct_deep_or_severe"]
        std = WINNER_DISTRESS_PATTERNS["std_pct_deep_or_severe"]
        pctile = _normal_cdf((deep - mean) / max(std, 1e-9))
        # Linear scaling: 0th percentile → 0, 100th percentile → 100
        # Clamp so below 0.50 (historical floor) scores poorly
        if deep < WINNER_DISTRESS_PATTERNS["min_pct_deep_or_severe"]:
            return deep / WINNER_DISTRESS_PATTERNS["min_pct_deep_or_severe"] * 30.0
        return min(100.0, pctile * 100.0)

    def _score_geography(self, g: dict) -> float:
        states = g.get("states_count", 0)
        hhi = g.get("hhi", 10_000)
        # States: normalize vs winner distribution (mean 7.2, std 3.8)
        states_mean = WINNER_GEOGRAPHIC_PATTERNS["mean_states"]
        states_std = WINNER_GEOGRAPHIC_PATTERNS["std_states"]
        states_score = _normal_cdf((states - states_mean) / max(states_std, 1e-9)) * 100.0
        # HHI: lower is better; normalize inversely
        hhi_score = max(0.0, (2_000 - hhi) / 2_000 * 100.0)
        # Rural bonus: above winner mean (18%) adds points
        rural = g.get("rural_pct", 0.0)
        rural_bonus = min(10.0, rural / WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"] * 5.0)
        return min(100.0, states_score * 0.5 + hhi_score * 0.4 + rural_bonus)

    def _score_impact(self, i: dict) -> float:
        jpm = i.get("jobs_per_million_qei", 0.0)
        mean = WINNER_IMPACT_BENCHMARKS["mean_jobs_per_mm_qei"]
        # p75 = 18, p50 = 10
        if jpm <= 0:
            return 0.0
        if jpm >= WINNER_IMPACT_BENCHMARKS["top_decile_jobs_per_mm_qei"]:
            return 100.0
        pctile = _normal_cdf((jpm - mean) / 6.0) * 100.0
        return min(100.0, max(0.0, pctile))

    def _score_sector(self, s: dict) -> float:
        n_sectors = s.get("sectors_represented", 0)
        max_single = s.get("max_single_sector_pct", 1.0)
        # Sectors: normalize vs winner mean 4.8
        sector_score = min(100.0, n_sectors / WINNER_SECTOR_PATTERNS["mean_sectors_represented"] * 80.0)
        # Concentration penalty: > 35% in one sector is a red flag
        conc_penalty = max(0.0, (max_single - WINNER_SECTOR_PATTERNS["max_single_sector_pct"]) * 200.0)
        return max(0.0, min(100.0, sector_score - conc_penalty))

    def _score_pipeline(
        self,
        result: "PipelineAnalysisResult",
        requested_allocation: float,
    ) -> float:
        # Eligibility
        elig = result.eligibility_pct
        elig_score = min(100.0, elig / WINNER_DISTRESS_PATTERNS["mean_pct_eligible"] * 90.0)
        # Project count vs winner mean (14.5)
        n = result.total_projects
        count_score = min(100.0, n / WINNER_GEOGRAPHIC_PATTERNS["mean_projects"] * 80.0)
        # Award size fit — reward sizes in the typical winner range ($35-65M)
        if 35_000_000 <= requested_allocation <= 65_000_000:
            size_score = 90.0
        elif 25_000_000 <= requested_allocation < 35_000_000:
            size_score = 70.0
        elif requested_allocation > 65_000_000:
            size_score = 75.0
        else:
            size_score = 50.0
        return elig_score * 0.4 + count_score * 0.3 + size_score * 0.3

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------

    def _classify_tier(self, score: float) -> str:
        if score >= 75:
            return "strong"
        if score >= 55:
            return "competitive"
        if score >= 35:
            return "marginal"
        return "weak"

    def _peer_comparison(self, score: float, dims: dict) -> str:
        tier = self._classify_tier(score)
        strong_dims = [k for k, v in dims.items() if v >= 75]
        weak_dims = [k for k, v in dims.items() if v < 40]

        phrases = {
            "strong": "Well-aligned with historical winners across most dimensions.",
            "competitive": "Competitive alignment — above threshold in key dimensions.",
            "marginal": "Marginal alignment — improvement needed to be competitive.",
            "weak": "Below typical winner patterns — significant changes required.",
        }
        note = phrases[tier]
        if strong_dims:
            note += f" Standout dimensions: {', '.join(d.replace('_', ' ') for d in strong_dims[:2])}."
        if weak_dims:
            note += f" Priority gaps: {', '.join(d.replace('_', ' ') for d in weak_dims[:2])}."
        return note


def _normal_cdf(x: float) -> float:
    return math.erfc(-x / math.sqrt(2)) * 0.5


def _mini_bar(score: float, width: int = 12) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)
