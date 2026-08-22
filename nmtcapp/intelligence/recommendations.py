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
    HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA,
    SEVERE_DISTRESS_MIN_PCT,
    HOUSE_TOP_TIER_SECTION_MIN,
    TRACK_RECORD_ALIGNMENT_MAX,
    TRACK_RECORD_STRENGTH_MAX,
    HOUSE_TRACK_RECORD_DEPLOYMENT_MIN,
    TRACK_RECORD_PIPELINE_ALIGNMENT_MIN,
    TRACK_RECORD_TO_PROJECTION_MIN,
    HOUSE_UNRELATED_ENTITIES_MIN_PCT,
    WINNER_PATTERN_THRESHOLDS,
)

from nmtcapp.intelligence.cde_inputs import SUBSCORE_LABELS
from nmtcapp.renderers._round_provenance import round_provenance_paragraphs

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
_UNRELATED_PCT_TEXT = f"{HOUSE_UNRELATED_ENTITIES_MIN_PCT:.0%}"
_ALIGNMENT_PCT_TEXT = f"{TRACK_RECORD_PIPELINE_ALIGNMENT_MIN:.0%}"
_DEPLOYMENT_PCT_TEXT = f"{HOUSE_TRACK_RECORD_DEPLOYMENT_MIN:.0%}"
_FUND_TRACK_TO_PROJECTION_TEXT = f"{TRACK_RECORD_TO_PROJECTION_MIN:.0%}"
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


#: WHAT THE FUND SCORES BEHIND EACH SUB-SCORE, AND WHERE THE CDE SUPPLIES IT.
#:
#: The disclosure that replaces an instruction (1.5.4 T2) is not silence and is
#: not a shorter instruction. It states three things, and it needs all three or
#: it is worse than what it replaced:
#:
#:   1. the input was NOT SUPPLIED -- so the CDE can tell a blank from a zero;
#:   2. the CDFI Fund nevertheless scores the underlying criterion, and here is
#:      the criterion -- so the CDE does not conclude the field is optional;
#:   3. where to put the value -- so the disclosure is actionable.
#:
#: (2) is what gives the disclosure a basis. It is a statement about the Fund's
#: own published criterion, not about this CDE's position, so it survives the
#: principle that removed the instruction: the tool may say what the Fund
#: scores; it may not tell a CDE to change something it never measured.
#:
#: The ``fund`` sentences below are LIFTED from the items they replace rather
#: than rewritten, so the sourcing work done in 1.2.2 (D1, D2, D3, D5) is not
#: quietly discarded on the path a CDE with an empty profile actually takes --
#: which is the only path the shipped scaffold produced.
#: EVERY KEY HERE IS REACHABLE, AND TWO WERE NOT (1.5.4 audit close, B4).
#: ``special_targeting`` and ``unrelated_entities`` carried entries that
#: ``unsupplied_inputs`` can never ask for. Proved by exhausting all 2^17 =
#: 131,072 presence combinations of the seventeen scoring inputs: the emitted
#: set is the same seven sub-scores every time, and neither of those two is
#: among them.
#:
#: THE CAUSE IS THE REGISTRY'S OWN RULE, WORKING CORRECTLY. ``unsupplied_inputs``
#: skips any input with a ``measured_substitute``; ``special_targeting``'s only
#: two inputs (``pct_persistent_poverty``, ``pct_us_territories``) both have
#: one, and ``unrelated_entities``' single input does too.
#:
#: RULED: DELETED, not made reachable. The alternative was widening
#: ``unsupplied_inputs`` to report them, and that would REVERSE a correct
#: ruling -- both sub-scores ARE scored, from a QEI-weighted measurement of
#: this CDE's own pipeline, so printing "NOT SCORED" over them would be a new
#: false statement in the opposite direction. That is the error
#: ``test_a_cde_that_supplies_everything_is_still_given_scores`` exists to
#: catch, and shipping it here to justify a dictionary entry would be the tail
#: wagging the tool.
#:
#: A ``fund_attribution_allowlist.txt`` row went with the ``unrelated_entities``
#: entry -- an allowlist adjudicating a Fund attribution in text that can never
#: render, which is the "registry entry that adjudicates nothing while
#: appearing to" shape a session correctly refused to create at 1.5.2. Removed
#: with the entry it ruled.
#:
#: ``tests/test_cde_scoring_inputs.py`` now DERIVES the reachable set from
#: ``CDE_SCORING_INPUTS`` and asserts these keys are exactly it, in both
#: directions, so a third unreachable entry fails instead of accumulating.
_NOT_SUPPLIED_BASIS = {
    "product_flexibility": (
        "business_strategy", "high",
        "Question 15 of the CY 2024-2025 NMTC Allocation Application "
        "(pp. 20-21) asks the Applicant to check ONE option committing that "
        "100% of its QLICIs will be provided as equity; equity-equivalent "
        "financing; debt at least 50% below market; or debt satisfying at "
        "least "
        f"{HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA} indicia of flexible or "
        "non-traditional terms. This tool's sub-score is not that test.",
        f"{_SOURCE_DOC}, Section II.A.1; CY 2024-2025 NMTC Allocation "
        "Application, Question 15 (pp. 20-21). Sub-score is this tool's own.",
    ),
    "pipeline_credibility": (
        "business_strategy", "high",
        "The CDFI Fund reviews whether the proposed pipeline is credible — "
        "identified projects, documented sizing and timing, and a deployment "
        "timeline it can believe.",
        f"{_SOURCE_DOC}, Section II.A — Business Strategy, Business Plan/Pipeline",
    ),
    "track_record_strength": (
        "business_strategy", "high",
        "The CDFI Fund looks for a 5-year direct financing record, and cites "
        "own capital committed alongside QEIs as a differentiator.",
        f"{_SOURCE_DOC}, Section II.A — Business Strategy, Track Record",
    ),
    "track_record_alignment": (
        "business_strategy", "high",
        "The CDFI Fund (Review Process p.7, Part II.A.4) looks for "
        f"{_ALIGNMENT_PCT_TEXT}+ of proposed NMTC investments to be supported "
        "by a track record of similar business and activity types, and for "
        "the most recent 5-year direct financing track record to be "
        f"{_FUND_TRACK_TO_PROJECTION_TEXT}+ of projected NMTC deployment in "
        "Exhibit A.",
        f"{_SOURCE_DOC}, Section II.A — Business Strategy, Track Record",
    ),
    "community_outcomes_quality": (
        "community_outcomes", "high",
        "The CDFI Fund scores whether community outcome projections are "
        "quantified (jobs, units, square footage) and supported by a "
        "documented third-party methodology.",
        f"{_SOURCE_DOC}, Section II.C.2 — Community Outcomes, Quality of "
        "Community Outcomes",
    ),
    "community_accountability": (
        "community_outcomes", "high",
        "The CDFI Fund values LIC resident representation on the governing "
        "board AND a documented community engagement history.",
        f"{_SOURCE_DOC}, Section II.C.3 — Community Outcomes, Community "
        "Accountability",
    ),
    "dbc_track_record": (
        "priority_points", "medium",
        f"Full credit under this tool requires {DBC_PRIORITY_YEARS_MIN}+ years "
        f"of DBC focus AND {_DBC_VOLUME_PCT_TEXT}+ of direct financing volume "
        "to Disadvantaged Businesses or Communities.",
        f"{_SOURCE_DOC}, Section III — Priority Points, DBC Track Record",
    ),
}

