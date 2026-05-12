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

import math
import warnings
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import (
    SEVERE_DISTRESS_MIN_PCT,
    DEEP_DISTRESS_MIN_PCT,
    SPECIAL_TARGETING_BONUS_PCT,
    TRACK_RECORD_PIPELINE_ALIGNMENT_MIN,
    TRACK_RECORD_DEPLOYMENT_MIN,
    PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT,
    PRODUCT_FLEXIBILITY_MIN_INDICIA,
    DBC_PRIORITY_YEARS_MIN,
    DBC_VOLUME_PCT_MIN,
    UNRELATED_ENTITIES_MIN_PCT,
    HIGHLY_QUALIFIED_AGGREGATE_MIN,
    HIGHLY_QUALIFIED_SECTION_MIN,
    TOP_TIER_AGGREGATE_MIN,
    TOP_TIER_SECTION_MIN,
)
from nmtcapp.data.historical_awards import get_overall_acceptance_rate

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

_METHODOLOGY = (
    "IMPORTANT: This score assesses alignment with the CDFI Fund's published CY 2024-2025 "
    "Review Process criteria (Business Strategy 50 pts + Community Outcomes 50 pts + Priority "
    "Points 10 pts). It is a self-assessment tool, not a guarantee of selection. Sub-score "
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
    competitive_tier: str = ""         # "strong" | "competitive" | "marginal" | "weak"
    peer_comparison: str = ""
    methodology_disclosure: str = field(default=_METHODOLOGY)

    def __post_init__(self) -> None:
        # Populate backward-compat fields from new structure
        if not self.composite_score:
            self.composite_score = float(self.aggregate_base_score)
        if not self.dimensional_scores:
            self.dimensional_scores = {
                "business_strategy": round(
                    self.business_strategy.get("section_total", 0) / 50 * 100, 1
                ),
                "community_outcomes": round(
                    self.community_outcomes.get("section_total", 0) / 50 * 100, 1
                ),
                "priority_points": round(
                    self.priority_points.get("section_total", 0) / 10 * 100, 1
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
        lines = [
            "=" * 70,
            "  NMTC APPLICATION SCORE  (CDFI Fund CY 2024-2025 Framework)",
            f"  Aggregate Base Score:    {self.aggregate_base_score} / 100",
            f"  With Priority Points:    {self.aggregate_with_priority} / 110",
            f"  Tier:                    {self.tier.upper()}",
            "=" * 70,
            "",
            f"  BUSINESS STRATEGY:  {bs['section_total']:2d} / 50",
            f"    Product Flexibility       {bs.get('product_flexibility', 0):2d} / 10",
            f"    Pipeline Credibility      {bs.get('pipeline_credibility', 0):2d} / 15",
            f"    Track Record Strength     {bs.get('track_record_strength', 0):2d} / 15",
            f"    Track Record Alignment    {bs.get('track_record_alignment', 0):2d} / 10",
            "",
            f"  COMMUNITY OUTCOMES: {co['section_total']:2d} / 50",
            f"    Higher Distress Targeting {co.get('higher_distress_targeting', 0):2d} / 15",
            f"    Deep Distress Commitment  {co.get('deep_distress_commitment', 0):2d} / 10",
            f"    Special Targeting         {co.get('special_targeting', 0):2d} /  5",
            f"    Community Outcomes Quality{co.get('community_outcomes_quality', 0):2d} / 10",
            f"    Community Accountability  {co.get('community_accountability', 0):2d} / 10",
            "",
            f"  PRIORITY POINTS:    {pp['section_total']:2d} / 10",
            f"    DBC Track Record          {pp.get('dbc_track_record', 0):2d} /  5",
            f"    Unrelated Entities        {pp.get('unrelated_entities', 0):2d} /  5",
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

        # --- Section 1: Business Strategy (0–50) ---
        pf = self._score_product_flexibility(attrs)
        pc = self._score_pipeline_credibility(pipeline_result, attrs)
        trs = self._score_track_record_strength(attrs)
        tra = self._score_track_record_alignment(attrs)
        bs_total = pf + pc + trs + tra

        business_strategy = {
            "product_flexibility": pf,
            "pipeline_credibility": pc,
            "track_record_strength": trs,
            "track_record_alignment": tra,
            "section_total": bs_total,
        }

        # --- Section 2: Community Outcomes (0–50) ---
        hdt = self._score_higher_distress(pipeline_result)
        ddc = self._score_deep_distress(pipeline_result)
        st  = self._score_special_targeting(pipeline_result, attrs)
        coq = self._score_outcomes_quality(attrs)
        ca  = self._score_community_accountability(attrs)
        co_total = hdt + ddc + st + coq + ca

        community_outcomes = {
            "higher_distress_targeting": hdt,
            "deep_distress_commitment": ddc,
            "special_targeting": st,
            "community_outcomes_quality": coq,
            "community_accountability": ca,
            "section_total": co_total,
        }

        # --- Priority Points (0–10) ---
        dbc = self._score_dbc_track_record(attrs)
        ue  = self._score_unrelated_entities(attrs)
        pp_total = dbc + ue

        priority_points = {
            "dbc_track_record": dbc,
            "unrelated_entities": ue,
            "section_total": pp_total,
        }

        aggregate_base = bs_total + co_total
        aggregate_with_priority = aggregate_base + pp_total

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
        )

    # ------------------------------------------------------------------
    # Business Strategy sub-scorers
    # ------------------------------------------------------------------

    def _score_product_flexibility(self, attrs: dict) -> int:
        below_mkt = attrs.get("products_below_market_pct", 0.0)
        indicia = attrs.get("products_flexible_indicia_count", 0)
        # Full credit if either threshold is met
        score_from_below_mkt = min(10.0, below_mkt / PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT * 10)
        score_from_indicia = min(10.0, indicia / PRODUCT_FLEXIBILITY_MIN_INDICIA * 10)
        return _to_int(max(score_from_below_mkt, score_from_indicia))

    def _score_pipeline_credibility(
        self, result: "PipelineAnalysisResult", attrs: dict
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
        # Eligibility bonus: subtract up to 2 pts if eligibility rate is low
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
        deploy_score = min(5.0, deploy_pct / TRACK_RECORD_DEPLOYMENT_MIN * 5.0)
        return _to_int(align_score + deploy_score)

    # ------------------------------------------------------------------
    # Community Outcomes sub-scorers
    # ------------------------------------------------------------------

    def _score_higher_distress(self, result: "PipelineAnalysisResult") -> int:
        pct = result.distress_breakdown.get("pct_deep_or_severe", 0.0)
        return _to_int(min(15.0, pct / SEVERE_DISTRESS_MIN_PCT * 15.0))

    def _score_deep_distress(self, result: "PipelineAnalysisResult") -> int:
        # Use pct_deep if available; fall back to 50% of pct_deep_or_severe
        d = result.distress_breakdown
        deep_pct = d.get("pct_deep", d.get("pct_deep_or_severe", 0.0) * 0.5)
        return _to_int(min(10.0, deep_pct / DEEP_DISTRESS_MIN_PCT * 10.0))

    def _score_special_targeting(
        self, result: "PipelineAnalysisResult", attrs: dict
    ) -> int:
        d = result.distress_breakdown
        # Check four qualifying categories; each 10%+ in a category = 1.25 pts (max 5)
        categories = [
            d.get("pct_native_area", 0.0),
            d.get("pct_high_migration_rural", 0.0),
            attrs.get("pct_persistent_poverty", 0.0),
            attrs.get("pct_us_territories", 0.0),
        ]
        qualified = sum(1 for c in categories if c >= SPECIAL_TARGETING_BONUS_PCT)
        # Partial credit: weight by concentration in each category (up to 1.25 each)
        partial = sum(
            min(1.25, c / SPECIAL_TARGETING_BONUS_PCT * 1.25) for c in categories
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

    def _score_unrelated_entities(self, attrs: dict) -> int:
        pct = attrs.get("unrelated_entities_pct", 0.0)
        return _to_int(min(5.0, pct / UNRELATED_ENTITIES_MIN_PCT * 5.0))

    # ------------------------------------------------------------------
    # Gating / classification
    # ------------------------------------------------------------------

    def _classify_tier(
        self, bs_total: int, co_total: int, aggregate: int
    ) -> tuple[str, list[str]]:
        notes = []
        meets_section_min = bs_total >= HIGHLY_QUALIFIED_SECTION_MIN and co_total >= HIGHLY_QUALIFIED_SECTION_MIN
        meets_aggregate = aggregate >= HIGHLY_QUALIFIED_AGGREGATE_MIN

        if bs_total < HIGHLY_QUALIFIED_SECTION_MIN:
            notes.append(
                f"Business Strategy section ({bs_total}/50) is below the 40-point "
                "minimum required for Highly Qualified status."
            )
        if co_total < HIGHLY_QUALIFIED_SECTION_MIN:
            notes.append(
                f"Community Outcomes section ({co_total}/50) is below the 40-point "
                "minimum required for Highly Qualified status."
            )
        if not meets_aggregate and (meets_section_min or aggregate >= 70):
            notes.append(
                f"Aggregate base score ({aggregate}/100) is below the 85-point minimum "
                "required for Highly Qualified status."
            )

        if meets_section_min and meets_aggregate:
            # Check top tier
            top_sections = bs_total >= TOP_TIER_SECTION_MIN and co_total >= TOP_TIER_SECTION_MIN
            top_agg = aggregate >= TOP_TIER_AGGREGATE_MIN
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

        # Non-metro commitment
        rural_pct = result.geographic_diversity.get("rural_pct", 0.0)
        flags["non_metro_commitment_pct"] = round(rural_pct * 100, 1)
        flags["non_metro_meets_minimum"] = rural_pct >= 0.20

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
    return {
        "Top Tier": "strong",
        "Highly Qualified": "competitive",
        "Not Qualified": "weak",
    }.get(tier, "marginal")


def _map_tier_legacy_from_score(score: float) -> str:
    if score >= TOP_TIER_AGGREGATE_MIN:
        return "strong"
    if score >= HIGHLY_QUALIFIED_AGGREGATE_MIN:
        return "competitive"
    if score >= 70:
        return "marginal"
    return "weak"


def _build_peer_comparison(score: "WinProbabilityScore") -> str:
    tier = score.tier
    agg = score.aggregate_base_score
    bs = score.business_strategy.get("section_total", 0)
    co = score.community_outcomes.get("section_total", 0)
    pp = score.priority_points.get("section_total", 0)

    if tier == "Top Tier":
        return (
            f"Top Tier ({agg}/100). Both sections exceed the 45-point threshold. "
            "High probability of Phase 2 advancement; award may approach the maximum requested."
        )
    if tier == "Highly Qualified":
        weak_section = "Business Strategy" if bs < co else "Community Outcomes"
        return (
            f"Highly Qualified ({agg}/100). Both sections meet the 40-point minimum. "
            f"Priority Points: {pp}/10. Phase 2 review of Management Capacity and "
            f"Capitalization Strategy will determine final ranking. "
            f"Focus improvement on {weak_section} ({min(bs, co)}/50)."
        )
    # Not Qualified
    below = []
    if bs < HIGHLY_QUALIFIED_SECTION_MIN:
        below.append(f"Business Strategy ({bs}/50 < 40)")
    if co < HIGHLY_QUALIFIED_SECTION_MIN:
        below.append(f"Community Outcomes ({co}/50 < 40)")
    if agg < HIGHLY_QUALIFIED_AGGREGATE_MIN:
        below.append(f"Aggregate ({agg}/100 < 85)")
    gap_str = "; ".join(below) if below else f"aggregate {agg}/100"
    return (
        f"Not Qualified ({agg}/100). Application does not meet the Highly Qualified "
        f"gating thresholds — {gap_str}. Significant pipeline or CDE positioning "
        "changes are needed before submission."
    )


def _normal_cdf(x: float) -> float:
    return math.erfc(-x / math.sqrt(2)) * 0.5


def _mini_bar(score: float, width: int = 12) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)
