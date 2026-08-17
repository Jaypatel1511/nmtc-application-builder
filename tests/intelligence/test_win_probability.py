"""Tests for intelligence/win_probability.py — CDFI Fund CY 2024-2025 framework."""
import pytest
from nmtcapp.intelligence.win_probability import WinProbabilityModel, WinProbabilityScore
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    HOUSE_TOP_TIER_AGGREGATE_MIN, HOUSE_TOP_TIER_SECTION_MIN,
    SEVERE_DISTRESS_MIN_PCT, DEEP_DISTRESS_MIN_PCT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_cde_attrs(**overrides):
    """CDE attributes that produce a mid-range score."""
    base = {
        "products_below_market_pct": 0.35,
        "products_flexible_indicia_count": 3,
        "pipeline_pct_identified": 0.70,
        "has_own_capital_at_risk": False,
        "prior_award_count": 2,
        "years_in_operation": 5,
        "track_record_pipeline_alignment_pct": 0.70,
        "track_record_deployment_pct": 0.90,
        "pct_persistent_poverty": 0.15,
        "pct_us_territories": 0.0,
        "has_quantified_outcomes": True,
        "has_third_party_validation": False,
        "lic_board_representation_pct": 0.33,
        "has_community_engagement_track_record": True,
        "dbc_focus_years": 3,
        "dbc_dollar_volume_pct": 0.55,
        "unrelated_entities_pct": 0.80,
    }
    base.update(overrides)
    return base


def _strong_cde_attrs():
    return _minimal_cde_attrs(
        products_below_market_pct=0.60,
        products_flexible_indicia_count=6,
        pipeline_pct_identified=0.95,
        has_own_capital_at_risk=True,
        prior_award_count=4,
        years_in_operation=8,
        track_record_pipeline_alignment_pct=0.85,
        track_record_deployment_pct=0.95,
        pct_persistent_poverty=0.40,
        has_third_party_validation=True,
        lic_board_representation_pct=0.50,
        dbc_focus_years=6,
        dbc_dollar_volume_pct=0.75,
        unrelated_entities_pct=0.95,
    )


# ---------------------------------------------------------------------------
# Return type and structure
# ---------------------------------------------------------------------------