#: THE SHARE FLOOR (1.5.4 audit close, B2). A non-zero share may never render
#: as ``0%``, and a partial share may never render as ``100%``.
#:
#: THE DEFECT. T4 introduced three ``:.0%`` renders and gave none of them a
#: floor. Measured on ONE $50,000 ineligible project in a 20-project,
#: $114,050,000 pipeline -- a share of 0.0438% -- all three printed::
#:
#:     0% of pipeline QEI (1 of 20 projects) is in a census tract that is
#:     not a Low-Income Community. This is a statutory gate...
#:
#: On the assessment surface, which carried no project count at all, that
#: sentence read simply "0% of pipeline QEI is in tracts that are not a
#: Low-Income Community" -- an unqualified, false statement, in the release
#: whose entire purpose is removing false statements from this engine.
#:
#: THE MIRROR IS REAL TOO, and the audit that found the first end did not name
#: it. ``f"{0.996:.0%}"`` is ``"100%"``: a pipeline with one small ELIGIBLE
#: project among nineteen ineligible ones would state that 100% of its QEI is
#: in a tract that does not qualify, which is false in the direction that tells
#: a CDE its whole pipeline is dead. Same rounding, opposite end, so it is
#: closed here rather than left for the round that trips over it.
#:
#: THE THRESHOLD IS DERIVED FROM THE RENDER, NOT TYPED. Testing ``share <
#: 0.005`` would hard-code one format spec's rounding behaviour in a second
#: place -- two copies of one fact, joined by nothing, which is the shape this
#: package has recorded most often. This formats the number and asks what came
#: out, so it stays correct if the spec ever changes.
def _share_text(numerator: float, denominator: float) -> str:
    """A share of ``numerator`` in ``denominator``, floored at both ends."""
    share = numerator / denominator
    rendered = f"{share:.0%}"
    if rendered == "0%" and share > 0:
        return "<1%"
    if rendered == "100%" and share < 1:
        return ">99%"
    return rendered


