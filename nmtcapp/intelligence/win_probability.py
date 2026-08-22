"""
NMTC Application scoring against the CDFI Fund's CY 2024-2025 Review Process.

The CDFI Fund evaluates applications on two scored sections (Business Strategy
and Community Outcomes, 50 pts each), plus optional Priority Points (10 pts).
Applicants must score 85+ aggregate AND 40+ in each section to reach the
"Highly Qualified" pool eligible for Phase 2 review and potential award.

Source: CY 2024-2025 NMTC Allocation Application Review Process
https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf

METHODOLOGY NOTE: Sub-score weights within each section (e.g., Product
Flexibility 10 pts, Pipeline Credibility 15 pts) are this tool's best-effort
interpretation of CDFI Fund guidance. The CDFI Fund does not publish exact
point values for individual sub-criteria. Treat sub-scores as directional,
not authoritative.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import (
    SEVERE_DISTRESS_MIN_PCT,
    DEEP_DISTRESS_MIN_PCT,
    HOUSE_SPECIAL_TARGETING_TRIGGER_PCT,
    TRACK_RECORD_PIPELINE_ALIGNMENT_MIN,
    HOUSE_TRACK_RECORD_DEPLOYMENT_MIN,
    HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT,
    HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA,
    DBC_PRIORITY_YEARS_MIN,
    DBC_VOLUME_PCT_MIN,
    HOUSE_UNRELATED_ENTITIES_MIN_PCT,
    HIGHLY_QUALIFIED_AGGREGATE_MIN,
    HIGHLY_QUALIFIED_SECTION_MIN,
    HOUSE_TOP_TIER_AGGREGATE_MIN,
    HOUSE_TOP_TIER_SECTION_MIN,
    BUSINESS_STRATEGY_MAX,
    COMMUNITY_OUTCOMES_MAX,
    PRIORITY_POINTS_MAX,
    PRODUCT_FLEXIBILITY_MAX,
    PIPELINE_CREDIBILITY_MAX,
    TRACK_RECORD_STRENGTH_MAX,
    TRACK_RECORD_ALIGNMENT_MAX,
    HIGHER_DISTRESS_MAX,
    DEEP_DISTRESS_MAX,
    HOUSE_SPECIAL_TARGETING_MAX,
    COMMUNITY_OUTCOMES_QUALITY_MAX,
    COMMUNITY_ACCOUNTABILITY_MAX,
    DBC_TRACK_RECORD_MAX,
    UNRELATED_ENTITIES_MAX,
)
from nmtcapp.data.historical_awards import get_overall_acceptance_rate
from nmtcapp.intelligence.cde_inputs import unsupplied_inputs

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

# The three section maxima are INTERPOLATED. This note is the sentence that
# tells a CDE what the denominators in the block above mean, and it carried
# them as literals — so moving BUSINESS_STRATEGY_MAX would have changed every
# printed denominator while the paragraph explaining them went on naming 50.
_METHODOLOGY = (
    "IMPORTANT: This score assesses alignment with the CDFI Fund's published CY 2024-2025 "
    f"Review Process criteria (Business Strategy {BUSINESS_STRATEGY_MAX} pts + Community "
    f"Outcomes {COMMUNITY_OUTCOMES_MAX} pts + Priority "
    f"Points {PRIORITY_POINTS_MAX} pts). It is a self-assessment tool, not a guarantee of selection. "
    "TIER NAMES: \"Highly Qualified\" is the CDFI Fund's own gate. \"Top Tier\" is "
    "this tool's own label for an application well clear of that gate — the CDFI "
    "Fund publishes no tier above Highly Qualified, and the 95/45 cut points "
    "behind the label are an unsourced house heuristic, not a federal figure. "
    "Sub-score "
    "weights within sections are this tool's interpretation — the CDFI Fund does not publish "
    "exact point values for individual sub-criteria. Phase 2 factors (Management Capacity, "
    "Capitalization Strategy) and past reporting compliance deductions are not modeled here. "
    "Source: CY_2024_25_NMTC_Program_Review_Process.pdf"
)


@dataclass
class WinProbabilityScore:
    """CDFI Fund alignment score for an NMTC application.

    Mirrors the CDFI Fund's CY 2024-2025 scoring structure:
    - Business Strategy (0–50)
    - Community Outcomes (0–50)
    - Priority Points (0–10, bonus)
    - Aggregate base score (0–100)
    - Tier: Not Qualified / Highly Qualified / Top Tier

    Backward-compatible fields (``composite_score``, ``dimensional_scores``,
    ``competitive_tier``) are populated from the new structure so callers that
    pre-date this refactor continue to work without changes.

    Example::

        model = WinProbabilityModel()
        score = model.score(pipeline_result, 55_000_000)
        print(score.summary())
    """
    # --- CDFI Fund scored sections ---
    business_strategy: dict            # sub-scores + section_total (0–50)
    community_outcomes: dict           # sub-scores + section_total (0–50)
    priority_points: dict              # sub-scores + section_total (0–10)

    # --- Aggregate and tier ---
    aggregate_base_score: int          # 0–100 (Business Strategy + Community Outcomes)
    aggregate_with_priority: int       # 0–110 (includes Priority Points, used for ranking)
    tier: str                          # "Not Qualified" | "Highly Qualified" | "Top Tier"
    tier_gating_notes: List[str]

    # --- Phase 2 / qualitative flags (not scored) ---
    phase2_flags: dict = field(default_factory=dict)

    # --- Backward-compatible fields ---
    composite_score: float = 0.0       # = aggregate_base_score (float for old API compat)
    dimensional_scores: dict = field(default_factory=dict)  # section totals mapped to 0–100
    acceptance_rate_baseline: float = 0.34
    # "strong" | "competitive" | "marginal" | "weak" | "not_rated"
    # "not_rated" is the degraded state: no tier was assigned because
    # eligibility data was unavailable. It is not a low rating.
    competitive_tier: str = ""
    peer_comparison: str = ""
    methodology_disclosure: str = field(default=_METHODOLOGY)
    # Partial-score marker: True when eligibility data was unavailable — the
    # distress-based Community Outcomes components are excluded (None), the
    # aggregate covers only the available points, and no tier is assigned.
    partial: bool = False
    partial_note: str = ""
    eligibility_data_error: str = ""
    # WHICH SUB-SCORES ARE BUILT OUT OF DEFAULTS (1.5.4 T2). Sub-score key ->
    # the CDE-declared inputs it reads that this run did not receive. Empty for
    # a CDE that supplied everything, which is the shipped sample.
    #
    # THIS FIELD MOVES NO SCORE. Every sub-score above is computed exactly as
    # it was in 1.5.3, from exactly the same defaults. What this records is
    # whether the number DESCRIBES anything, so that a renderer can tell an
    # absent input from a declared zero -- which, until 1.5.4, nothing
    # downstream of this model could do. ``lic_board_representation_pct``
    # absent and ``lic_board_representation_pct: 0.0`` produced the identical
    # 0/10, and the recommendation engine instructed on both.
    #
    # See nmtcapp/intelligence/cde_inputs for the registry and for why an input
    # with a measured pipeline substitute never appears here.
    unsupplied_inputs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Populate backward-compat fields from new structure
        if not self.composite_score:
            self.composite_score = float(self.aggregate_base_score)
        if not self.dimensional_scores:
            # Divide by the FIXED structural maxima, never by max_available:
            # in degraded mode Community Outcomes' max_available shrinks to the
            # section total less the two unscorable components, and dividing by
            # it would inflate 20 earned points into 80.0 — the honest
            # structural value is 40.0. The maxima are READ, not typed: three
            # more copies of 50/50/10 here would drift from the constants the
            # same way the max_available literals did (R-5).
            self.dimensional_scores = {
                "business_strategy": round(
                    self.business_strategy.get("section_total", 0)
                    / BUSINESS_STRATEGY_MAX * 100, 1
                ),
                "community_outcomes": round(
                    self.community_outcomes.get("section_total", 0)
                    / COMMUNITY_OUTCOMES_MAX * 100, 1
                ),
                "priority_points": round(
                    self.priority_points.get("section_total", 0)
                    / PRIORITY_POINTS_MAX * 100, 1
                ),
            }
        if not self.competitive_tier:
            self.competitive_tier = _map_tier_legacy(self.tier)
        if not self.peer_comparison:
            self.peer_comparison = _build_peer_comparison(self)

    def summary(self) -> str:
        """Return a formatted alignment score report."""
        bs = self.business_strategy
        co = self.community_outcomes
        pp = self.priority_points

        def _pts(section: dict, key: str) -> str:
            val = section.get(key, 0)
            return "n/a" if val is None else f"{val:2d} "

        # The .get() defaults are the constants, not literals. A default that
        # is a typed number is a silent second copy of the constant which fires
        # exactly when the score dict is malformed — the moment a wrong
        # denominator is least likely to be noticed.
        agg_denom = (
            bs.get("max_available", BUSINESS_STRATEGY_MAX)
            + co.get("max_available", COMMUNITY_OUTCOMES_MAX)
        )
        lines = []
        if self.partial:
            lines.extend([
                "!" * 70,
                "  ELIGIBILITY DATA UNAVAILABLE",
                f"  {self.eligibility_data_error or 'reason unknown'}",
                f"  {self.partial_note}",
                "!" * 70,
            ])
        lines += [
            "=" * 70,
            "  NMTC APPLICATION SCORE  (CDFI Fund CY 2024-2025 Framework)",
            f"  Aggregate Base Score:    {self.aggregate_base_score} / {agg_denom}"
            + ("  (PARTIAL)" if self.partial else ""),
            f"  With Priority Points:    {self.aggregate_with_priority} / {agg_denom + pp.get('max_available', PRIORITY_POINTS_MAX)}"
            + ("  (PARTIAL)" if self.partial else ""),
            f"  Tier:                    {self.tier.upper()}",
            "=" * 70,
            "",
            f"  BUSINESS STRATEGY:  {bs['section_total']:2d} / {bs.get('max_available', BUSINESS_STRATEGY_MAX)}",
            f"    Product Flexibility       {_pts(bs, 'product_flexibility')}/{PRODUCT_FLEXIBILITY_MAX:3d}",
            f"    Pipeline Credibility      {_pts(bs, 'pipeline_credibility')}/{PIPELINE_CREDIBILITY_MAX:3d}",
            f"    Track Record Strength     {_pts(bs, 'track_record_strength')}/{TRACK_RECORD_STRENGTH_MAX:3d}",
            f"    Track Record Alignment    {_pts(bs, 'track_record_alignment')}/{TRACK_RECORD_ALIGNMENT_MAX:3d}",
            "",
            f"  COMMUNITY OUTCOMES: {co['section_total']:2d} / {co.get('max_available', COMMUNITY_OUTCOMES_MAX)}",
            f"    Higher Distress Targeting {_pts(co, 'higher_distress_targeting')}/{HIGHER_DISTRESS_MAX:3d}",
            f"    Deep Distress Commitment  {_pts(co, 'deep_distress_commitment')}/{DEEP_DISTRESS_MAX:3d}",
            f"    Special Targeting         {_pts(co, 'special_targeting')}/{HOUSE_SPECIAL_TARGETING_MAX:3d}",
            f"    Community Outcomes Quality{_pts(co, 'community_outcomes_quality')}/{COMMUNITY_OUTCOMES_QUALITY_MAX:3d}",
            f"    Community Accountability  {_pts(co, 'community_accountability')}/{COMMUNITY_ACCOUNTABILITY_MAX:3d}",
            "",
            f"  PRIORITY POINTS:    {pp['section_total']:2d} / {pp.get('max_available', PRIORITY_POINTS_MAX)}",
            f"    DBC Track Record          {_pts(pp, 'dbc_track_record')}/{DBC_TRACK_RECORD_MAX:3d}",
            f"    Unrelated Entities        {_pts(pp, 'unrelated_entities')}/{UNRELATED_ENTITIES_MAX:3d}",
            "",
        ]
        if self.tier_gating_notes:
            lines.append("  GATING NOTES:")
            for note in self.tier_gating_notes:
                lines.append(f"    • {note}")
            lines.append("")
        lines.extend([
            f"  Assessment: {self.peer_comparison}",
            "",
            "  *** METHODOLOGY NOTE ***",
            f"  {self.methodology_disclosure}",
            "=" * 70,
        ])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "business_strategy": self.business_strategy,
            "community_outcomes": self.community_outcomes,
            "priority_points": self.priority_points,
            "aggregate_base_score": self.aggregate_base_score,
            "aggregate_with_priority": self.aggregate_with_priority,
            "tier": self.tier,
            "tier_gating_notes": self.tier_gating_notes,
            "phase2_flags": self.phase2_flags,
            "composite_score": self.composite_score,
            "dimensional_scores": self.dimensional_scores,
            "acceptance_rate_baseline": self.acceptance_rate_baseline,
            "competitive_tier": self.competitive_tier,
            "peer_comparison": self.peer_comparison,
            "methodology_disclosure": self.methodology_disclosure,
            "partial": self.partial,
            "partial_note": self.partial_note,
            "eligibility_data_error": self.eligibility_data_error,
        }


class WinProbabilityModel:
    """Score an NMTC application against the CDFI Fund's CY 2024-2025 framework.

    Accepts optional ``cde_attributes`` dict for CDE-level scoring inputs
    (track record, product terms, board composition, etc.) that are not
    derivable from pipeline data alone. When ``None``, conservative defaults
    are applied — scores will be lower than for a CDE with strong attributes.

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
        cde_attributes: Optional[dict] = None,
    ) -> WinProbabilityScore:
        """Compute a CDFI Fund framework score.

        Args:
            pipeline_result: Result from PipelineAnalyzer.
            requested_allocation: CDE's requested allocation in dollars.
            application_round: Target application round label (informational).
            cde_attributes: Optional dict of CDE-level scoring inputs. Keys:
                ``products_below_market_pct`` (float 0–1),
                ``products_flexible_indicia_count`` (int),
                ``pipeline_pct_identified`` (float 0–1),
                ``has_own_capital_at_risk`` (bool),
                ``prior_award_count`` (int),
                ``years_in_operation`` (int),
                ``track_record_pipeline_alignment_pct`` (float 0–1),
                ``track_record_deployment_pct`` (float 0–1),
                ``pct_persistent_poverty`` (float 0–1),
                ``pct_us_territories`` (float 0–1),
                ``has_third_party_validation`` (bool),
                ``has_quantified_outcomes`` (bool),
                ``lic_board_representation_pct`` (float 0–1),
                ``has_community_engagement_track_record`` (bool),
                ``dbc_focus_years`` (int),
                ``dbc_dollar_volume_pct`` (float 0–1),
                ``unrelated_entities_pct`` (float 0–1).

        Returns:
            :class:`WinProbabilityScore` with full CDFI Fund structure.
        """
        attrs = cde_attributes or {}
        degraded = getattr(pipeline_result, "eligibility_data_status", "ok") != "ok"
        # Recorded BEFORE anything is scored, from the dict this model actually
        # received. Deriving it afterwards from the sub-scores would be the
        # guess this field exists to remove: a 0 tells you nothing about
        # whether an input arrived.
        missing_inputs = unsupplied_inputs(attrs)

        # --- Section 1: Business Strategy (0–50) ---
        pf = self._score_product_flexibility(attrs, pipeline_result)
        pc = self._score_pipeline_credibility(
            pipeline_result, attrs, skip_eligibility_penalty=degraded
        )
        trs = self._score_track_record_strength(attrs)
        tra = self._score_track_record_alignment(attrs)
        bs_total = pf + pc + trs + tra

        business_strategy = {
            "product_flexibility": pf,
            "pipeline_credibility": pc,
            "track_record_strength": trs,
            "track_record_alignment": tra,
            "section_total": bs_total,
            # R-5: READ, NOT TYPED. This dict's max_available is what
            # WinProbabilityScore.summary() prints as the "/ 50" denominator
            # and what the aggregate denominator is summed from, so a literal
            # here is a second, independent copy of BUSINESS_STRATEGY_MAX. The
            # 1.2.1 waiver for that constant was factually true BECAUSE of this
            # duplication — "the printed denominator comes from the score
            # dict's max_available, not from this constant" — which recorded a
            # duplication in the same release that removed five others. Reading
            # the constant turns the waiver into a pin.
            "max_available": BUSINESS_STRATEGY_MAX,
        }

        # --- Section 2: Community Outcomes (0–50) ---
        # The tract-distress components require verified eligibility data.
        # When it is unavailable they are None (excluded), never estimated.
        if degraded:
            hdt = None
            ddc = None
        else:
            hdt = self._score_higher_distress(pipeline_result)
            ddc = self._score_deep_distress(pipeline_result)
        st  = self._score_special_targeting(pipeline_result, attrs)
        coq = self._score_outcomes_quality(attrs)
        ca  = self._score_community_accountability(attrs)
        co_total = (hdt or 0) + (ddc or 0) + st + coq + ca

        community_outcomes = {
            "higher_distress_targeting": hdt,
            "deep_distress_commitment": ddc,
            "special_targeting": st,
            "community_outcomes_quality": coq,
            "community_accountability": ca,
            "section_total": co_total,
            # The degraded denominator is the section maximum LESS the two
            # tract-derived components that could not be scored, so it stays
            # correct when any of the three constants moves. Typed, it was 25 —
            # a number with no visible relationship to the 15 and 10 it is the
            # complement of.
            "max_available": (
                COMMUNITY_OUTCOMES_MAX - (HIGHER_DISTRESS_MAX + DEEP_DISTRESS_MAX)
                if degraded else COMMUNITY_OUTCOMES_MAX
            ),
        }

        # --- Priority Points (0–10) ---
        dbc = self._score_dbc_track_record(attrs)
        ue  = self._score_unrelated_entities(attrs, pipeline_result)
        pp_total = dbc + ue

        priority_points = {
            "dbc_track_record": dbc,
            "unrelated_entities": ue,
            "section_total": pp_total,
            "max_available": PRIORITY_POINTS_MAX,
        }

        aggregate_base = bs_total + co_total
        aggregate_with_priority = aggregate_base + pp_total

        partial_note = ""
        if degraded:
            # No tier: with 25 of 100 base points unavailable, classification
            # against the 85/40 CDFI Fund thresholds would be meaningless.
            tier = "Not Rated — eligibility data unavailable"
            gating_notes = [
                "Score computed without eligibility verification: Higher "
                "Distress Targeting (15 pts) and Deep Distress Commitment "
                "(10 pts) could not be assessed. No tier is assigned.",
            ]
            partial_note = (
                "score computed without eligibility verification "
                "(8 of 10 scored components; 25 of 100 base points unavailable)"
            )
        else:
            tier, gating_notes = self._classify_tier(bs_total, co_total, aggregate_base)
        phase2_flags = self._build_phase2_flags(attrs, pipeline_result)

        baseline = get_overall_acceptance_rate(rounds=4)

        return WinProbabilityScore(
            business_strategy=business_strategy,
            community_outcomes=community_outcomes,
            priority_points=priority_points,
            aggregate_base_score=aggregate_base,
            aggregate_with_priority=aggregate_with_priority,
            tier=tier,
            tier_gating_notes=gating_notes,
            phase2_flags=phase2_flags,
            composite_score=float(aggregate_base),
            acceptance_rate_baseline=baseline,
            partial=degraded,
            partial_note=partial_note,
            eligibility_data_error=(
                getattr(pipeline_result, "eligibility_data_error", None) or ""
            ) if degraded else "",
            unsupplied_inputs=missing_inputs,
        )

    # ------------------------------------------------------------------
    # Business Strategy sub-scorers
    # ------------------------------------------------------------------

    def _score_product_flexibility(
        self, attrs: dict, result: "PipelineAnalysisResult | None" = None
    ) -> int:
        # Prefer explicit CDE-level attr; fall back to pipeline-derived pct_below_market_rate
        below_mkt = attrs.get("products_below_market_pct")
        if below_mkt is None and result is not None:
            below_mkt = result.distress_breakdown.get("pct_below_market_rate", 0.0)
        below_mkt = below_mkt or 0.0
        indicia = attrs.get("products_flexible_indicia_count", 0)
        # Full credit if either threshold is met
        score_from_below_mkt = min(10.0, below_mkt / HOUSE_PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT * 10)
        score_from_indicia = min(10.0, indicia / HOUSE_PRODUCT_FLEXIBILITY_MIN_INDICIA * 10)
        return _to_int(max(score_from_below_mkt, score_from_indicia))

    def _score_pipeline_credibility(
        self, result: "PipelineAnalysisResult", attrs: dict,
        skip_eligibility_penalty: bool = False,
    ) -> int:
        identified_pct = attrs.get("pipeline_pct_identified", 0.65)
        # Piecewise: 100% → 15, 80% → 12, 60% → 9, <50% → proportional
        if identified_pct >= 1.0:
            raw = 15.0
        elif identified_pct >= 0.80:
            raw = 9.0 + (identified_pct - 0.60) / 0.40 * 6.0
        elif identified_pct >= 0.60:
            raw = 6.0 + (identified_pct - 0.40) / 0.20 * 3.0
        else:
            raw = identified_pct / 0.60 * 6.0
        # Eligibility penalty: subtract up to 2 pts if eligibility rate is low.
        # Skipped when eligibility data is unavailable — an unverified rate of
        # 0% would otherwise zero the sub-score (a fabricated negative).
        if skip_eligibility_penalty:
            elig_penalty = 0.0
        else:
            elig_penalty = max(0.0, (0.95 - result.eligibility_pct) * 20)
        return _to_int(max(0.0, min(15.0, raw - elig_penalty)))

    def _score_track_record_strength(self, attrs: dict) -> int:
        # Base: number of prior awards (each worth 3 pts, max 3 awards = 9 pts)
        prior_awards = attrs.get("prior_award_count", 0)
        award_pts = min(9, prior_awards * 3)
        # Years in operation component (up to 3 pts for 5+ years)
        years = attrs.get("years_in_operation", 0)
        year_pts = min(3, years / 5 * 3)
        # Own capital at risk bonus: 3 pts
        capital_bonus = 3 if attrs.get("has_own_capital_at_risk", False) else 0
        return _to_int(min(15.0, award_pts + year_pts + capital_bonus))

    def _score_track_record_alignment(self, attrs: dict) -> int:
        # 5 pts for pipeline alignment ≥ 70%; 5 pts for deployment rate ≥ 90%
        align_pct = attrs.get("track_record_pipeline_alignment_pct", 0.0)
        deploy_pct = attrs.get("track_record_deployment_pct", 0.0)
        align_score = min(5.0, align_pct / TRACK_RECORD_PIPELINE_ALIGNMENT_MIN * 5.0)
        deploy_score = min(5.0, deploy_pct / HOUSE_TRACK_RECORD_DEPLOYMENT_MIN * 5.0)
        return _to_int(align_score + deploy_score)

    # ------------------------------------------------------------------
    # Community Outcomes sub-scorers
    # ------------------------------------------------------------------

    # BOTH SUB-SCORES DIVIDE A QEI SHARE BY A QLICI BAR, AND THAT IS KNOWN.
    # SEVERE_DISTRESS_MIN_PCT and DEEP_DISTRESS_MIN_PCT are shares of QLICIs
    # (CY 2024-2025 Review Process, Question 25); pct_deep_or_severe and
    # pct_deep are shares of QEI (distress_analysis.py:128). The scale factor
    # is therefore a proxy, not the Fund's own arithmetic, and the 85% carries
    # a second mismatch — it covers severe distress OR MULTIPLE INDICIA, which
    # this package does not measure at all.
    #
    # LEFT AS IT IS, DELIBERATELY. Swapping the denominator to QLICIs moves
    # every Community Outcomes sub-score and every figure downstream of them,
    # and belongs behind a written methodology that is hostile-audited first —
    # 1.2.2. What FIX-3 removed is the CLAIM that these numbers answer the
    # Fund's bars, not the numbers. Nothing rendered may say they do.
    def _score_higher_distress(self, result: "PipelineAnalysisResult") -> int:
        pct = result.distress_breakdown.get("pct_deep_or_severe", 0.0)
        return _to_int(min(15.0, pct / SEVERE_DISTRESS_MIN_PCT * 15.0))

    def _score_deep_distress(self, result: "PipelineAnalysisResult") -> int:
        # NO SUBSTITUTE FOR pct_deep (1.2.1 B-1 sweep). This used to fall back
        # to "50% of pct_deep_or_severe", a made-up split of a combined share
        # that the Fund's nesting does not support — deep is a strict subset of
        # severe, in no fixed proportion. analyze_distress_concentration always
        # emits pct_deep, so the fallback only ever fired on a hand-built dict,
        # and when it fired it invented the number this sub-score is entirely
        # made of. Absent means unknown, and unknown scores zero.
        d = result.distress_breakdown
        deep_pct = d.get("pct_deep", 0.0)
        return _to_int(min(10.0, deep_pct / DEEP_DISTRESS_MIN_PCT * 10.0))

    def _score_special_targeting(
        self, result: "PipelineAnalysisResult", attrs: dict
    ) -> int:
        d = result.distress_breakdown
        # Prefer explicit CDE-level attrs; fall back to pipeline-derived pcts
        pct_persistent = attrs.get("pct_persistent_poverty", d.get("pct_persistent_poverty", 0.0))
        pct_territories = attrs.get("pct_us_territories", d.get("pct_us_territories", 0.0))
        # Check four qualifying categories; each 10%+ in a category = 1.25 pts (max 5)
        categories = [
            d.get("pct_native_area", 0.0),
            d.get("pct_high_migration_rural", 0.0),
            pct_persistent,
            pct_territories,
        ]
        qualified = sum(1 for c in categories if c >= HOUSE_SPECIAL_TARGETING_TRIGGER_PCT)
        # Partial credit: weight by concentration in each category (up to 1.25 each)
        partial = sum(
            min(1.25, c / HOUSE_SPECIAL_TARGETING_TRIGGER_PCT * 1.25) for c in categories
        )
        return _to_int(min(5.0, partial))

    def _score_outcomes_quality(self, attrs: dict) -> int:
        has_quantified = attrs.get("has_quantified_outcomes", True)
        has_third_party = attrs.get("has_third_party_validation", False)
        if not has_quantified:
            return 2
        if has_third_party:
            return 9
        return 6

    def _score_community_accountability(self, attrs: dict) -> int:
        lic_pct = attrs.get("lic_board_representation_pct", 0.0)
        has_engagement = attrs.get("has_community_engagement_track_record", False)
        # Board representation: up to 8 pts (reference: 33% ≈ competitive)
        board_pts = min(8.0, lic_pct / 0.33 * 8.0)
        engagement_bonus = 2 if has_engagement else 0
        return _to_int(min(10.0, board_pts + engagement_bonus))

    # ------------------------------------------------------------------
    # Priority Points sub-scorers
    # ------------------------------------------------------------------

    def _score_dbc_track_record(self, attrs: dict) -> int:
        years = attrs.get("dbc_focus_years", 0)
        vol_pct = attrs.get("dbc_dollar_volume_pct", 0.0)
        year_score = min(2.5, years / DBC_PRIORITY_YEARS_MIN * 2.5)
        vol_score = min(2.5, vol_pct / DBC_VOLUME_PCT_MIN * 2.5)
        return _to_int(year_score + vol_score)

    def _score_unrelated_entities(
        self, attrs: dict, result: "PipelineAnalysisResult | None" = None
    ) -> int:
        # Prefer explicit CDE-level attr; fall back to pipeline-derived pct_unrelated_entity
        pct = attrs.get("unrelated_entities_pct")
        if pct is None and result is not None:
            pct = result.distress_breakdown.get("pct_unrelated_entity", 0.0)
        pct = pct or 0.0
        return _to_int(min(5.0, pct / HOUSE_UNRELATED_ENTITIES_MIN_PCT * 5.0))

    # ------------------------------------------------------------------
    # Gating / classification
    # ------------------------------------------------------------------

    def _classify_tier(
        self, bs_total: int, co_total: int, aggregate: int
    ) -> tuple[str, list[str]]:
        notes = []
        meets_section_min = bs_total >= HIGHLY_QUALIFIED_SECTION_MIN and co_total >= HIGHLY_QUALIFIED_SECTION_MIN
        meets_aggregate = aggregate >= HIGHLY_QUALIFIED_AGGREGATE_MIN

        # THE THRESHOLDS ARE INTERPOLATED, NOT TYPED. These three sentences
        # carried the literals "40-point" and "85-point" while the comparisons
        # beside them read HIGHLY_QUALIFIED_SECTION_MIN and
        # HIGHLY_QUALIFIED_AGGREGATE_MIN. Moving either constant would have
        # changed which applications were gated out while the printed
        # explanation went on naming the old bar — a document stating one rule
        # and a program applying another. tests/pinned_constants.txt pins the
        # rendered sentence, and a pin over a literal pins the typing.
        if bs_total < HIGHLY_QUALIFIED_SECTION_MIN:
            notes.append(
                f"Business Strategy section ({bs_total}/{BUSINESS_STRATEGY_MAX}) is below the "
                f"{HIGHLY_QUALIFIED_SECTION_MIN}-point minimum required for "
                "Highly Qualified status."
            )
        if co_total < HIGHLY_QUALIFIED_SECTION_MIN:
            notes.append(
                f"Community Outcomes section ({co_total}/{COMMUNITY_OUTCOMES_MAX}) is below the "
                f"{HIGHLY_QUALIFIED_SECTION_MIN}-point minimum required for "
                "Highly Qualified status."
            )
        if not meets_aggregate and (meets_section_min or aggregate >= 70):
            notes.append(
                f"Aggregate base score ({aggregate}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX}) is below the "
                f"{HIGHLY_QUALIFIED_AGGREGATE_MIN}-point minimum required for "
                "Highly Qualified status."
            )

        if meets_section_min and meets_aggregate:
            # Check top tier
            top_sections = bs_total >= HOUSE_TOP_TIER_SECTION_MIN and co_total >= HOUSE_TOP_TIER_SECTION_MIN
            top_agg = aggregate >= HOUSE_TOP_TIER_AGGREGATE_MIN
            if top_sections and top_agg:
                return "Top Tier", []
            return "Highly Qualified", notes

        return "Not Qualified", notes

    # ------------------------------------------------------------------
    # Phase 2 flags (not scored, reported as indicators)
    # ------------------------------------------------------------------

    def _build_phase2_flags(
        self, attrs: dict, result: "PipelineAnalysisResult"
    ) -> dict:
        flags = {}

        # NON-METRO: A COMMITMENT THE CDE DECLARES, AND A PIPELINE SHARE THE
        # TOOL MEASURES. Two different facts. This block used to publish the
        # second under the first's name and drop the first on the floor.
        #
        # WHAT WAS HERE, and why each line went:
        #
        #   flags["non_metro_commitment_pct"] = round(rural_pct * 100, 1)
        #
        # `non_metro_commitment_pct` IS A CDE PROFILE FIELD. It ships in
        # templates/cde_profile_sample.yaml as `non_metro_commitment_pct: 0.22`
        # — a CDE's own answer to Question 22(c) — and arrives here in `attrs`
        # via CDEProfile.extra, exactly like has_favorable_fee_structure two
        # lines below, which IS read from attrs. This line ignored it and wrote
        # a computed pipeline share over the top, under the identical key and
        # in different units (the YAML is a fraction; this wrote a percentage
        # number). A CDE who declared 22% read back 7.0 and had no way to see
        # which number that was. It is the fourth instance of this package
        # discarding a column the CDE filled in — after native_area,
        # urban_rural and the declared tract/distress pair.
        #
        # It is also misnamed on its own terms: a pipeline share is not a
        # commitment. Question 22(c) asks what the Applicant "is willing to
        # commit to deploy", which is a forward undertaking about capital not
        # yet raised. The word `commitment` now appears only on the CDE's own
        # declaration, never on anything this tool computed.
        #
        #   flags["non_metro_meets_minimum"] = rural_pct >= 0.20
        #
        # DELETED OUTRIGHT, not renamed. THERE IS NO 20% APPLICANT THRESHOLD.
        # The 20% is a CDFI Fund goal across "all QLICIs made by Allocatees
        # under this Round" and a bar on what an Allocatee has COMMITTED to;
        # Question 22 states no minimum an individual Applicant must clear, and
        # the question is not scored in Phase I at all. Comparing one CDE's QEI
        # share to a Fund-wide target and rendering the result as a boolean
        # called `meets_minimum` told a CDE it had failed a bar that does not
        # exist. Its consumers were: none — one write, no reads, in this
        # package or its docs. See renderers/_question_22 for the instrument.
        flags["non_metro_commitment_pct"] = attrs.get(
            "non_metro_commitment_pct", None
        )
        # The measured pipeline share, named for what it is: a share of QEI,
        # measured, not committed to. None-safe because an empty pipeline
        # determines nothing.
        flags["non_metro_pipeline_qei_pct"] = round(
            result.geographic_diversity.get("non_metro_pct", 0.0) * 100, 1
        )
        flags["non_metro_undetermined_qei_pct"] = round(
            result.geographic_diversity.get("metro_undetermined_pct", 0.0) * 100, 1
        )

        # Fee structure (informational; set in attrs if known)
        flags["favorable_fee_structure"] = attrs.get("has_favorable_fee_structure", None)

        # Prior compliance (deductions risk; assume clean unless specified)
        flags["prior_reporting_compliance_risk"] = attrs.get(
            "has_prior_reporting_issues", False
        )

        return flags

    # ------------------------------------------------------------------
    # Deprecated helper (kept for backward compat)
    # ------------------------------------------------------------------

    def _classify_tier_legacy(self, score: float) -> str:
        """Map old 0–100 composite to legacy tier names. Deprecated."""
        warnings.warn(
            "_classify_tier_legacy is deprecated; use tier from WinProbabilityScore.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _map_tier_legacy_from_score(score)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_int(value: float) -> int:
    return max(0, min(110, int(round(value))))


def _map_tier_legacy(tier: str) -> str:
    """Map a tier label to the legacy ``competitive_tier`` vocabulary.

    The default is "not_rated", NOT "marginal". In degraded mode ``tier`` is
    the sentinel "Not Rated — eligibility data unavailable", deliberately
    withheld because 25 of 100 base points could not be assessed. Defaulting
    an unmapped label to "marginal" manufactured exactly the rating the
    scoring code had refused to assign.
    """
    return {
        "Top Tier": "strong",
        "Highly Qualified": "competitive",
        "Not Qualified": "weak",
    }.get(tier, "not_rated")


def _map_tier_legacy_from_score(score: float) -> str:
    if score >= HOUSE_TOP_TIER_AGGREGATE_MIN:
        return "strong"
    if score >= HIGHLY_QUALIFIED_AGGREGATE_MIN:
        return "competitive"
    if score >= 70:
        return "marginal"
    return "weak"


def _build_peer_comparison(score: "WinProbabilityScore") -> str:
    tier = score.tier
    agg = score.aggregate_base_score
    if score.partial:
        return (
            f"NOT RATED — eligibility data unavailable. {score.partial_note}. "
            "Restore nmtc-mapper data access and re-score before drawing any "
            "conclusions from this partial result."
        )
    bs = score.business_strategy.get("section_total", 0)
    co = score.community_outcomes.get("section_total", 0)
    pp = score.priority_points.get("section_total", 0)

    if tier == "Top Tier":
        # D4, SIXTH SURFACE — found in 1.2.2 round 2, on neither round 1's list
        # of four nor the gate's radar (the string names no authority token, so
        # tests/test_fund_attribution_source.py could not see it).
        #
        # This ended: "High probability of Phase 2 advancement; award may
        # approach the maximum requested." Two claims, both wrong to make here:
        #
        #   * an AWARD PREDICTION, which this package disclaims in the same
        #     breath everywhere else --- "Not a win probability calculator. The
        #     CDFI Fund does not publish scores or application data for
        #     non-winning applicants" (docs/reference/methodology.md) --- and
        #   * attached to a tier the CDFI Fund does not publish, so the
        #     prediction rested on an invented gate.
        #
        # What is actually true above the published gate is that ranking and the
        # Phase 2 panel decide it, and the Review Process says ranking uses only
        # HALF the priority points (p.3 Step 2) --- which this package does not
        # model at all.
        return (
            f"Top Tier ({agg}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX}). Both sections exceed the "
            f"{HOUSE_TOP_TIER_SECTION_MIN}-point threshold. "
            "\"Top Tier\" is this tool's own label, not a CDFI Fund tier: the "
            f"Fund publishes the Highly Qualified gate ({HIGHLY_QUALIFIED_AGGREGATE_MIN} "
            f"aggregate, {HIGHLY_QUALIFIED_SECTION_MIN} per section) and nothing above it, and these cut "
            "points are an unsourced house heuristic. This application is well "
            "clear of the published gate, and is in the same Highly Qualified "
            "pool as any other application that clears it. No award outcome "
            "follows: above the gate the CDFI Fund ranks applicants (inclusive "
            "of half their priority points) and an Allocation Recommendation "
            "Panel decides, neither of which this tool models."
        )
    if tier == "Highly Qualified":
        weak_section = "Business Strategy" if bs < co else "Community Outcomes"
        return (
            f"Highly Qualified ({agg}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX}). Both sections meet the "
            f"{HIGHLY_QUALIFIED_SECTION_MIN}-point minimum. "
            f"Priority Points: {pp}/{PRIORITY_POINTS_MAX}. Phase 2 review of Management Capacity and "
            f"Capitalization Strategy will determine final ranking. "
            f"Focus improvement on {weak_section} ({min(bs, co)}/{BUSINESS_STRATEGY_MAX})."
        )
    # Not Qualified
    below = []
    # Same rule as _classify_tier: the bar prints from the constant it gates on.
    if bs < HIGHLY_QUALIFIED_SECTION_MIN:
        below.append(f"Business Strategy ({bs}/{BUSINESS_STRATEGY_MAX} < {HIGHLY_QUALIFIED_SECTION_MIN})")
    if co < HIGHLY_QUALIFIED_SECTION_MIN:
        below.append(f"Community Outcomes ({co}/{COMMUNITY_OUTCOMES_MAX} < {HIGHLY_QUALIFIED_SECTION_MIN})")
    if agg < HIGHLY_QUALIFIED_AGGREGATE_MIN:
        below.append(f"Aggregate ({agg}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX} < {HIGHLY_QUALIFIED_AGGREGATE_MIN})")
    gap_str = "; ".join(below) if below else f"aggregate {agg}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX}"
    return (
        f"Not Qualified ({agg}/{BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX}). Application does not meet the Highly Qualified "
        f"gating thresholds — {gap_str}. Significant pipeline or CDE positioning "
        "changes are needed before submission."
    )

