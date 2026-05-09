"""
Actionable recommendation engine for NMTC applications.

Each recommendation is specific, quantified, and maps to a scoring dimension.
Recommendations are tiered by priority: critical (blocks competitiveness),
high (meaningful score improvement), medium (incremental gains).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from nmtcapp.data.historical_awards import (
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.benchmarks import BenchmarkComparison
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
    from nmtcapp.intelligence.win_probability import WinProbabilityScore


@dataclass
class Recommendation:
    """A single actionable recommendation for improving NMTC application competitiveness.

    All fields are populated — ``action`` and ``quantified_improvement`` are
    always specific and measurable.
    """
    category: str                # "distress", "geographic", "sector", "impact", "pipeline"
    priority: str                # "critical", "high", "medium"
    finding: str                 # what the analysis found
    action: str                  # specific action to take
    expected_impact: str         # qualitative outcome
    quantified_improvement: str  # numeric estimate of score/metric change

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "priority": self.priority,
            "finding": self.finding,
            "action": self.action,
            "expected_impact": self.expected_impact,
            "quantified_improvement": self.quantified_improvement,
        }


@dataclass
class RecommendationSet:
    """Full set of recommendations for an NMTC application.

    Example::

        engine = RecommendationEngine()
        recs = engine.recommend(pipeline_result, benchmark_comparison, win_score)
        print(recs.summary())
    """
    recommendations: List[Recommendation]
    overall_assessment: str
    quick_wins: List[Recommendation] = field(default_factory=list)
    strategic_changes: List[Recommendation] = field(default_factory=list)

    def __post_init__(self):
        self.quick_wins = [r for r in self.recommendations if r.priority == "medium"]
        self.strategic_changes = [r for r in self.recommendations if r.priority in ("critical", "high")]

    def summary(self) -> str:
        lines = [
            "=" * 68,
            "  RECOMMENDATIONS",
            f"  {self.overall_assessment}",
            "=" * 68,
        ]
        priority_order = [("critical", "[!]"), ("high", "[H]"), ("medium", "[M]")]
        for priority, symbol in priority_order:
            recs = [r for r in self.recommendations if r.priority == priority]
            if not recs:
                continue
            lines.append(f"\n  {symbol} {priority.upper()} PRIORITY")
            lines.append(f"  {'─'*62}")
            for r in recs:
                lines.extend([
                    f"  Category:  {r.category.title()}",
                    f"  Finding:   {r.finding}",
                    f"  Action:    {r.action}",
                    f"  Impact:    {r.expected_impact}",
                    f"  Estimate:  {r.quantified_improvement}",
                    "",
                ])
        lines.append("=" * 68)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "overall_assessment": self.overall_assessment,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "quick_wins": [r.to_dict() for r in self.quick_wins],
            "strategic_changes": [r.to_dict() for r in self.strategic_changes],
        }


class RecommendationEngine:
    """Generate actionable, quantified recommendations from analysis results.

    Example::

        from nmtcapp.intelligence.recommendations import RecommendationEngine
        engine = RecommendationEngine()
        recs = engine.recommend(pipeline_result, benchmark_comparison, win_score)
        print(recs.summary())
    """

    def recommend(
        self,
        pipeline_result: "PipelineAnalysisResult",
        benchmark_comparison: Optional["BenchmarkComparison"],
        win_score: Optional["WinProbabilityScore"],
    ) -> RecommendationSet:
        """Generate a prioritized recommendation set.

        Args:
            pipeline_result: Result from PipelineAnalyzer.
            benchmark_comparison: Result from HistoricalBenchmarks.compare() (or None).
            win_score: Result from WinProbabilityModel.score() (or None).

        Returns:
            :class:`RecommendationSet` with all recommendations sorted by priority.

        Example::

            recs = RecommendationEngine().recommend(result, None, None)
        """
        recs: List[Recommendation] = []

        d = pipeline_result.distress_breakdown
        g = pipeline_result.geographic_diversity
        s = pipeline_result.sector_mix
        i = pipeline_result.aggregate_impact

        recs.extend(self._distress_recs(d))
        recs.extend(self._geographic_recs(g))
        recs.extend(self._impact_recs(i))
        recs.extend(self._sector_recs(s))
        recs.extend(self._pipeline_recs(pipeline_result))

        # Sort: critical → high → medium
        priority_rank = {"critical": 0, "high": 1, "medium": 2}
        recs.sort(key=lambda r: priority_rank.get(r.priority, 3))

        assessment = self._overall_assessment(pipeline_result, win_score)
        return RecommendationSet(recommendations=recs, overall_assessment=assessment)

    # ------------------------------------------------------------------
    # Category-specific recommendation generators
    # ------------------------------------------------------------------

    def _distress_recs(self, d: dict) -> List[Recommendation]:
        recs = []
        deep = d.get("pct_deep_or_severe", 0.0)
        winner_median = WINNER_DISTRESS_PATTERNS["p50_pct_deep_or_severe"]
        winner_p25 = WINNER_DISTRESS_PATTERNS["p25_pct_deep_or_severe"]

        if deep < winner_p25:
            gap = winner_p25 - deep
            pct_projects = round(gap * 100)
            recs.append(Recommendation(
                category="distress",
                priority="critical",
                finding=(
                    f"Deep/severe distress concentration is {deep:.0%} — "
                    f"below the p25 floor of {winner_p25:.0%} seen in historical winners."
                ),
                action=(
                    f"Replace at least {pct_projects} percentage points of standard-LIC pipeline "
                    "with projects in Deep Distressed or Severely Distressed census tracts. "
                    "Use CDFI Fund's NMTC Mapping Tool to identify qualifying tracts."
                ),
                expected_impact=(
                    "Bring distress concentration into the competitive range; "
                    "NOFA scoring criteria weight this dimension heavily."
                ),
                quantified_improvement=(
                    f"Estimated +15–25 distress alignment score points; "
                    f"moves from 'below_weak' tier toward 'competitive'."
                ),
            ))
        elif deep < winner_median:
            gap = winner_median - deep
            recs.append(Recommendation(
                category="distress",
                priority="high",
                finding=(
                    f"Deep/severe distress concentration ({deep:.0%}) is competitive but "
                    f"below the winner median of {winner_median:.0%}."
                ),
                action=(
                    f"Substitute {round(gap * 100)}pp of LIC projects with deeper-distress "
                    "alternatives to reach the winner median. Target projects in tracts with "
                    "poverty rate ≥30% or median family income ≤60% AMI."
                ),
                expected_impact="Reach median winner distress concentration; stronger NOFA score.",
                quantified_improvement=(
                    f"Estimated +8–15 distress alignment score points; "
                    f"advances from 'competitive' to 'strong' tier."
                ),
            ))

        # Native area / HMR bonus
        native = d.get("pct_native_area", 0.0)
        if native < WINNER_DISTRESS_PATTERNS["mean_pct_native_area"]:
            recs.append(Recommendation(
                category="distress",
                priority="medium",
                finding=(
                    f"Native area concentration ({native:.0%}) is below the winner mean "
                    f"of {WINNER_DISTRESS_PATTERNS['mean_pct_native_area']:.0%}."
                ),
                action=(
                    "Add 1–2 projects in BIA-designated Native American areas or "
                    "Alaska Native Villages to capture the NOFA Native Area bonus."
                ),
                expected_impact="Trigger Native Area scoring bonus; differentiates from competing applications.",
                quantified_improvement="Estimated +3–5 overall alignment points from bonus credit.",
            ))
        return recs

    def _geographic_recs(self, g: dict) -> List[Recommendation]:
        recs = []
        states = g.get("states_count", 0)
        hhi = g.get("hhi", 10_000)
        rural = g.get("rural_pct", 0.0)

        winner_min_states = 2
        winner_p25_states = int(WINNER_GEOGRAPHIC_PATTERNS["p25_states"])
        winner_median_states = int(WINNER_GEOGRAPHIC_PATTERNS["p50_states"])

        if states < winner_min_states:
            recs.append(Recommendation(
                category="geographic",
                priority="critical",
                finding=(
                    f"Pipeline spans only {states} state(s) — below the minimum "
                    f"of {winner_min_states} states seen in any historical winner."
                ),
                action=(
                    f"Immediately add projects in at least {winner_min_states - states + 1} "
                    "additional state(s). A single-state pipeline is rarely funded. "
                    "Target adjacent markets with existing QALICB relationships."
                ),
                expected_impact="Meet minimum geographic diversity requirement for competitive consideration.",
                quantified_improvement=(
                    f"Geographic score near 0 currently; +30–50 points by reaching "
                    f"{winner_min_states + 1} states."
                ),
            ))
        elif states < winner_p25_states:
            recs.append(Recommendation(
                category="geographic",
                priority="high",
                finding=(
                    f"Pipeline spans {states} states — below the p25 of {winner_p25_states} "
                    "states seen in historical winners."
                ),
                action=(
                    f"Add projects in {winner_p25_states - states} additional states to reach "
                    "the competitive baseline. Prioritize states where the CDE has existing "
                    "relationships or a planned market entry."
                ),
                expected_impact="Reach competitive geographic baseline; improve NOFA geographic score.",
                quantified_improvement=(
                    f"Estimated +10–20 geographic alignment score points."
                ),
            ))
        elif states < winner_median_states:
            recs.append(Recommendation(
                category="geographic",
                priority="medium",
                finding=(
                    f"Pipeline spans {states} states — below the winner median of "
                    f"{winner_median_states} states."
                ),
                action=(
                    f"Add {winner_median_states - states} more state(s) to reach the "
                    "winner median. Consider projects in underserved markets to also "
                    "improve distress and rural metrics simultaneously."
                ),
                expected_impact="Reach median geographic breadth; marginal NOFA improvement.",
                quantified_improvement="Estimated +5–10 geographic alignment score points.",
            ))

        if hhi > WINNER_GEOGRAPHIC_PATTERNS["mean_hhi"] * 1.5:
            recs.append(Recommendation(
                category="geographic",
                priority="high",
                finding=(
                    f"Geographic HHI of {hhi:.0f} indicates high concentration — "
                    f"well above winner mean of {WINNER_GEOGRAPHIC_PATTERNS['mean_hhi']:.0f}."
                ),
                action=(
                    "Diversify project distribution across states. No single state should "
                    "represent more than 40% of total QEI. Consider splitting larger project "
                    "commitments into multi-state tranches."
                ),
                expected_impact="Reduce concentration; improve geographic diversity score.",
                quantified_improvement=(
                    f"Reducing HHI below {WINNER_GEOGRAPHIC_PATTERNS['mean_hhi']:.0f} "
                    "estimated to add +8–12 geographic alignment points."
                ),
            ))

        if rural < WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"] * 0.5:
            recs.append(Recommendation(
                category="geographic",
                priority="medium",
                finding=(
                    f"Rural concentration ({rural:.0%}) is below half the winner mean "
                    f"of {WINNER_GEOGRAPHIC_PATTERNS['rural_pct_mean']:.0%}."
                ),
                action=(
                    "Add 1–2 rural projects (non-metropolitan census tracts) to reach "
                    f"the ~{WINNER_GEOGRAPHIC_PATTERNS['rural_pct_mean']:.0%} winner average. "
                    "Rural projects often score well on distress metrics simultaneously."
                ),
                expected_impact="Improve rural NOFA scoring criterion; may also lift distress score.",
                quantified_improvement="Estimated +3–6 geographic alignment points from rural bonus.",
            ))
        return recs

    def _impact_recs(self, i: dict) -> List[Recommendation]:
        recs = []
        jpm = i.get("jobs_per_million_qei", 0.0)
        p25 = WINNER_IMPACT_BENCHMARKS["p25_jobs_per_mm_qei"]
        p50 = WINNER_IMPACT_BENCHMARKS["p50_jobs_per_mm_qei"]
        p75 = WINNER_IMPACT_BENCHMARKS["p75_jobs_per_mm_qei"]

        if jpm < p25:
            recs.append(Recommendation(
                category="impact",
                priority="high",
                finding=(
                    f"Jobs-per-$1MM-QEI of {jpm:.1f} is below the winner p25 of {p25:.0f}. "
                    "This metric receives significant weight in CDFI Fund scoring."
                ),
                action=(
                    "Add operating business (manufacturing, healthcare, light industrial) "
                    "projects to the pipeline. These typically generate 20–40 jobs per "
                    f"$1MM QEI vs. real-estate projects at 5–10. Target {p50:.0f} jobs/$MM "
                    "as the immediate goal."
                ),
                expected_impact="Bring impact intensity above winner p25; meaningfully improve NOFA score.",
                quantified_improvement=(
                    f"Each operating-business project at ~25 jobs/$MM raises portfolio "
                    f"average by 1–3 jobs/$MM. Target ≥{p50:.0f} jobs/$MM to enter "
                    f"competitive range (+10–20 impact alignment points)."
                ),
            ))
        elif jpm < p50:
            recs.append(Recommendation(
                category="impact",
                priority="medium",
                finding=(
                    f"Jobs-per-$1MM-QEI of {jpm:.1f} is between p25 ({p25:.0f}) and "
                    f"median ({p50:.0f}) of historical winners."
                ),
                action=(
                    f"Add 1–2 high-job-intensity projects targeting {p75:.0f}+ jobs/$MM "
                    "to lift the portfolio average above the winner median."
                ),
                expected_impact="Reach median winner impact intensity; competitive NOFA impact score.",
                quantified_improvement=(
                    f"Estimated +5–10 impact alignment points by reaching {p50:.0f} jobs/$MM."
                ),
            ))
        return recs

    def _sector_recs(self, s: dict) -> List[Recommendation]:
        recs = []
        n_sectors = s.get("sectors_represented", 0)
        max_single = s.get("max_single_sector_pct", 0.0)
        dominant = s.get("dominant_sector", "unknown")
        winner_max = WINNER_SECTOR_PATTERNS["max_single_sector_pct"]
        winner_mean_sectors = WINNER_SECTOR_PATTERNS["mean_sectors_represented"]

        if max_single > winner_max:
            excess = max_single - winner_max
            recs.append(Recommendation(
                category="sector",
                priority="high",
                finding=(
                    f"Sector '{dominant}' represents {max_single:.0%} of QEI — "
                    f"above the {winner_max:.0%} concentration ceiling seen in winners."
                ),
                action=(
                    f"Reduce '{dominant}' concentration by {round(excess * 100)}pp by adding "
                    "projects in complementary sectors (healthcare + education + community "
                    "facility is a common winning combination). Aim for ≤35% per sector."
                ),
                expected_impact="Reduce concentration risk; better alignment with CDFI Fund diversification preference.",
                quantified_improvement=(
                    f"Reducing to ≤{winner_max:.0%} estimated to add +8–12 sector alignment points."
                ),
            ))

        if n_sectors < winner_mean_sectors - 1:
            target = int(winner_mean_sectors)
            recs.append(Recommendation(
                category="sector",
                priority="medium",
                finding=(
                    f"Only {n_sectors} sector(s) represented — below the winner mean "
                    f"of {winner_mean_sectors:.1f}."
                ),
                action=(
                    f"Expand to {target} sectors by adding projects in 1–2 underrepresented "
                    "sectors. High-priority CDFI Fund sectors: healthcare, affordable housing, "
                    "education, small business, and community facilities."
                ),
                expected_impact="Improve sector diversity score; signal mission breadth to reviewers.",
                quantified_improvement=(
                    f"Reaching {target} sectors estimated to add +4–8 sector alignment points."
                ),
            ))
        return recs

    def _pipeline_recs(self, r: "PipelineAnalysisResult") -> List[Recommendation]:
        recs = []
        winner_median_projects = int(WINNER_GEOGRAPHIC_PATTERNS["p50_projects"])

        if r.eligibility_pct < 0.90:
            recs.append(Recommendation(
                category="pipeline",
                priority="critical",
                finding=(
                    f"NMTC eligibility rate is {r.eligibility_pct:.0%} — "
                    "below the 90% competitive threshold."
                ),
                action=(
                    "Verify census tract eligibility for all pipeline projects using the "
                    "CDFI Fund NMTC Mapping Tool. Remove or replace ineligible projects "
                    "immediately. Target ≥98% eligibility."
                ),
                expected_impact="Ensure all QEI is deployable; avoid NOFA eligibility penalties.",
                quantified_improvement=(
                    "Reaching 98% eligibility adds an estimated +10–15 pipeline quality points."
                ),
            ))
        elif r.eligibility_pct < 0.96:
            recs.append(Recommendation(
                category="pipeline",
                priority="medium",
                finding=(
                    f"Eligibility rate ({r.eligibility_pct:.0%}) is below the winner "
                    "average of 96%."
                ),
                action=(
                    "Review borderline projects and confirm tract eligibility. "
                    "Replace any projects below 80% confidence of eligibility."
                ),
                expected_impact="Improve eligibility score; reduce NOFA review risk.",
                quantified_improvement="Estimated +3–7 pipeline quality points.",
            ))

        if r.total_projects < winner_median_projects:
            recs.append(Recommendation(
                category="pipeline",
                priority="medium",
                finding=(
                    f"Pipeline has {r.total_projects} projects — below the winner "
                    f"median of {winner_median_projects}."
                ),
                action=(
                    f"Add {winner_median_projects - r.total_projects} more projects to "
                    "reach the winner median. A deeper pipeline demonstrates deployment "
                    "certainty and sector diversity."
                ),
                expected_impact="Demonstrate deployment readiness; improve pipeline depth score.",
                quantified_improvement=(
                    f"Estimated +3–5 pipeline quality points reaching {winner_median_projects} "
                    "projects."
                ),
            ))
        return recs

    def _overall_assessment(
        self,
        result: "PipelineAnalysisResult",
        win_score: Optional["WinProbabilityScore"],
    ) -> str:
        if win_score is None:
            return (
                "Analysis complete. Review recommendations below to improve "
                "alignment with historical NMTC winner patterns."
            )
        score = win_score.composite_score
        tier = win_score.competitive_tier
        phrases = {
            "strong": (
                f"Strong alignment ({score:.0f}/100) with historical winners. "
                "Focus on incremental improvements and maintaining strengths through submission."
            ),
            "competitive": (
                f"Competitive alignment ({score:.0f}/100). Priority changes below "
                "could improve your score by 10–20 points before submission."
            ),
            "marginal": (
                f"Marginal alignment ({score:.0f}/100). Significant changes recommended "
                "before submission. Address 'critical' items first."
            ),
            "weak": (
                f"Weak alignment ({score:.0f}/100). Pipeline restructuring required "
                "to be competitive. All 'critical' recommendations are blocking issues."
            ),
        }
        return phrases.get(tier, f"Score: {score:.0f}/100. Review recommendations.")