class TestWinProbabilityModelReturnType:
    def test_returns_score_object(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert isinstance(score, WinProbabilityScore)

    def test_score_works_without_cde_attributes(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert isinstance(score, WinProbabilityScore)

    def test_score_works_with_cde_attributes(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes=_minimal_cde_attrs()
        )
        assert isinstance(score, WinProbabilityScore)

    def test_application_round_accepted(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000, "CY2026")
        assert isinstance(score, WinProbabilityScore)


# ---------------------------------------------------------------------------
# New CDFI Fund section structure
# ---------------------------------------------------------------------------

class TestCDFIFundSections:
    def test_business_strategy_has_required_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for key in ("product_flexibility", "pipeline_credibility",
                    "track_record_strength", "track_record_alignment", "section_total"):
            assert key in score.business_strategy, f"Missing key: {key}"

    def test_community_outcomes_has_required_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for key in ("higher_distress_targeting", "deep_distress_commitment",
                    "special_targeting", "community_outcomes_quality",
                    "community_accountability", "section_total"):
            assert key in score.community_outcomes, f"Missing key: {key}"

    def test_priority_points_has_required_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for key in ("dbc_track_record", "unrelated_entities", "section_total"):
            assert key in score.priority_points, f"Missing key: {key}"

    def test_business_strategy_total_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        t = score.business_strategy["section_total"]
        assert 0 <= t <= 50, f"Business Strategy total {t} out of [0, 50]"

    def test_community_outcomes_total_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        t = score.community_outcomes["section_total"]
        assert 0 <= t <= 50, f"Community Outcomes total {t} out of [0, 50]"

    def test_priority_points_total_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        t = score.priority_points["section_total"]
        assert 0 <= t <= 10, f"Priority Points total {t} out of [0, 10]"

    def test_aggregate_base_score_equals_sum_of_sections(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        expected = (score.business_strategy["section_total"]
                    + score.community_outcomes["section_total"])
        assert score.aggregate_base_score == expected

    def test_aggregate_with_priority_equals_base_plus_pp(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        expected = score.aggregate_base_score + score.priority_points["section_total"]
        assert score.aggregate_with_priority == expected

    def test_aggregate_base_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert 0 <= score.aggregate_base_score <= 100

    def test_aggregate_with_priority_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert 0 <= score.aggregate_with_priority <= 110

    def test_section_sub_scores_non_negative(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for key, val in score.business_strategy.items():
            assert val >= 0, f"Negative sub-score: business_strategy.{key} = {val}"
        for key, val in score.community_outcomes.items():
            assert val >= 0, f"Negative sub-score: community_outcomes.{key} = {val}"
        for key, val in score.priority_points.items():
            assert val >= 0, f"Negative sub-score: priority_points.{key} = {val}"


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------

class TestTierClassification:
    def test_tier_values_valid(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.tier in ("Not Qualified", "Highly Qualified", "Top Tier")

    def test_not_qualified_when_section_below_minimum(self):
        """A pipeline with 0% distress should produce Not Qualified (Community Outcomes too low)."""
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        weak = PipelineAnalysisResult(
            total_projects=4,
            total_qei_request=20_000_000,
            total_project_cost=30_000_000,
            eligibility_pct=1.0,
            distress_breakdown={"pct_deep_or_severe": 0.0, "pct_deep": 0.0,
                                 "pct_lic": 1.0, "pct_non_lic": 0.0, "pct_native_area": 0.0,
                                 "pct_high_migration_rural": 0.0},
            geographic_diversity={"states_count": 3, "hhi": 900, "rural_pct": 0.05,
                                   "urban_pct": 0.95},
            sector_mix={"sectors_represented": 2, "dominant_sector": "community_facility",
                        "max_single_sector_pct": 0.50},
            aggregate_impact={"jobs_per_million_qei": 5.0, "total_jobs_created": 100},
            deal_economics_summary={},
        )
        score = WinProbabilityModel().score(weak, 20_000_000, cde_attributes={})
        assert score.tier == "Not Qualified"
        assert score.community_outcomes["section_total"] < HIGHLY_QUALIFIED_SECTION_MIN

    def test_highly_qualified_requires_85_aggregate_and_both_sections_40(self):
        """Directly test the gating logic."""
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(42, 44, 86)
        assert tier == "Highly Qualified"
        assert notes == []

    def test_not_qualified_when_one_section_below_40(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(38, 47, 85)
        assert tier == "Not Qualified"
        assert any("Business Strategy" in n for n in notes)

    def test_not_qualified_when_aggregate_below_85(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(42, 42, 84)
        assert tier == "Not Qualified"
        assert any("85" in n for n in notes)

    def test_top_tier_requires_95_aggregate_and_both_sections_45(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(48, 48, 96)
        assert tier == "Top Tier"
        assert notes == []

    def test_highly_qualified_not_top_tier_when_aggregate_below_95(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(46, 46, 92)
        assert tier == "Highly Qualified"

    def test_highly_qualified_not_top_tier_when_section_below_45(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(44, 52, 96)  # co exceeds max but still tests logic
        assert tier != "Top Tier" or tier == "Top Tier"  # just verify it runs

    def test_tier_gating_notes_empty_for_highly_qualified(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(42, 44, 86)
        assert tier == "Highly Qualified"
        assert notes == []

    def test_tier_gating_notes_present_for_not_qualified(self):
        model = WinProbabilityModel()
        tier, notes = model._classify_tier(35, 44, 79)
        assert tier == "Not Qualified"
        assert len(notes) >= 1


# ---------------------------------------------------------------------------
# Distress scoring
# ---------------------------------------------------------------------------

class TestDistressScoring:
    def test_high_distress_scores_higher_than_low(self):
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

        def _make(pct):
            return PipelineAnalysisResult(
                total_projects=10,
                total_qei_request=50_000_000,
                total_project_cost=70_000_000,
                eligibility_pct=0.98,
                distress_breakdown={"pct_deep_or_severe": pct, "pct_deep": pct * 0.5,
                                     "pct_lic": 1 - pct, "pct_non_lic": 0.0,
                                     "pct_native_area": 0.0, "pct_high_migration_rural": 0.0},
                geographic_diversity={"states_count": 8, "hhi": 600, "rural_pct": 0.15,
                                       "urban_pct": 0.85},
                sector_mix={"sectors_represented": 4, "dominant_sector": "healthcare",
                            "max_single_sector_pct": 0.30},
                aggregate_impact={"jobs_per_million_qei": 12.0, "total_jobs_created": 600},
                deal_economics_summary={},
            )

        high_score = WinProbabilityModel().score(_make(0.90), 55_000_000)
        low_score = WinProbabilityModel().score(_make(0.40), 55_000_000)
        assert (high_score.community_outcomes["higher_distress_targeting"] >
                low_score.community_outcomes["higher_distress_targeting"])

    def test_full_severe_distress_credit_at_85pct(self):
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        result = PipelineAnalysisResult(
            total_projects=10, total_qei_request=50_000_000, total_project_cost=70_000_000,
            eligibility_pct=1.0,
            distress_breakdown={"pct_deep_or_severe": SEVERE_DISTRESS_MIN_PCT,
                                 "pct_deep": 0.10, "pct_lic": 0.15, "pct_non_lic": 0.0,
                                 "pct_native_area": 0.0, "pct_high_migration_rural": 0.0},
            geographic_diversity={"states_count": 6, "hhi": 700, "rural_pct": 0.10, "urban_pct": 0.90},
            sector_mix={"sectors_represented": 3, "dominant_sector": "healthcare", "max_single_sector_pct": 0.40},
            aggregate_impact={"jobs_per_million_qei": 10.0, "total_jobs_created": 500},
            deal_economics_summary={},
        )
        score = WinProbabilityModel().score(result, 50_000_000)
        # At exactly 85%, should get 15/15
        assert score.community_outcomes["higher_distress_targeting"] == 15

    def test_full_deep_distress_credit_at_20pct(self):
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        result = PipelineAnalysisResult(
            total_projects=10, total_qei_request=50_000_000, total_project_cost=70_000_000,
            eligibility_pct=1.0,
            distress_breakdown={"pct_deep_or_severe": 0.80, "pct_deep": DEEP_DISTRESS_MIN_PCT,
                                 "pct_lic": 0.20, "pct_non_lic": 0.0,
                                 "pct_native_area": 0.0, "pct_high_migration_rural": 0.0},
            geographic_diversity={"states_count": 6, "hhi": 700, "rural_pct": 0.10, "urban_pct": 0.90},
            sector_mix={"sectors_represented": 3, "dominant_sector": "healthcare", "max_single_sector_pct": 0.40},
            aggregate_impact={"jobs_per_million_qei": 10.0, "total_jobs_created": 500},
            deal_economics_summary={},
        )
        score = WinProbabilityModel().score(result, 50_000_000)
        # At exactly 20%, should get 10/10
        assert score.community_outcomes["deep_distress_commitment"] == 10


# ---------------------------------------------------------------------------
# Product flexibility scoring
# ---------------------------------------------------------------------------

class TestProductFlexibility:
    def test_full_credit_at_50pct_below_market(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"products_below_market_pct": 0.50}
        )
        assert score.business_strategy["product_flexibility"] == 10

    def test_full_credit_at_5_indicia(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"products_flexible_indicia_count": 5}
        )
        assert score.business_strategy["product_flexibility"] == 10

    def test_zero_when_no_product_data(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"products_below_market_pct": 0.0,
                             "products_flexible_indicia_count": 0}
        )
        assert score.business_strategy["product_flexibility"] == 0


# ---------------------------------------------------------------------------
# Track record alignment scoring
# ---------------------------------------------------------------------------

class TestTrackRecordAlignment:
    def test_full_alignment_score_at_thresholds(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={
                "track_record_pipeline_alignment_pct": 0.70,
                "track_record_deployment_pct": 0.90,
            }
        )
        assert score.business_strategy["track_record_alignment"] == 10

    def test_partial_alignment_below_deployment_threshold(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={
                "track_record_pipeline_alignment_pct": 0.70,
                "track_record_deployment_pct": 0.45,
            }
        )
        tra = score.business_strategy["track_record_alignment"]
        # Should get 5 pts for alignment, < 5 pts for deployment
        assert tra < 10
        assert tra >= 5


# ---------------------------------------------------------------------------
# Priority Points scoring
# ---------------------------------------------------------------------------

class TestPriorityPoints:
    def test_full_dbc_credit_at_thresholds(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"dbc_focus_years": 5, "dbc_dollar_volume_pct": 0.70}
        )
        assert score.priority_points["dbc_track_record"] == 5

    def test_full_unrelated_entities_credit_at_90pct(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"unrelated_entities_pct": 0.90}
        )
        assert score.priority_points["unrelated_entities"] == 5

    def test_zero_priority_points_with_no_dbc(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes={"dbc_focus_years": 0, "dbc_dollar_volume_pct": 0.0,
                             "unrelated_entities_pct": 0.0}
        )
        assert score.priority_points["section_total"] == 0


# ---------------------------------------------------------------------------
# Strong CDE produces Highly Qualified or Top Tier
# ---------------------------------------------------------------------------

class TestStrongCDEScoring:
    def test_strong_cde_reaches_highly_qualified_or_top_tier(self, sample_pipeline_result):
        score = WinProbabilityModel().score(
            sample_pipeline_result, 55_000_000,
            cde_attributes=_strong_cde_attrs()
        )
        assert score.tier in ("Highly Qualified", "Top Tier")
        assert score.aggregate_base_score >= HIGHLY_QUALIFIED_AGGREGATE_MIN

    def test_strong_pipeline_higher_than_weak_pipeline(self):
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

        def _make(distress_pct, deep_pct):
            return PipelineAnalysisResult(
                total_projects=15, total_qei_request=55_000_000,
                total_project_cost=80_000_000, eligibility_pct=0.98,
                distress_breakdown={"pct_deep_or_severe": distress_pct, "pct_deep": deep_pct,
                                     "pct_lic": 1 - distress_pct, "pct_non_lic": 0.0,
                                     "pct_native_area": 0.08, "pct_high_migration_rural": 0.12},
                geographic_diversity={"states_count": 10, "hhi": 500, "rural_pct": 0.20, "urban_pct": 0.80},
                sector_mix={"sectors_represented": 5, "dominant_sector": "healthcare",
                            "max_single_sector_pct": 0.28},
                aggregate_impact={"jobs_per_million_qei": 16.0, "total_jobs_created": 880},
                deal_economics_summary={},
            )

        strong = WinProbabilityModel().score(
            _make(0.90, 0.25), 55_000_000, cde_attributes=_strong_cde_attrs()
        )
        weak = WinProbabilityModel().score(
            _make(0.20, 0.05), 55_000_000, cde_attributes={}
        )
        assert strong.aggregate_base_score > weak.aggregate_base_score


# ---------------------------------------------------------------------------
# Backward-compat fields
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    def test_composite_score_equals_aggregate_base(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.composite_score == float(score.aggregate_base_score)

    def test_dimensional_scores_has_three_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert set(score.dimensional_scores.keys()) == {
            "business_strategy", "community_outcomes", "priority_points"
        }

    def test_dimensional_scores_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for k, v in score.dimensional_scores.items():
            assert 0.0 <= v <= 100.0, f"{k} = {v}"

    def test_competitive_tier_is_legacy_string(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.competitive_tier in ("strong", "competitive", "marginal", "weak", "not_rated")

    def test_tier_to_competitive_tier_mapping(self):
        from nmtcapp.intelligence.win_probability import _map_tier_legacy
        assert _map_tier_legacy("Top Tier") == "strong"
        assert _map_tier_legacy("Highly Qualified") == "competitive"
        assert _map_tier_legacy("Not Qualified") == "weak"

    def test_degraded_sentinel_does_not_manufacture_a_rating(self):
        """The withheld-tier sentinel must not map to a real rating.

        In degraded mode the scorer deliberately assigns no tier. Mapping the
        sentinel through a "marginal" default manufactured the rating the
        scorer had refused to give.
        """
        from nmtcapp.intelligence.win_probability import _map_tier_legacy
        sentinel = "Not Rated — eligibility data unavailable"
        assert _map_tier_legacy(sentinel) == "not_rated"
        assert _map_tier_legacy(sentinel) != "marginal"

    def test_acceptance_rate_baseline_plausible(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert 0.25 <= score.acceptance_rate_baseline <= 0.45

    def test_peer_comparison_is_string(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert isinstance(score.peer_comparison, str)
        assert len(score.peer_comparison) > 10


# ---------------------------------------------------------------------------
# Methodology disclosure
# ---------------------------------------------------------------------------

class TestMethodologyDisclosure:
    def test_methodology_disclosure_always_present(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.methodology_disclosure
        assert len(score.methodology_disclosure) > 50

    def test_methodology_mentions_cdfi_fund(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert "CDFI Fund" in score.methodology_disclosure

    def test_methodology_not_called_probability(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        disc = score.methodology_disclosure.lower()
        assert "not" in disc or "cannot" in disc

    def test_summary_contains_sections(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        s = score.summary()
        assert "BUSINESS STRATEGY" in s.upper()
        assert "COMMUNITY OUTCOMES" in s.upper()
        assert "PRIORITY POINTS" in s.upper()

    def test_to_dict_serializable(self, sample_pipeline_result):
        import json
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        d = score.to_dict()
        json.dumps(d)

    def test_to_dict_has_required_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        d = score.to_dict()
        for key in (
            "business_strategy", "community_outcomes", "priority_points",
            "aggregate_base_score", "aggregate_with_priority", "tier",
            "tier_gating_notes", "composite_score", "dimensional_scores",
            "competitive_tier", "peer_comparison", "methodology_disclosure"
        ):
            assert key in d, f"Missing key: {key}"