#: Where a CDE puts the values. Named once; both sentences below read it.
_WHERE_TO_SUPPLY = (
    "the \"OPTIONAL — Win Alignment scoring inputs\" block of "
    "nmtcapp/templates/cde_profile_template.yaml (read into CDEProfile.extra), "
    "or the CDE Profile sheet of an uploaded workbook"
)


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
        """The recommendations, as text, headed by which round they score.

        THE ROUND NOTE IS READ, NOT RETYPED (1.5.4 T1). This surface cited the
        CY 2024-2025 Review Process thirteen times on a single run and said
        nothing about that round being closed and awarded, or about CY 2026
        being announced and not open. Markdown, Word, Excel and PDF have all
        carried ``_round_provenance`` since 1.5.0; this surface did not,
        because ``tests/test_round_provenance._ALL_FORMATS`` enumerates the
        four ``Application.generate()`` formats and a surface that is not one
        of them cannot appear in that list.

        Only the FIRST paragraph renders here. The other three are the
        re-check list, the AMIS certification deadline and the prior-Allocatee
        Subsidiary obligation -- all of which belong on a filing artifact and
        none of which is what a reader of a recommendation list needs in order
        to read the citations under the items correctly. The full note is on
        every generated document.
        """
        lines = [
            "=" * 70,
            "  RECOMMENDATIONS",
            f"  {self.overall_assessment}",
            "=" * 70,
            "",
            f"  {round_provenance_paragraphs()[0]}",
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
        # ELIGIBILITY PRECEDES RANKING (1.5.4 T4), so it is built first and the
        # sort below is stable. Everything after this is advice about POSITION:
        # where an application ranks against the Review Process criteria and,
        # if it clears the gate, within the Highly Qualified pool. None of it
        # reaches a project whose tract is not a Low-Income Community.
        recs: List[Recommendation] = list(self._eligibility_gate_recs(pipeline_result))

        if win_score is not None:
            recs.extend(self._business_strategy_recs(win_score))
            recs.extend(self._community_outcomes_recs(win_score, pipeline_result))
            recs.extend(self._priority_points_recs(win_score))
            recs.extend(self._gating_recs(win_score))
        else:
            # Fall back to pipeline-only recommendations when no score available
            recs.extend(self._pipeline_fallback_recs(pipeline_result))

        # STABLE, WHICH IS THE WHOLE POINT. ``list.sort`` preserves the order of
        # equal keys, so the statutory gate stays ahead of the other criticals
        # rather than landing wherever the sort happened to put it.
        priority_rank = {"critical": 0, "high": 1, "medium": 2}
        recs.sort(key=lambda r: priority_rank.get(r.priority, 3))

        assessment = self._overall_assessment(win_score, pipeline_result)
        return RecommendationSet(recommendations=recs, overall_assessment=assessment)

    # ------------------------------------------------------------------
    # Unsupplied inputs — disclose, never instruct (1.5.4 T2)
    # ------------------------------------------------------------------

    @staticmethod
    def _unsupplied(win_score: "WinProbabilityScore", subscore: str) -> tuple:
        """The CDE-declared inputs this sub-score needs and did not get."""
        return tuple(getattr(win_score, "unsupplied_inputs", {}).get(subscore, ()))

    def _not_supplied_rec(
        self, win_score: "WinProbabilityScore", subscore: str
    ) -> Recommendation:
        """A disclosure, in place of the instruction that used to render here.

        WHAT THIS REPLACES, MEASURED. On a CDE whose ``extra`` is empty -- which
        is what the shipped scaffold and the Streamlit upload path both
        produce -- ``community_accountability`` scored 0/10 out of
        ``attrs.get("lic_board_representation_pct", 0.0)`` and this engine
        emitted::

            Finding:  Community Accountability is 0/10. ...
            Action:   Increase LIC resident or community representative board
                      seats to at least 33% of total board members.

        to a CDE whose REQUIRED ``governance`` block declared 4 of 9 community
        representatives. 44%, told to reach 33%, in an action field.

        NO SCORE IS PRINTED HERE, and that is the first of the two rules. The
        model still computes one and ``WinProbabilityScore`` still carries it --
        1.5.4 moves no score -- but a fraction is how a reader is told a thing
        was measured, and part of this one is a ``.get`` default.

        THE PRIORITY IS INHERITED FROM THE ITEM THIS REPLACES, not raised. A
        disclosure that a field is blank is not more urgent than the sourced
        finding it stands in for, and inflating it would push real critical
        items down the page.
        """
        keys = self._unsupplied(win_score, subscore)
        category, priority, fund, citation = _NOT_SUPPLIED_BASIS[subscore]
        label = SUBSCORE_LABELS[subscore]
        key_list = ", ".join(f"`{k}`" for k in keys)
        plural = "these inputs were" if len(keys) > 1 else "this input was"
        return Recommendation(
            category=category,
            priority=priority,
            finding=(
                f"{label} — NOT SCORED. This tool cannot score it because "
                f"{plural} not supplied: {key_list}. No sub-score is stated "
                "here: an input that was not supplied is not a zero, and the "
                "figure the model computes from its absent-value defaults "
                f"would describe nothing. {fund}"
            ),
            action=(
                f"Supply {key_list} in {_WHERE_TO_SUPPLY}, then re-score. "
                "Until then this tool states nothing about "
                f"{label} and instructs nothing about it — it has not measured "
                "it, and advice built on a default is advice about the default."
            ),
            expected_impact=(
                f"Makes {label} scorable. Nothing about the application's "
                "position changes; what changes is that this tool stops "
                "reporting an absent field as a zero."
            ),
            quantified_improvement=(
                f"Not quantifiable until {len(keys)} input(s) named above are "
                "supplied. The CDFI Fund does score the criterion above; this "
                "tool does not score it for this CDE."
            ),
            citation=citation,
        )

    # ------------------------------------------------------------------
    # Eligibility gate (1.5.4 T4) — statutory, and it precedes everything
    # ------------------------------------------------------------------

    def _eligibility_gate_recs(
        self, result: "PipelineAnalysisResult"
    ) -> List[Recommendation]:
        """Say that the pipeline fails the LIC gate, before advising on rank.

        THE DEFECT. An all-ineligible pipeline emitted thirteen items and not
        one of them mentioned that the pipeline was ineligible. The items
        advised on improving rank within the Highly Qualified pool.

        LIC status is not a scored band. It is a statutory precondition, and no
        movement in any scored sub-criterion reaches a project whose tract does
        not qualify.

        MEASURED ON THE ``ineligible`` BUCKET, NOT ON ``eligibility_pct``, and
        the difference is a fabricated negative. ``eligibility_pct`` counts
        ``is_nmtc_eligible is True`` and therefore reads an UNVERIFIED project
        exactly like a DISQUALIFIED one -- it is 0.0 both for a pipeline the
        Fund's data says does not qualify and for one nobody could check.
        ``distress_breakdown['dollars_by_distress']['ineligible']`` holds only
        QEI whose tract was determined not to qualify; unverified QEI lands in
        ``unknown``. Unknown is not ineligible, and this gate never says it is.
        """
        if getattr(result, "eligibility_data_status", "ok") != "ok":
            return []
        breakdown = result.distress_breakdown or {}
        buckets = breakdown.get("dollars_by_distress") or {}
        counts = breakdown.get("project_count_by_distress") or {}
        ineligible_qei = buckets.get("ineligible", 0) or 0
        total_qei = result.total_qei_request or 0
        if ineligible_qei <= 0 or total_qei <= 0:
            return []

        n_ineligible = counts.get("ineligible", 0)
        n_total = result.total_projects
        unknown_qei = buckets.get("unknown", 0) or 0
        n_unknown = counts.get("unknown", 0)
        # THE COUNT TRAVELS WITH THE SHARE, on every surface that states one
        # (1.5.4 audit close, B2 rule 2). A share alone cannot distinguish TINY
        # from NONE, and this sentence is read by a CDE deciding whether its
        # pipeline has an undetermined-tract problem at all.
        unknown_note = (
            f" A further {_share_text(unknown_qei, total_qei)} of QEI "
            f"({n_unknown} of {n_total} projects) is in tracts this "
            "tool could not determine; that is reported as undetermined and is "
            "NOT counted as ineligible."
            if unknown_qei > 0 else ""
        )
        return [Recommendation(
            category="pipeline",
            priority="critical",
            finding=(
                f"{_share_text(ineligible_qei, total_qei)} of pipeline QEI "
                f"({n_ineligible} of {n_total} "
                "projects) is in a census tract that is not a Low-Income "
                "Community. This is a statutory gate, not a scored band: "
                "IRC §45D(d) requires each QLICI to be made in a qualified "
                "active low-income community business located in a Low-Income "
                "Community, and Treas. Reg. §1.45D-1(c)(5)(i) requires "
                "substantially all — at least 85 percent — of QEI proceeds to "
                "be invested in QLICIs. QEI attributed to a tract that does "
                "not qualify cannot count toward that test." + unknown_note
            ),
            action=(
                "Re-check each flagged project's tract against the CDFI Fund's "
                "NMTC Mapping Tool and replace, relocate or drop any project "
                "whose tract does not qualify. Do this before acting on the "
                "items below: those concern where an application RANKS against "
                "the Review Process criteria, and ranking does not reach QEI "
                "that cannot be deployed."
            ),
            expected_impact=(
                "Restores the affected QEI to deployable status. This is a "
                "precondition for the scored criteria below, not an addition "
                "to them."
            ),
            quantified_improvement=(
                "Not a point movement. Eligibility is statutory and this tool "
                "assigns it no score; the items below are scored and this one "
                "is not."
            ),
            citation=(
                "IRC §45D(d); Treas. Reg. §1.45D-1(c)(5)(i). NOT a "
                f"{_SOURCE_DOC} scoring criterion — a statutory precondition "
                "to being scored at all."
            ),
        )]

    # ------------------------------------------------------------------
    # Business Strategy recommendations
    # ------------------------------------------------------------------

    def _business_strategy_recs(
        self, win_score: "WinProbabilityScore"
    ) -> List[Recommendation]:
        recs = []
        bs = win_score.business_strategy

        # THE GUARD IS THE SAME SHAPE EVERYWHERE BELOW (1.5.4 T2), and it comes
        # BEFORE the band test on purpose. The band test reads a number built
        # partly out of ``.get`` defaults, so gating the disclosure on it would
        # be circular: a CDE that supplied nothing could be scored above the
        # threshold by the defaults alone and then told nothing at all.
        # ``has_quantified_outcomes`` defaults to True, which is exactly that
        # case waiting to happen.
        # Product Flexibility (10 pts)
        pf = bs.get("product_flexibility", 0)
        if self._unsupplied(win_score, "product_flexibility"):
            recs.append(self._not_supplied_rec(win_score, "product_flexibility"))
        elif pf < 8:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                # D1 (1.2.2 round 2). This read: "The CDFI Fund awards full
                # credit for CDEs offering 50%+ below-market products OR
                # documenting 5+ indicia of flexible terms." Every clause of
                # that was wrong about the Fund. Question 15 is a single-select
                # ladder, its percentages are per-loan discount DEPTHS and not
                # portfolio shares, and its OR sits inside one QLICI rather
                # than across an application. Withdrawn, and replaced with the
                # three things a CDE needs in order to act:
                #   (1) this sub-score is not Question 15's test;
                #   (2) what Question 15 actually asks;
                #   (3) whose threshold the number above is.
                # Stating only (1) would leave a reader assuming the sub-score
                # is a near-miss proxy for Q15 — the 1.2.0 disclosure defect.
                finding=(
                    f"Product Flexibility score is {pf}/10 — this tool's own "
                    "sub-score, not a measure of the CDFI Fund's Question 15 "
                    "test. Question 15 (CY 2024-2025 NMTC Allocation "
                    "Application, pp. 20-21) asks the Applicant to check ONE "
                    "option committing that 100% of its QLICIs will be "
                    "provided as equity; equity-equivalent financing; debt at "
                    "least 50% below market; or debt satisfying at least 5 "
                    "indicia of flexible or non-traditional terms — with "
                    "lower-scoring rungs at 33%/4 indicia, 25%/3 and 15%/2. "
                    "Every rung is a property of each individual QLICI. This "
                    "sub-score instead divides a QEI-weighted share of the "
                    "portfolio priced below market by a per-loan discount "
                    "depth, and takes the better of that and an "
                    "application-level indicia count. Those are different "
                    "quantities, so no figure here answers Question 15."
                ),
                action=(
                    f"Document {HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA} or more product "
                    "flexibility indicia: longer maturities, "
                    "lower origination fees, equity-like features, reduced collateral "
                    "requirements, below-market interest rates, extended interest-only periods, "
                    "or technical assistance grants. Quantify the below-market rate discount "
                    "as a percentage of market-rate comparables. Then answer Question 15 "
                    "directly from the CDE's own loan terms — this tool cannot answer it."
                ),
                expected_impact=(
                    "Raise this tool's Product Flexibility sub-score toward its 10-point "
                    "maximum. The sub-score's weight is this tool's interpretation; the "
                    "CDFI Fund does not publish point values for individual sub-criteria."
                ),
                quantified_improvement=f"Estimated +{10-pf} points (Product Flexibility: {pf}/10 → 10/10).",
                # Section II.A.1 describes what a HIGHLY RANKED application did.
                # The requirement itself is Question 15 in the Application, and
                # the citation now names both rather than implying the Review
                # Process states a threshold this sub-score measures.
                citation=(
                    f"{_SOURCE_DOC}, Section II.A.1; CY 2024-2025 NMTC Allocation "
                    "Application, Question 15 (pp. 20-21). Sub-score is this tool's own."
                ),
            ))
        elif pf < 10:
            recs.append(Recommendation(
                category="business_strategy",
                priority="medium",
                finding=(
                    f"Product Flexibility is {pf}/10 on this tool's own sub-score — one or "
                    f"two indicia short of its {HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA}-indicia "
                    "full-credit point. That point is this tool's threshold, not the CDFI "
                    "Fund's: Question 15 asks for a single committed option covering 100% "
                    "of QLICIs, which this tool does not compute."
                ),
                action=(
                    "Add 1–2 additional flexible product features or document them more explicitly "
                    "in the narrative. Technical assistance grants or equity co-investment features "
                    "are highly credible differentiators."
                ),
                expected_impact="Reach this tool's maximum Product Flexibility sub-score.",
                quantified_improvement=f"Estimated +{10-pf} points (Product Flexibility: {pf}/10 → 10/10).",
                citation=(
                    f"{_SOURCE_DOC}, Section II.A.1; CY 2024-2025 NMTC Allocation "
                    "Application, Question 15 (pp. 20-21). Sub-score is this tool's own."
                ),
            ))

        # Pipeline Credibility (15 pts)
        #
        # THE SECOND ``lic_board_representation_pct``, FOUND WHILE FIXING THE
        # FIRST. ``pipeline_pct_identified`` is absent-defaulted to 0.65
        # (win_probability.py:442) -- not zero, and not measured: an invented
        # moderate position. On an empty profile that default produced 10/15
        # and this engine rendered "A few projects lack documented sizing or
        # LOIs" as a FINDING about the CDE's pipeline, when nothing about the
        # CDE's pipeline had been read.
        pc = bs.get("pipeline_credibility", 0)
        if self._unsupplied(win_score, "pipeline_credibility"):
            recs.append(self._not_supplied_rec(win_score, "pipeline_credibility"))
        elif pc < 10:
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
        if self._unsupplied(win_score, "track_record_strength"):
            recs.append(self._not_supplied_rec(win_score, "track_record_strength"))
        elif trs < 9:
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
        if self._unsupplied(win_score, "track_record_alignment"):
            recs.append(self._not_supplied_rec(win_score, "track_record_alignment"))
        elif tra < 8:
            recs.append(Recommendation(
                category="business_strategy",
                priority="high",
                # D2 (1.2.2 round 2). This read: "The CDFI Fund requires 70%+
                # of NMTC pipeline to be supported by similar prior activity
                # AND 90%+ of prior allocation deployed on schedule." Two Fund
                # concepts had been fused into one invented bar under "The CDFI
                # Fund requires":
                #   * the 70% IS the Fund's, verbatim, and is UNTOUCHED here;
                #   * the 90% is the Fund's track-record-TO-PROJECTION ratio,
                #     re-pointed at prior-allocation deployment, which the Fund
                #     reviews in Phase 2 with NO percentage attached.
                # "deployment rate" returns 0 hits across all three primary
                # documents. The two halves are now stated separately, each
                # with its own provenance, because sweeping the true half out
                # with the false one would be its own defect.
                finding=(
                    f"Track Record Alignment is {tra}/{TRACK_RECORD_ALIGNMENT_MAX}. The CDFI Fund "
                    f"(Review Process p.7, Part II.A.4) looks for {_ALIGNMENT_PCT_TEXT}+ of "
                    "proposed NMTC investments to be supported by a track record of similar "
                    "business types and activity types, and for the most recent 5-year direct "
                    f"financing track record to be {_FUND_TRACK_TO_PROJECTION_TEXT}+ of "
                    "projected NMTC deployment in Exhibit A. Separately, this tool scores "
                    f"prior-allocation deployment against its own {_DEPLOYMENT_PCT_TEXT} "
                    "point — the CDFI Fund reviews deployment of a prior allocation in "
                    "Phase 2 (p.4) and publishes no percentage for it."
                ),
                action=(
                    f"Map at least {_ALIGNMENT_PCT_TEXT} of the NMTC pipeline projects to comparable prior direct "
                    "financing transactions (same sector, geography, or borrower profile). "
                    f"If prior-allocation deployment is below this tool's {_DEPLOYMENT_PCT_TEXT} "
                    "point, document catch-up plan and explain any delay."
                ),
                expected_impact=(
                    "Raise this tool's Track Record Alignment sub-score; strengthen the "
                    "Exhibit A track-record-to-projection comparison the CDFI Fund does make."
                ),
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
        #
        # THE SUB-SCORE IS A QEI-BASED PROXY AND THE FINDING NOW SAYS SO.
        # ``pct_deep_or_severe`` is a share of QEI (distress_analysis.py:128);
        # the Fund's higher-distress commitment is a share of QLICIs, and it
        # covers severe distress OR MULTIPLE INDICIA, which this package does
        # not measure. This finding used to read "Only X% of QEI is in severe
        # distress or multi-indicia distress tracts — below the 85% CDFI Fund
        # threshold", which compared a QEI share to a QLICI bar and claimed a
        # multi-indicia numerator that is not computed. The percentage-point
        # gap is now stated as what it is — the distance to THIS TOOL'S full
        # credit on its own proxy — rather than as a gap to the commitment,
        # which cannot be computed from anything in this package.
        severe_pct = d.get("pct_deep_or_severe", 0.0)
        if hdt is not None and hdt < 12:
            gap_pp = round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="critical",
                finding=(
                    f"Higher Distress Targeting is {hdt}/{HIGHER_DISTRESS_MAX}. "
                    f"{severe_pct:.0%} of QEI is in severely distressed tracts, "
                    "deep distress included. The CDFI Fund's higher-distress "
                    "commitment is measured on QLICIs rather than QEI and covers "
                    "severe distress OR multiple indicia of distress; this tool "
                    "computes neither the QLICI-denominated share nor any "
                    "multi-indicia measure, so the distance to the commitment "
                    "cannot be stated here and this sub-score is a QEI-based "
                    "proxy for it."
                ),
                action=(
                    f"Replace at least {gap_pp} percentage points of standard-LIC pipeline with "
                    "projects in census tracts the CDFI Fund flags as severely distressed — "
                    f"that is what closes the gap to full credit on this tool's {_SEVERE_PCT_TEXT}-of-QEI "
                    "proxy, not what the Fund will score. Use the CDFI Fund's NMTC Mapping Tool to "
                    "identify qualifying tracts in your target markets, and compute your own "
                    "QLICI-denominated share before committing to a figure."
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
                    f"but below this tool's {_SEVERE_PCT_TEXT}-of-QEI full-credit point. "
                    "The CDFI Fund's commitment is measured on QLICIs, not QEI."
                ),
                action=(
                    f"Add {round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)}pp of deeper-distress projects to "
                    f"reach full credit on this tool's {_SEVERE_PCT_TEXT}-of-QEI proxy. Target tracts at ≤60% AMI "
                    "or ≥30% poverty rate to maximize the distress classification, and compute your own "
                    "QLICI-denominated share before committing to a figure."
                ),
                expected_impact="Reach full Higher Distress Targeting credit.",
                quantified_improvement=f"Estimated +{HIGHER_DISTRESS_MAX - hdt} points (Higher Distress: {hdt}/{HIGHER_DISTRESS_MAX} → {HIGHER_DISTRESS_MAX}/{HIGHER_DISTRESS_MAX}).",
                citation=f"{_SOURCE_DOC}, Section II.C.1 — Community Outcomes, Higher Distress Targeting",
            ))

        # Deep Distress Commitment (10 pts) — tract-derived, skip when unassessable
        if ddc is not None and ddc < 7 and "pct_deep" in d:
            # NO SUBSTITUTE FOR pct_deep (1.2.1 B-1 sweep). The fallback here
            # was "50% of pct_deep_or_severe" — an invented split, printed to
            # the CDE as "Only X% of QEI is in CDFI Fund-designated Deep
            # Distress tracts". Deep is a strict subset of severe in no fixed
            # proportion, so no such split exists to compute. If the share is
            # not in the breakdown, the finding cannot be stated at all and
            # this recommendation is skipped.
            deep_pct = d["pct_deep"]
            gap_pp = round((DEEP_DISTRESS_MIN_PCT - deep_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="high",
                finding=(
                    f"Deep Distress Commitment is {ddc}/{DEEP_DISTRESS_MAX}. "
                    f"{deep_pct:.0%} of QEI is in CDFI Fund-designated Deep Distress tracts, "
                    f"{gap_pp}pp below this tool's {_DEEP_PCT_TEXT}-of-QEI full-credit point. "
                    "The CDFI Fund's Deep Distress commitment is measured on QLICIs rather "
                    "than QEI and this tool does not compute the QLICI-denominated share, so "
                    "the gap above is to the proxy, not to the commitment."
                ),
                # "These are distinct from severe distress" was FALSE, and it
                # was live text telling a CDE which tracts to go and find. Deep
                # Distress is a strict SUBSET of severe distress in the Fund's
                # own workbook — a deep tract is always also a severe one, and
                # across all 85,395 tracts there is not one exception. A CDE
                # reading "distinct" would look for tracts that do not exist as
                # a separate category, and would not know that every deep tract
                # it adds also counts toward the 85% higher-distress bar.
                action=(
                    "Identify and add pipeline projects in CDFI Fund Deep Distress areas. "
                    "Deep Distress is the tighter tier INSIDE severe distress, not a "
                    "separate category — every Deep Distress tract also counts toward the "
                    "higher-distress commitment. Check the NMTC Mapping Tool for tracts "
                    "flagged 'Deep distress' in the CY 2024-2025 eligibility data."
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
        #
        # NO ``_unsupplied`` GUARD HERE, AND THAT IS DELIBERATE (1.5.4 audit
        # close, B4). Every other sub-score below carries one; these two do
        # not, because both of this sub-score's inputs -- ``pct_persistent_
        # poverty`` and ``pct_us_territories`` -- have a measured substitute,
        # so ``unsupplied_inputs`` can never name it and the guard could never
        # be true. It was measured unreachable across all 2^17 presence
        # combinations before it was removed.
        st = co.get("special_targeting", 0)
        if hdt is not None and ddc is not None and st < 3:
            recs.append(Recommendation(
                category="community_outcomes",
                priority="medium",
                # D5 — WITHDRAWN, NOT RE-CITED (1.2.2 round 2).
                #
                # This read: "The CDFI Fund awards up to 5 bonus points for QEI
                # in U.S. Territories, High Migration Rural Counties, NMTC
                # Native Areas, or Persistent Poverty Counties." Round 1 could
                # not disprove it, having retrieved only the Review Process.
                # Round 2 retrieved the other two documents and it is now
                # disproved rather than unlocated: "special targeting" and
                # "bonus point" each return ZERO hits across the CY 2024-2025
                # Allocation Application (142pp), the Review Process (7pp) and
                # the CY 2024-2025 NOAA (10pp).
                #
                # The NOAA settles it affirmatively. Section V.B(b): "as
                # provided by IRC Sec. 45D(f)(2), the CDFI Fund will ascribe
                # additional points to entities that meet ONE OR BOTH of the
                # statutory priorities ... Applicants that meet the
                # requirements of both priority categories can receive up to a
                # total of ten additional points." Two priorities, ten points,
                # and this package already scores both separately (DBC track
                # record, Unrelated Entities). A third five-point award would
                # make fifteen against a published maximum of ten.
                #
                # THE "10 PRIORITY POINTS" DOES NOT RESCUE THIS. The
                # Application does say "up to 10 additional 'priority points'
                # available under sub-sections B and E" (p.19) — a point count
                # belonging to those two criteria. Reusing it to license a
                # five-point Community Outcomes criterion would be the D1
                # failure exactly: a real Fund figure re-pointed at a different
                # kind of quantity.
                #
                # The four CATEGORIES are real, and the Application does name
                # them — inside the glossary definition of "Disadvantaged
                # Business or Disadvantaged Community" (p.132): a Disadvantaged
                # Business is one located in "a Persistent Poverty County; a
                # NMTC Native Area; or a U.S. Island Area". They are inputs to
                # the DBC priority, not a criterion of their own. So the advice
                # below still helps a CDE — it is the ATTRIBUTION that was
                # false, and the sentence now says whose criterion this is.
                finding=(
                    f"Special Targeting is {st}/5 — this tool's own criterion. The CDFI "
                    "Fund publishes no 'Special Targeting' criterion and no bonus points "
                    "for it: the CY 2024-2025 NOAA sets out exactly two statutory "
                    "priorities under IRC §45D(f)(2), worth ten additional points in "
                    "total, and this tool scores both of them elsewhere. U.S. Territories, "
                    "High Migration Rural Counties, NMTC Native Areas and Persistent "
                    "Poverty Counties are real NMTC concepts, but the Application uses "
                    "them to define a Disadvantaged Business, not to award a separate "
                    "score. Treat this sub-score as a house prompt to consider those "
                    "areas, not as a bar the Fund will measure."
                ),
                action=(
                    "Add 1–2 projects in these areas if they fit the CDE's strategy. "
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
                    "before relying on it. Where such a project also serves a "
                    "Disadvantaged Business or Community, it counts toward the "
                    "DBC statutory priority, which the CDFI Fund does score."
                ),
                expected_impact=(
                    "Raise this tool's Special Targeting sub-score. No CDFI Fund points "
                    "follow from it directly; the Fund-scored route for these areas is the "
                    "DBC statutory priority."
                ),
                quantified_improvement=f"Estimated +{5-st} points (Special Targeting: {st}/5 → 5/5).",
                # NO REVIEW PROCESS SECTION IS CITED, BECAUSE NONE STATES THIS.
                # The old citation named "Section II.C.1", a real section
                # (Targeting Areas of Higher Distress, Question 25) that does
                # not contain the claim — a wrong pointer reads as corroboration
                # to anyone who does not open the document. What is cited now is
                # the document that DISPROVES the attribution, plus the glossary
                # entry the four categories actually come from.
                citation=(
                    "HOUSE criterion — no CDFI Fund source. Disproved against: CY 2024-2025 "
                    "NOAA (89 FR 92283, 21 Nov 2024), section V.B(b), two statutory "
                    "priorities totalling 10 points; CY 2024-2025 NMTC Allocation "
                    "Application p.132, which uses these four categories to define a "
                    "Disadvantaged Business."
                ),
            ))

        # Community Outcomes Quality (10 pts)
        coq = co.get("community_outcomes_quality", 0)
        if self._unsupplied(win_score, "community_outcomes_quality"):
            recs.append(self._not_supplied_rec(win_score, "community_outcomes_quality"))
        elif coq < 8:
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
        if self._unsupplied(win_score, "community_accountability"):
            recs.append(self._not_supplied_rec(win_score, "community_accountability"))
        elif ca < 8:
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
        if self._unsupplied(win_score, "dbc_track_record"):
            recs.append(self._not_supplied_rec(win_score, "dbc_track_record"))
        elif dbc < 4:
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

        # NO ``_unsupplied`` GUARD, for the same measured reason as Special
        # Targeting above: ``unrelated_entities_pct`` has a measured
        # substitute, so this sub-score is never unscored.
        ue = pp.get("unrelated_entities", 0)
        if ue < 4:
            recs.append(Recommendation(
                category="priority_points",
                priority="medium",
                # D3 (1.2.2 round 2). This read: "Full credit requires
                # committing substantially all (90%+) QEIs to entities
                # unrelated to the CDE." The 90% was presented as the content of
                # "substantially all" under a "Full credit requires" stem, i.e.
                # as the Fund's own figure. It is not, and the Fund publishes no
                # percentage here at all.
                #
                # THE DENOMINATOR IS UNCHANGED. "Proceeds of its QEIs" is what
                # Question 23 and the NOAA both say, and it is the one share
                # this package has right. Nothing below re-bases anything.
                #
                # NOT RE-BASED TO 85% EITHER. Treas. Reg. §1.45D-1(c)(5)(i) does
                # define "substantially all" as at least 85 percent, but it
                # defines it for the DEPLOYMENT test — QEI cash into QLICIs, at
                # §1.45D-1(c)(1)(ii). Borrowing it here would swap one unstated
                # number for another while making the citation look stronger.
                #
                # WHAT THE FUND ACTUALLY ASKS IS A YES/NO. Application p.34,
                # Question 23, is a dropdown: "Does the Applicant intend to use
                # substantially all of the proceeds of its QEIs to make QLICIs
                # in one or more businesses in which persons Unrelated to the
                # Applicant hold the majority equity interest?  [ ] Yes [ ] No",
                # and sub-section E: "An Applicant that answers 'Yes' to
                # Question 23 will be awarded five additional points." So this
                # package scores a continuous share against a binary question —
                # a category error before it is a wrong number, which is why
                # this is labelled house rather than re-based.
                finding=(
                    f"Unrelated Entities Priority Points are {ue}/5, scored against this "
                    f"tool's own {_UNRELATED_PCT_TEXT}-of-QEI point. The CDFI Fund publishes "
                    "no percentage here: Question 23 is a Yes/No commitment to use "
                    "\"substantially all\" of the proceeds of the CDE's QEIs for QLICIs in "
                    "businesses in which unrelated persons hold the majority equity "
                    "interest, and answering Yes is awarded five additional points."
                ),
                action=(
                    "Review pipeline for any related-party transactions. "
                    "If any QEIs go to CDE affiliates, replace with unrelated QALICB projects. "
                    "The commitment the Fund records is the Question 23 answer itself, and a "
                    "CDE that answers Yes is bound to it in its Allocation Agreement — decide "
                    f"it on the CDE's own structure, not on this tool's {_UNRELATED_PCT_TEXT} point."
                ),
                expected_impact="Earn unrelated entity priority points with minimal pipeline changes.",
                quantified_improvement=f"Estimated +{5-ue} priority points (Unrelated: {ue}/5 → 5/5).",
                # "Section III — Priority Points" is not a section of the Review
                # Process; priority points are Part II.B there. Corrected, and
                # the Application question is named because that is where the
                # commitment is actually made.
                citation=(
                    f"{_SOURCE_DOC}, p.7 Part II.B.2; CY 2024-2025 NMTC Allocation "
                    "Application, Question 23 and sub-section E (p.34). Percentage above "
                    "is this tool's own."
                ),
            ))

        return recs

    # ------------------------------------------------------------------
    # Gating recommendations (most important if not Highly Qualified)
    # ------------------------------------------------------------------

    @staticmethod
    def _gating_unscored_clause(win_score: "WinProbabilityScore") -> str:
        """T2, ONE LEVEL UP. The gating items instructed on defaults too.

        A section total is a SUM of sub-scores, so a section total containing
        unscored sub-scores is not a measurement either -- and the action field
        below said "focus immediately on the lowest-scoring Business Strategy
        sub-criteria", naming three of them. On an empty profile the
        lowest-scoring sub-criteria are lowest BECAUSE nothing was supplied,
        which makes that sentence an instruction to restructure a CDE around
        blanks in its own profile.

        The gap arithmetic is left exactly as it is: it is a true statement
        about what this tool computed, and it is the thing the gate turns on.
        What is added is that part of the figure it is computed from was never
        supplied.
        """
        missing = getattr(win_score, "unsupplied_inputs", None) or {}
        if not missing:
            return ""
        labels = ", ".join(SUBSCORE_LABELS.get(k, k) for k in sorted(missing))
        return (
            f" NOTE: {len(missing)} sub-score(s) — {labels} — could not be "
            "scored because this CDE supplied none of the inputs they read, so "
            "this section total includes absent-value defaults. Supply those "
            "inputs and re-score before treating the gap above as a gap in the "
            "application rather than a gap in the profile."
        )

    def _gating_recs(self, win_score: "WinProbabilityScore") -> List[Recommendation]:
        recs = []
        unscored_clause = self._gating_unscored_clause(win_score)
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
                        "Applications that miss either section minimum do not "
                        "advance to Phase 2." + unscored_clause
                    ),
                    action=(
                        (
                            "Supply the missing Business Strategy inputs named "
                            "above and re-score. Which sub-criterion is "
                            "genuinely lowest cannot be read off a section "
                            "total built partly from absent-value defaults, so "
                            "this tool does not name one."
                            if unscored_clause else
                            "Focus immediately on the lowest-scoring Business "
                            "Strategy sub-criteria: Product Flexibility, "
                            "Pipeline Credibility, and Track Record."
                        )
                        + f" You need at least {HIGHLY_QUALIFIED_SECTION_MIN} "
                        "points in this section to be considered."
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
                        + unscored_clause
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
                        f"{HIGHLY_QUALIFIED_AGGREGATE_MIN} — the Highly "
                        "Qualified threshold." + unscored_clause
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

        # SAME BASIS MISMATCH AS THE SCORED PATH ABOVE (FIX-3), and this one
        # fires when no score is available at all — the surface with the least
        # context around it, which is the worst place to state a bar wrong.
        # It read "below the CDFI Fund's 85% threshold for full Higher Distress
        # Targeting credit" over a share of QEI, and its quantified_improvement
        # subtracted the QLICI bar from that QEI share to size the gap.
        if severe_pct < SEVERE_DISTRESS_MIN_PCT:
            gap_pp = round((SEVERE_DISTRESS_MIN_PCT - severe_pct) * 100)
            recs.append(Recommendation(
                category="community_outcomes",
                priority="critical",
                finding=(
                    f"Severe/deep distress concentration is {severe_pct:.0%} of QEI — "
                    f"below this tool's {_SEVERE_PCT_TEXT}-of-QEI full-credit point for "
                    "Higher Distress Targeting. The CDFI Fund's own commitment is "
                    "measured on QLICIs, not QEI, and covers severe distress OR "
                    "multiple indicia of distress; this tool computes neither, so "
                    "the distance to the commitment cannot be stated here."
                ),
                action=(
                    f"Replace {gap_pp}pp of standard-LIC pipeline with projects in "
                    "severely distressed census tracts, and compute your own "
                    "QLICI-denominated share before committing to a figure."
                ),
                expected_impact="Reach full Higher Distress Targeting credit (15/15 pts).",
                quantified_improvement=(
                    f"Estimated {severe_pct:.0%} → {_SEVERE_PCT_TEXT} of QEI requires "
                    f"adding {gap_pp}pp of severe-distress QEI. That is the gap to this "
                    "tool's proxy; the QLICI-denominated gap is not computed."
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
                # INTERPOLATED, NOT TYPED (1.5.4 T7). This read "Reaching 98%
                # eligibility ..." with a hand-typed 98 sitting beside an
                # ``action`` two lines above that interpolates
                # _ELIGIBLE_STRONG_TEXT from the same constant. Move
                # WINNER_PATTERN_THRESHOLDS["min_eligible_pct"]["strong"] and
                # the two sentences of ONE recommendation disagree with each
                # other. The 98 was CORRECT — which is the whole hazard: the
                # 1.5.1 audit's instance 25 was four percentiles that had
                # agreed by luck and the suite stayed green.
                #
                # The band is also relabelled here, not just derived. It is
                # this package's own winner-pattern band, disclosed as such in
                # the finding above and now in the estimate too, so the
                # estimate cannot be read alone as a Fund target.
                quantified_improvement=(
                    f"Reaching {_ELIGIBLE_STRONG_TEXT} eligibility "
                    "significantly improves Pipeline Credibility. That band is "
                    "this tool's own winner-pattern heuristic, not a CDFI Fund "
                    "threshold."
                ),
                citation=f"{_SOURCE_DOC}, Section II.A — Business Strategy, Pipeline",
            ))

        return recs

    # ------------------------------------------------------------------
    # Assessment qualifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _eligibility_gate_note(result: Optional["PipelineAnalysisResult"]) -> str:
        """One sentence, on the same measurement the gate item uses."""
        if result is None:
            return ""
        if getattr(result, "eligibility_data_status", "ok") != "ok":
            return ""
        breakdown = result.distress_breakdown or {}
        buckets = breakdown.get("dollars_by_distress") or {}
        counts = breakdown.get("project_count_by_distress") or {}
        ineligible_qei = buckets.get("ineligible", 0) or 0
        total_qei = result.total_qei_request or 0
        if ineligible_qei <= 0 or total_qei <= 0:
            return ""
        # THE COUNT IS HERE BECAUSE THIS IS THE SENTENCE A CDE READS FIRST
        # (1.5.4 audit close, B2 rule 2). The gate ITEM has carried "(1 of 20
        # projects)" since T4; this sentence carried a bare percentage, so on
        # the one surface most likely to be read alone the share had nothing to
        # qualify it. It is a DISCLOSURE of what was measured, not an
        # instruction, so it sits inside the principle T2 adopted.
        return (
            f" ELIGIBILITY FIRST: {_share_text(ineligible_qei, total_qei)} of "
            f"pipeline QEI ({counts.get('ineligible', 0)} of "
            f"{result.total_projects} projects) is in tracts that are not a "
            "Low-Income Community, which is a "
            "statutory gate under IRC §45D(d) and not one of the things the "
            "score above ranks. The tier is a ranking; it does not answer that."
        )

    @staticmethod
    def _unscored_note(win_score: Optional["WinProbabilityScore"]) -> str:
        """One sentence, naming how much of the aggregate was not measured."""
        missing = getattr(win_score, "unsupplied_inputs", None) or {}
        if not missing:
            return ""
        labels = ", ".join(
            SUBSCORE_LABELS.get(k, k) for k in sorted(missing)
        )
        return (
            f" NOT ALL OF THIS WAS SCORED: {len(missing)} sub-score(s) — "
            f"{labels} — read CDE-declared inputs this run did not receive, so "
            "the figures above include absent-value defaults. The aggregate is "
            "a sum of what was computed, not a measurement of what was "
            "supplied."
        )

    # ------------------------------------------------------------------
    # Overall assessment
    # ------------------------------------------------------------------

    def _overall_assessment(
        self,
        win_score: Optional["WinProbabilityScore"],
        pipeline_result: Optional["PipelineAnalysisResult"] = None,
    ) -> str:
        """The one-line verdict, with what qualifies it attached to it.

        TWO QUALIFIERS ARE APPENDED, AND BOTH ARE ABOUT THE VERDICT ITSELF
        rather than about the pipeline:

          * the statutory eligibility gate (1.5.4 T4). A tier is a RANKING, and
            a ranking stated over a pipeline that fails the LIC gate reads as
            though the gate were one of the things being ranked on.
          * the count of sub-scores this tool could not score (1.5.4 T2). The
            aggregate is a sum, so a sum containing five ``.get`` defaults is
            not a measurement of the application either -- and the tier is read
            off that aggregate. No number changes; what changes is that the
            number no longer arrives unqualified.
        """
        gate = self._eligibility_gate_note(pipeline_result)
        unscored = self._unscored_note(win_score)
        if win_score is None:
            return (
                "Analysis complete. Review recommendations below to improve "
                "alignment with the CDFI Fund's CY 2024-2025 Review Process "
                "criteria." + gate
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
                "conclusion about competitiveness." + gate + unscored
            )

        tier = win_score.tier
        agg = win_score.aggregate_base_score
        bs = win_score.business_strategy.get("section_total", 0)
        co = win_score.community_outcomes.get("section_total", 0)

        if tier == "Top Tier":
            return (
                f"Top Tier ({agg}/{_AGGREGATE_MAX}). Business Strategy: {bs}/{BUSINESS_STRATEGY_MAX}, "
                f"Community Outcomes: {co}/{COMMUNITY_OUTCOMES_MAX}. Both sections exceed the "
                f"{HOUSE_TOP_TIER_SECTION_MIN}-point threshold. "
                # "Top Tier" is this package's own label and the two cut points
                # behind it are unsourced. The CDFI Fund publishes the Highly
                # Qualified gate and nothing above it, so a CDE reading this
                # line must not take the ranking for a federal one.
                "(\"Top Tier\" is this tool's own label: the CDFI Fund publishes "
                "no tier above Highly Qualified, and the cut points behind it "
                "are an unsourced house heuristic, not a CDFI Fund threshold.) "
                "Focus on Phase 2 preparation (Management Capacity, "
                "Capitalization Strategy)." + gate + unscored
            )
        if tier == "Highly Qualified":
            return (
                f"Highly Qualified ({agg}/{_AGGREGATE_MAX}). Business Strategy: {bs}/{BUSINESS_STRATEGY_MAX}, "
                f"Community Outcomes: {co}/{COMMUNITY_OUTCOMES_MAX}. Both sections meet the "
                f"{HIGHLY_QUALIFIED_SECTION_MIN}-point gating minimum. "
                "Priority changes below can improve ranking within the Highly "
                "Qualified pool." + gate + unscored
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
            f"Not Qualified ({agg}/{_AGGREGATE_MAX}) — {gap_str}. "
            "Address Critical recommendations first to meet gating thresholds."
            + gate + unscored
        )
