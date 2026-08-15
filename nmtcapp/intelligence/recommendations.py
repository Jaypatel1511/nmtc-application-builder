"""
Recommendation engine for NMTC applications.

Each recommendation maps to a specific CDFI Fund criterion and cites the
CY 2024-2025 Review Process document section. Recommendations are triggered
by the new scoring structure (Business Strategy + Community Outcomes +
Priority Points) and ordered by potential point impact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import (
    BUSINESS_STRATEGY_MAX,
    COMMUNITY_OUTCOMES_MAX,
    DBC_PRIORITY_YEARS_MIN,
    DBC_VOLUME_PCT_MIN,
    DEEP_DISTRESS_MIN_PCT,
    DEEP_DISTRESS_MAX,
    HIGHER_DISTRESS_MAX,
    HIGHLY_QUALIFIED_AGGREGATE_MIN,
    HIGHLY_QUALIFIED_SECTION_MIN,
    SEVERE_DISTRESS_MIN_PCT,
    TOP_TIER_SECTION_MIN,
    TRACK_RECORD_ALIGNMENT_MAX,
    TRACK_RECORD_STRENGTH_MAX,
    TRACK_RECORD_DEPLOYMENT_MIN,
    TRACK_RECORD_PIPELINE_ALIGNMENT_MIN,
    UNRELATED_ENTITIES_MIN_PCT,
    WINNER_PATTERN_THRESHOLDS,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.benchmarks import BenchmarkComparison
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
    from nmtcapp.intelligence.win_probability import WinProbabilityScore

_SOURCE_DOC = "CY 2024-2025 Review Process"

# EVERY FEDERAL FIGURE IN THIS MODULE IS INTERPOLATED, NOT TYPED (1.2.1 L-3).
#
# RecommendationSet.summary() is a SEVENTH rendered surface. It is reachable
# through the public ``app.recommendations()`` and it is what the Streamlit
# scorer prints, and no gate in this package looked at it: the invariance gate
# masks digits, the attribution gate normalises them, and the constant registry
# had never named it as a surface. So the 85% CDFI Fund distress threshold —
# which appeared three separate times below as the literal 0.85 and the literal
# string "85%" — could be changed to 55% with 937 tests green, printing
# "below the 55% CDFI Fund threshold for full credit" to a CDE about a bar the
# Fund sets at 85%.
#
# The same defect class as win_probability's "40-point minimum" and
# excel_builder's weight_map, both removed earlier in 1.2.1: a display literal
# beside a comparison that reads the constant, so the printed explanation and
# the applied rule are joined by nothing but a coincidence of typing.
#
# RULE, same as renderers/_methodology: no federal figure is typed here. If a
# number in this module describes a CDFI Fund bar, it comes from
# nmtcapp/data/benchmark_thresholds and is pinned in tests/pinned_constants.txt
# against the string it renders.
_SEVERE_PCT_TEXT = f"{SEVERE_DISTRESS_MIN_PCT:.0%}"
_DEEP_PCT_TEXT = f"{DEEP_DISTRESS_MIN_PCT:.0%}"
_UNRELATED_PCT_TEXT = f"{UNRELATED_ENTITIES_MIN_PCT:.0%}"
_ALIGNMENT_PCT_TEXT = f"{TRACK_RECORD_PIPELINE_ALIGNMENT_MIN:.0%}"
_DEPLOYMENT_PCT_TEXT = f"{TRACK_RECORD_DEPLOYMENT_MIN:.0%}"
_DBC_VOLUME_PCT_TEXT = f"{DBC_VOLUME_PCT_MIN:.0%}"

# The aggregate BASE denominator is the two scored sections, not a third
# constant. Typing 100 beside two constants that sum to it is the same hazard
# as everything above: move either section maximum and the printed denominator
# stops describing the score it sits under.
_AGGREGATE_MAX = BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX

# NOT A CDFI FUND BAR, and the rendered sentence now says so. The 90%/98%
# eligibility figures were printed as a "competitive threshold" and a target,
# with no source; they are this package's own winner-pattern bands from
# benchmark_thresholds.WINNER_PATTERN_THRESHOLDS, whose own section header says
# they are "inferred from award announcements, not published by the CDFI Fund".
# The constant now supplies the number and the sentence supplies the
# disclaimer, so the two cannot drift apart.
_ELIGIBLE_COMPETITIVE_PCT = WINNER_PATTERN_THRESHOLDS["min_eligible_pct"]["competitive"]
_ELIGIBLE_STRONG_PCT = WINNER_PATTERN_THRESHOLDS["min_eligible_pct"]["strong"]
_ELIGIBLE_COMPETITIVE_TEXT = f"{_ELIGIBLE_COMPETITIVE_PCT:.0%}"
_ELIGIBLE_STRONG_TEXT = f"{_ELIGIBLE_STRONG_PCT:.0%}"


@dataclass
class Recommendation:
    """A single actionable recommendation for improving NMTC application competitiveness.

    All fields are populated — ``action`` and ``quantified_improvement`` are
    always specific and measurable. ``citation`` references the specific CDFI
    Fund document section supporting the recommendation.
    """
    category: str                # "business_strategy" | "community_outcomes" | "priority_points" | "pipeline"
    priority: str                # "critical", "high", "medium"
    finding: str                 # what the analysis found
    action: str                  # specific action to take
    expected_impact: str         # qualitative outcome
    quantified_improvement: str  # numeric estimate of score/metric change
    citation: str = ""           # CDFI Fund document section / source

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "priority": self.priority,
            "finding": self.finding,
            "action": self.action,
            "expected_impact": self.expected_impact,
            "quantified_improvement": self.quantified_improvement,
            "citation": self.citation,
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
            "=" * 70,
            "  RECOMMENDATIONS",
            f"  {self.overall_assessment}",
            "=" * 70,
        ]
        priority_order = [("critical", "[!]"), ("high", "[H]"), ("medium", "[M]")]
        for priority, symbol in priority_order:
            recs = [r for r in self.recommendations if r.priority == priority]
            if not recs:
                continue
            lines.append(f"\n  {symbol} {priority.upper()} PRIORITY")
            lines.append(f"  {'─'*64}")
            for r in recs:
                lines.extend([
                    f"  Category:  {r.category.replace('_', ' ').title()}",
                    f"  Finding:   {r.finding}",
                    f"  Action:    {r.action}",
                    f"  Impact:    {r.expected_impact}",
                    f"  Estimate:  {r.quantified_improvement}",
                    f"  Citation:  {r.citation}" if r.citation else "",
                    "",
                ])
        lines.append("=" * 70)
        return "\n".join(l for l in lines)

    def to_dict(self) -> dict:
        return {
            "overall_assessment": self.overall_assessment,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "quick_wins": [r.to_dict() for r in self.quick_wins],
            "strategic_changes": [r.to_dict() for r in self.strategic_changes],
        }


class RecommendationEngine:
    """Generate actionable, CDFI Fund-cited recommendations from scoring results.

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
        """
        recs: List[Recommendation] = []

        if win_score is not None:
            recs.extend(self._business_strategy_recs(win_score))
            recs.extend(self._community_outcomes_recs(win_score, pipeline_result))
            recs.extend(self._priority_points_recs(win_score))
            recs.extend(self._gating_recs(win_score))
        else:
            # Fall back to pipeline-only recommendations when no score available
            recs.extend(self._pipeline_fallback_recs(pipeline_result))

        priority_rank = {"critical": 0, "high": 1, "medium": 2}
        recs.sort(key=lambda r: priority_rank.get(r.priority, 3))

        assessment = self._overall_assessment(win_score)
        return RecommendationSet(recommendations=recs, overall_assessment=assessment)

    # ------------------------------------------------------------------
    # Business Strategy recommendations
    # ------------------------------------------------------------------

    def _business_strategy_recs(
        self, win_score: "WinProbabilityScore"
    ) -> List[Recommendation]:
        recs = []
        bs = win_score.business_strategy

        # Product Flexibility (10 pts)
        pf = bs.get("product_flexibility", 0)
        if pf < 8:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                finding=(
                    f"Product Flexibility score is {pf}/10. "
                    "The CDFI Fund awards full credit for CDEs offering 50%+ below-market "
                    "products OR documenting 5+ indicia of flexible terms."
                ),
                action=(
                    "Document 5 or more product flexibility indicia: longer maturities, "
                    "lower origination fees, equity-like features, reduced collateral "
                    "requirements, below-market interest rates, extended interest-only periods, "
                    "or technical assistance grants. Quantify the below-market rate discount "
                    "as a percentage of market-rate comparables."
                ),
                expected_impact=(
                    "Reach full Product Flexibility credit; 2–4 additional Business Strategy points."
                ),
                quantified_improvement=f"Estimated +{10-pf} points (Product Flexibility: {pf}/10 → 10/10).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Product Flexibility",
            ))
        elif pf < 10:
            recs.append(Recommendation(
                category="business_strategy",
                priority="medium",
                finding=f"Product Flexibility is {pf}/10 — one or two indicia short of full credit.",
                action=(
                    "Add 1–2 additional flexible product features or document them more explicitly "
                    "in the narrative. Technical assistance grants or equity co-investment features "
                    "are highly credible differentiators."
                ),
                expected_impact="Reach full Product Flexibility score.",
                quantified_improvement=f"Estimated +{10-pf} points (Product Flexibility: {pf}/10 → 10/10).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Product Flexibility",
            ))

        # Pipeline Credibility (15 pts)
        pc = bs.get("pipeline_credibility", 0)
        if pc < 10:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                finding=(
                    f"Pipeline Credibility is {pc}/15. Fewer than 80% of pipeline projects "
                    "have signed LOIs or executed commitment letters."
                ),
                action=(
                    "Obtain signed LOIs or letters of intent for all identified projects before "
                    "submission. For projects without LOIs, document specific sizing, timing, "
                    "and counterparty name. The CDFI Fund looks for a credible deployment timeline."
                ),
                expected_impact="Significantly improve Pipeline Credibility sub-score.",
                quantified_improvement=f"Estimated +{15-pc} points (Pipeline Credibility: {pc}/15 → 15/15).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Business Plan/Pipeline",
            ))
        elif pc < 13:
            recs.append(Recommendation(
                category="business_strategy",
                priority="medium",
                finding=f"Pipeline Credibility is {pc}/15. A few projects lack documented sizing or LOIs.",
                action=(
                    "Strengthen documentation for the remaining unsigned projects. "
                    "Include project-level financial projections and realistic deployment timeline."
                ),
                expected_impact="Incremental Pipeline Credibility improvement.",
                quantified_improvement=f"Estimated +{15-pc} points (Pipeline Credibility: {pc}/15 → 15/15).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Business Plan/Pipeline",
            ))

        # Track Record Strength (15 pts)
        trs = bs.get("track_record_strength", 0)
        if trs < 9:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                finding=(
                    f"Track Record Strength is {trs}/{TRACK_RECORD_STRENGTH_MAX}. The CDFI Fund looks for a 5-year "
                    "direct financing record and bonus credit if the applicant has committed "
                    "own capital alongside QEIs."
                ),
                action=(
                    "Emphasize in Section A narrative the full 5-year history of direct financing "
                    "transactions with QALICBs. If the CDE or its parent has co-invested balance-sheet "
                    "capital alongside any QEI, document the specific amount and share — this is "
                    "explicitly cited as a differentiator in the Review Process document."
                ),
                expected_impact="Improve Track Record Strength sub-score significantly.",
                quantified_improvement=f"Estimated +{15-trs} points (Track Record: {trs}/15 → 15/15).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Track Record",
            ))

        # Track Record Alignment (10 pts)
        tra = bs.get("track_record_alignment", 0)
        if tra < 8:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                finding=(
                    f"Track Record Alignment is {tra}/{TRACK_RECORD_ALIGNMENT_MAX}. The CDFI Fund "
                    f"requires {_ALIGNMENT_PCT_TEXT}+ of NMTC pipeline to be supported by "
                    f"similar prior activity AND {_DEPLOYMENT_PCT_TEXT}+ of prior "
                    "allocation deployed on schedule."
                ),
                action=(
                    f"Map at least {_ALIGNMENT_PCT_TEXT} of the NMTC pipeline projects to comparable prior direct "
                    "financing transactions (same sector, geography, or borrower profile). "
                    f"If deployment rate is below {_DEPLOYMENT_PCT_TEXT}, document catch-up plan and explain any delay."
                ),
                expected_impact="Reach both Track Record Alignment thresholds for full credit.",
                quantified_improvement=f"Estimated +{10-tra} points (Track Record Alignment: {tra}/10 → 10/10).",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Track Record",
            ))

        return recs

    # ------------------------------------------------------------------
    # Community Outcomes recommendations
    # ------------------------------------------------------------------

    def _community_outcomes_recs(
        self,
        win_score: "WinProbabilityScore",
        pipeline_result: "PipelineAnalysisResult",
    ) -> List[Recommendation]:
        recs = []
        co = win_score.community_outcomes
        d = pipeline_result.distress_breakdown

        # Partial score: the distress sub-scores are None (unassessable), so
        # distress-gap recommendations would be built from unverified data.
        # Emit the restore-data action instead — never fabricated targets.
        hdt = co.get("higher_distress_targeting", 0)
        ddc = co.get("deep_distress_commitment", 0)
        if hdt is None or ddc is None:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="critical",
                finding=(
                    "Higher Distress Targeting (15 pts) and Deep Distress "
                    "Commitment (10 pts) could not be assessed — eligibility "
                    "data is unavailable or projects are location-unverified."
                ),
                action=(
                    "Restore nmtc-mapper eligibility data access and/or resolve "
                    "project geocode failures, re-run the analysis, and re-score "
                    "before acting on any distress-targeting changes."
                ),
                expected_impact=(
                    "Unlocks assessment of the 25 base points currently excluded "
                    "from the Community Outcomes section."
                ),
                quantified_improvement="Not quantifiable until eligibility data is verified.",
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes",
            ))

        # Higher Distress Targeting (15 pts) — tract-derived, skip when unassessable
        severe_pct = d.get("pct_deep_or_severe", 0.0)
        if hdt is not None and hdt < 12:
            gap_pp = round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="critical",
                finding=(
                    f"Higher Distress Targeting is {hdt}/{HIGHER_DISTRESS_MAX}. Only {severe_pct:.0%} of QEI is "
                    f"in severe distress or multi-indicia distress tracts — below the "
                    f"{_SEVERE_PCT_TEXT} CDFI Fund threshold for full credit."
                ),
                action=(
                    f"Replace at least {gap_pp} percentage points of standard-LIC pipeline with "
                    "projects in census tracts meeting the CDFI Fund's severe distress or "
                    "multi-indicia distress criteria. Use the CDFI Fund's NMTC Mapping Tool to "
                    "identify qualifying tracts in your target markets."
                ),
                expected_impact=(
                    "Bring Higher Distress Targeting to full credit; this is the highest-weighted "
                    "Community Outcomes criterion and directly affects gating."
                ),
                quantified_improvement=(
                    f"Estimated +{HIGHER_DISTRESS_MAX - hdt} points (Higher Distress: "
                    f"{hdt}/{HIGHER_DISTRESS_MAX} → {HIGHER_DISTRESS_MAX}/{HIGHER_DISTRESS_MAX})."
                ),
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes, Higher Distress Targeting",
            ))
        elif hdt is not None and hdt < 15:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="medium",
                finding=(
                    f"Higher Distress Targeting is {hdt}/{HIGHER_DISTRESS_MAX} — close to "
                    f"but below the {_SEVERE_PCT_TEXT} threshold."
                ),
                action=(
                    f"Add {round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)}pp of deeper-distress projects to "
                    f"reach the {_SEVERE_PCT_TEXT} full-credit threshold. Target tracts at ≤60% AMI or ≥30% "
                    "poverty rate to maximize the distress classification."
                ),
                expected_impact="Reach full Higher Distress Targeting credit.",
                quantified_improvement=f"Estimated +{HIGHER_DISTRESS_MAX - hdt} points (Higher Distress: {hdt}/{HIGHER_DISTRESS_MAX} → {HIGHER_DISTRESS_MAX}/{HIGHER_DISTRESS_MAX}).",
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes, Higher Distress Targeting",
            ))

        # Deep Distress Commitment (10 pts) — tract-derived, skip when unassessable
        if ddc is not None and ddc < 7:
            deep_pct = d.get("pct_deep", d.get("pct_deep_or_severe", 0.0) * 0.5)
            gap_pp = round((DEEP_DISTRESS_MIN_PCT - deep_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="high",
                finding=(
                    f"Deep Distress Commitment is {ddc}/{DEEP_DISTRESS_MAX}. "
                    f"Only {deep_pct:.0%} of QEI is in CDFI Fund-designated Deep Distress tracts "
                    f"— {gap_pp}pp below the {_DEEP_PCT_TEXT} threshold for full credit."
                ),
                action=(
                    "Identify and add pipeline projects in CDFI Fund Deep Distress areas. "
                    "These are distinct from severe distress — check the NMTC Mapping Tool for "
                    "tracts explicitly classified as 'Deep Distress' in CY 2024-2025 data."
                ),
                expected_impact="Add Deep Distress credit; improves both section score and gating position.",
                quantified_improvement=(
                    f"Estimated +{DEEP_DISTRESS_MAX - ddc} points (Deep Distress: "
                    f"{ddc}/{DEEP_DISTRESS_MAX} → {DEEP_DISTRESS_MAX}/{DEEP_DISTRESS_MAX})."
                ),
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes, Deep Distress Commitment",
            ))

        # Special Targeting (5 pts) — derived from tract flags; skip when the
        # tract data behind those flags is unverified (hdt/ddc unassessable)
        st = co.get("special_targeting", 0)
        if hdt is not None and ddc is not None and st < 3:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="medium",
                finding=(
                    f"Special Targeting is {st}/5. The CDFI Fund awards up to 5 bonus points "
                    "for QEI in U.S. Territories, High Migration Rural Counties, NMTC Native Areas, "
                    "or Persistent Poverty Counties."
                ),
                action=(
                    "Add 1–2 projects in qualifying Special Targeting areas. "
                    # THE PARENTHETICAL DEFINITION IS GONE, NOT CORRECTED.
                    #
                    # It read "Persistent Poverty Counties (100+ years at ≥20%
                    # poverty)". No federal designation is defined over 100
                    # years — a Persistent Poverty County is measured over
                    # THREE DECADES, across consecutive decennial censuses and
                    # the current ACS — so the figure was wrong by more than
                    # threefold, in live text telling a CDE which targeting
                    # category to pursue.
                    #
                    # It is DELETED rather than replaced with 30. This tool
                    # does not determine the designation, holds no county list,
                    # and cannot cite one; substituting a number nobody here
                    # checked against a primary source would relocate the
                    # defect rather than remove it. The sentence now points at
                    # the authority that does publish the list, which is what
                    # the CDE has to consult anyway.
                    "Persistent Poverty Counties are the most accessible "
                    "category for most CDEs. The county list is the CDFI "
                    "Fund's, not this tool's — check a county against the "
                    "Fund's published Persistent Poverty County designation "
                    "before relying on it. NMTC Native Areas and High "
                    "Migration Rural Counties offer additional credit. "
                    "All four categories are identified in the CY 2024-2025 Allocation Application."
                ),
                expected_impact="Gain 1–3 additional Community Outcomes points from special targeting.",
                quantified_improvement=f"Estimated +{5-st} points (Special Targeting: {st}/5 → 5/5).",
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes, Special Targeting (CY 2024-2025 priority)",
            ))

        # Community Outcomes Quality (10 pts)
        coq = co.get("community_outcomes_quality", 0)
        if coq < 8:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="high",
                finding=(
                    f"Community Outcomes Quality is {coq}/10. The CDFI Fund requires "
                    "quantified projections (jobs, units, sq ft) supported by a documented "
                    "third-party methodology."
                ),
                action=(
                    "Commission or cite a third-party impact methodology for job creation estimates. "
                    "IMPLAN, RIMS II, or an academic partnership are credible options. "
                    "Ensure all pipeline projects report concrete outcomes: FTE jobs created, "
                    "jobs retained, affordable units, and commercial square footage."
                ),
                expected_impact="Improve Outcomes Quality to near-full credit.",
                quantified_improvement=f"Estimated +{10-coq} points (Outcomes Quality: {coq}/10 → 9/10).",
                citation=f"{_SOURCE_DOC}, Section II.C.2 — Community Outcomes, Quality of Community Outcomes",
            ))

        # Community Accountability (10 pts)
        ca = co.get("community_accountability", 0)
        if ca < 8:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="high",
                finding=(
                    f"Community Accountability is {ca}/10. The CDFI Fund values LIC resident "
                    "representation on the board AND documented community engagement history."
                ),
                action=(
                    "Increase LIC resident or community representative board seats to at least "
                    "33% of total board members. If below 33%, add 1–2 community seats before "
                    "submission. Document specific community engagement activities (town halls, "
                    "advisory committees, community surveys) with dates and participation numbers."
                ),
                expected_impact="Improve Community Accountability score by 2–4 points.",
                quantified_improvement=f"Estimated +{10-ca} points (Accountability: {ca}/10 → 10/10).",
                citation=f"{_SOURCE_DOC}, Section II.C.3 — Community Outcomes, Community Accountability",
            ))

        return recs

    # ------------------------------------------------------------------
    # Priority Points recommendations
    # ------------------------------------------------------------------

    def _priority_points_recs(
        self, win_score: "WinProbabilityScore"
    ) -> List[Recommendation]:
        recs = []
        pp = win_score.priority_points

        dbc = pp.get("dbc_track_record", 0)
        if dbc < 4:
            recs.append(Recommendation(
                category="priority_points",
                priority="medium",
                finding=(
                    f"DBC Track Record Priority Points are {dbc}/5. "
                    f"Full credit requires {DBC_PRIORITY_YEARS_MIN}+ years of DBC focus AND {_DBC_VOLUME_PCT_TEXT}+ of direct "
                    "financing volume to Disadvantaged Businesses/Communities."
                ),
                action=(
                    f"Document DBC lending history going back {DBC_PRIORITY_YEARS_MIN}+ years. If volume is below {_DBC_VOLUME_PCT_TEXT}, "
                    "shift the pipeline toward CDFI-certified DBCs, minority-owned businesses, "
                    "or businesses in QCTs with documented economic disadvantage."
                ),
                expected_impact="Earn up to 5 additional priority points.",
                quantified_improvement=f"Estimated +{5-dbc} priority points (DBC: {dbc}/5 → 5/5).",
                citation=f"{_SOURCE_DOC}, Section III — Priority Points, DBC Track Record",
            ))

        ue = pp.get("unrelated_entities", 0)
        if ue < 4:
            recs.append(Recommendation(
                category="priority_points",
                priority="medium",
                finding=(
                    f"Unrelated Entities Priority Points are {ue}/5. "
                    f"Full credit requires committing substantially all ({_UNRELATED_PCT_TEXT}+) QEIs to "
                    "entities unrelated to the CDE."
                ),
                action=(
                    "Review pipeline for any related-party transactions. "
                    "If any QEIs go to CDE affiliates, replace with unrelated QALICB projects "
                    f"to reach the {_UNRELATED_PCT_TEXT} unrelated threshold."
                ),
                expected_impact="Earn unrelated entity priority points with minimal pipeline changes.",
                quantified_improvement=f"Estimated +{5-ue} priority points (Unrelated: {ue}/5 → 5/5).",
                citation=f"{_SOURCE_DOC}, Section III — Priority Points, Unrelated Entities",
            ))

        return recs

    # ------------------------------------------------------------------
    # Gating recommendations (most important if not Highly Qualified)
    # ------------------------------------------------------------------

    def _gating_recs(self, win_score: "WinProbabilityScore") -> List[Recommendation]:
        recs = []
        if win_score.tier == "Not Qualified":
            bs = win_score.business_strategy.get("section_total", 0)
            co = win_score.community_outcomes.get("section_total", 0)
            agg = win_score.aggregate_base_score

            if bs < HIGHLY_QUALIFIED_SECTION_MIN:
                recs.append(Recommendation(
                    category="business_strategy",
                    priority="critical",
                    finding=(
                        f"Business Strategy section score ({bs}/{BUSINESS_STRATEGY_MAX}) is below "
                        f"the {HIGHLY_QUALIFIED_SECTION_MIN}-point "
                        "minimum required to reach the Highly Qualified pool. "
                        "Applications that miss either section minimum do not advance to Phase 2."
                    ),
                    action=(
                        "Focus immediately on the lowest-scoring Business Strategy sub-criteria: "
                        "Product Flexibility, Pipeline Credibility, and Track Record. "
                        f"You need at least {HIGHLY_QUALIFIED_SECTION_MIN} points in this section to be considered."
                    ),
                    expected_impact="Meet the section minimum gating threshold; allow Phase 2 consideration.",
                    quantified_improvement=(
                        f"Need {HIGHLY_QUALIFIED_SECTION_MIN - bs} more Business Strategy "
                        "points to reach gating minimum."
                    ),
                    citation=(
                        f"{_SOURCE_DOC}, Highly Qualified gating — both sections "
                        f"must score ≥ {HIGHLY_QUALIFIED_SECTION_MIN}"
                    ),
                ))

            if co < HIGHLY_QUALIFIED_SECTION_MIN:
                recs.append(Recommendation(
                    category="community_outcomes",
                    priority="critical",
                    finding=(
                        f"Community Outcomes section score ({co}/{COMMUNITY_OUTCOMES_MAX}) is below "
                        f"the {HIGHLY_QUALIFIED_SECTION_MIN}-point "
                        "minimum required to reach the Highly Qualified pool."
                    ),
                    action=(
                        f"Prioritize Higher Distress Targeting ({HIGHER_DISTRESS_MAX} pts max) and "
                        f"Deep Distress Commitment ({DEEP_DISTRESS_MAX} pts max) as the "
                        "largest available point pools. "
                        "Adding 1–2 deep-distress projects can rapidly close the gap."
                    ),
                    expected_impact="Meet the section minimum; allow application to advance to Phase 2.",
                    quantified_improvement=(
                        f"Need {HIGHLY_QUALIFIED_SECTION_MIN - co} more Community Outcomes "
                        "points to reach gating minimum."
                    ),
                    citation=(
                        f"{_SOURCE_DOC}, Highly Qualified gating — both sections "
                        f"must score ≥ {HIGHLY_QUALIFIED_SECTION_MIN}"
                    ),
                ))

            if (bs >= HIGHLY_QUALIFIED_SECTION_MIN and co >= HIGHLY_QUALIFIED_SECTION_MIN
                    and agg < HIGHLY_QUALIFIED_AGGREGATE_MIN):
                recs.append(Recommendation(
                    category="community_outcomes",
                    priority="critical",
                    finding=(
                        f"Both sections meet the {HIGHLY_QUALIFIED_SECTION_MIN}-point minimum but "
                        f"aggregate score ({agg}/{_AGGREGATE_MAX}) is below "
                        f"{HIGHLY_QUALIFIED_AGGREGATE_MIN} — the Highly Qualified threshold."
                    ),
                    action=(
                        "Focus on the sub-criteria with the most remaining points in both sections. "
                        f"You need {HIGHLY_QUALIFIED_AGGREGATE_MIN - agg} more aggregate points. Targeting 3–4 improvements "
                        "across both sections is typically more achievable than maximizing one."
                    ),
                    expected_impact=f"Cross the {HIGHLY_QUALIFIED_AGGREGATE_MIN}-point Highly Qualified threshold.",
                    quantified_improvement=(
                        f"Need {HIGHLY_QUALIFIED_AGGREGATE_MIN - agg} more aggregate points "
                        f"to reach {HIGHLY_QUALIFIED_AGGREGATE_MIN} (Highly Qualified)."
                    ),
                    citation=(
                        f"{_SOURCE_DOC}, Highly Qualified gating — aggregate "
                        f"score must be ≥ {HIGHLY_QUALIFIED_AGGREGATE_MIN}"
                    ),
                ))
        return recs

    # ------------------------------------------------------------------
    # Fallback recommendations (no score available)
    # ------------------------------------------------------------------

    def _pipeline_fallback_recs(
        self, result: "PipelineAnalysisResult"
    ) -> List[Recommendation]:
        recs = []
        d = result.distress_breakdown
        severe_pct = d.get("pct_deep_or_severe", 0.0)

        if severe_pct < SEVERE_DISTRESS_MIN_PCT:
            gap_pp = round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="critical",
                finding=(
                    f"Severe/deep distress concentration is {severe_pct:.0%} — "
                    f"below the CDFI Fund's {_SEVERE_PCT_TEXT} threshold for full Higher Distress Targeting credit."
                ),
                action=(
                    f"Replace {gap_pp}pp of standard-LIC pipeline with projects in severe "
                    "distress or multi-indicia distress census tracts."
                ),
                expected_impact="Reach full Higher Distress Targeting credit (15/15 pts).",
                quantified_improvement=(
                    f"Estimated {_SEVERE_PCT_TEXT} → {severe_pct:.0%} gap requires adding "
                    f"{gap_pp}pp of deep-distress QEI."
                ),
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Higher Distress Targeting",
            ))

        if result.eligibility_pct < _ELIGIBLE_COMPETITIVE_PCT:
            recs.append(Recommendation(
                category="business_strategy",
                priority="critical",
                finding=(
                    f"NMTC eligibility rate is {result.eligibility_pct:.0%} — below the "
                    f"{_ELIGIBLE_COMPETITIVE_TEXT} competitive band of this tool's own "
                    "winner-pattern comparison (an unsourced house heuristic, not a "
                    "CDFI Fund threshold)."
                ),
                action=(
                    "Verify census tract eligibility for all pipeline projects using the "
                    f"CDFI Fund NMTC Mapping Tool. Remove or replace ineligible projects. "
                    f"Target ≥{_ELIGIBLE_STRONG_TEXT}."
                ),
                expected_impact="Ensure QEI is deployable; improve Pipeline Credibility score.",
                quantified_improvement="Reaching 98% eligibility significantly improves Pipeline Credibility.",
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Pipeline",
            ))

        return recs

    # ------------------------------------------------------------------
    # Overall assessment
    # ------------------------------------------------------------------

    def _overall_assessment(self, win_score: Optional["WinProbabilityScore"]) -> str:
        if win_score is None:
            return (
                "Analysis complete. Review recommendations below to improve "
                "alignment with the CDFI Fund's CY 2024-2025 Review Process criteria."
            )
        # Partial guard, mirroring win_probability._build_peer_comparison.
        # Without it a degraded run fell through to the "Not Qualified" branch
        # and printed a verdict like "Not Qualified (65/100) — Community
        # Outcomes 40/50 < 40" against /50 and /100 denominators that were
        # never available: 25 of the 100 base points could not be scored.
        if getattr(win_score, "partial", False):
            return (
                "NOT RATED — eligibility data unavailable. "
                f"{getattr(win_score, 'partial_note', '')}. "
                "No qualification verdict can be given from a partial score. "
                "Restore nmtc-mapper data access and re-run before drawing any "
                "conclusion about competitiveness."
            )

        tier = win_score.tier
        agg = win_score.aggregate_base_score
        bs = win_score.business_strategy.get("section_total", 0)
        co = win_score.community_outcomes.get("section_total", 0)

        if tier == "Top Tier":
            return (
                f"Top Tier ({agg}/{_AGGREGATE_MAX}). Business Strategy: {bs}/{BUSINESS_STRATEGY_MAX}, "
                f"Community Outcomes: {co}/{COMMUNITY_OUTCOMES_MAX}. Both sections exceed the "
                f"{TOP_TIER_SECTION_MIN}-point threshold. "
                # "Top Tier" is this package's own label and the two cut points
                # behind it are unsourced. The CDFI Fund publishes the Highly
                # Qualified gate and nothing above it, so a CDE reading this
                # line must not take the ranking for a federal one.
                "(\"Top Tier\" is this tool's own label: the CDFI Fund publishes "
                "no tier above Highly Qualified, and the cut points behind it "
                "are an unsourced house heuristic, not a CDFI Fund threshold.) "
                "Focus on Phase 2 preparation (Management Capacity, Capitalization Strategy)."
            )
        if tier == "Highly Qualified":
            return (
                f"Highly Qualified ({agg}/{_AGGREGATE_MAX}). Business Strategy: {bs}/{BUSINESS_STRATEGY_MAX}, "
                f"Community Outcomes: {co}/{COMMUNITY_OUTCOMES_MAX}. Both sections meet the "
                f"{HIGHLY_QUALIFIED_SECTION_MIN}-point gating minimum. "
                "Priority changes below can improve ranking within the Highly Qualified pool."
            )
        # Not Qualified
        gaps = []
        if bs < HIGHLY_QUALIFIED_SECTION_MIN:
            gaps.append(f"Business Strategy {bs}/{BUSINESS_STRATEGY_MAX} < {HIGHLY_QUALIFIED_SECTION_MIN}")
        if co < HIGHLY_QUALIFIED_SECTION_MIN:
            gaps.append(f"Community Outcomes {co}/{COMMUNITY_OUTCOMES_MAX} < {HIGHLY_QUALIFIED_SECTION_MIN}")
        if agg < HIGHLY_QUALIFIED_AGGREGATE_MIN:
            gaps.append(
                f"aggregate {agg}/{_AGGREGATE_MAX} < {HIGHLY_QUALIFIED_AGGREGATE_MIN}")
        gap_str = "; ".join(gaps) if gaps else f"aggregate {agg}/{_AGGREGATE_MAX}"
        return (
            f"Not Qualified ({agg}/100) — {gap_str}. "
            "Address Critical recommendations first to meet gating thresholds."
        )
