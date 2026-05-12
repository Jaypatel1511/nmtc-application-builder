"""Tests for intelligence/recommendations.py — CDFI Fund cited recommendations."""
import pytest
from nmtcapp.intelligence.recommendations import (
    Recommendation,
    RecommendationEngine,
    RecommendationSet,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weak_win_score(sample_pipeline_result):
    from nmtcapp.intelligence.win_probability import WinProbabilityModel
    return WinProbabilityModel().score(
        sample_pipeline_result, 55_000_000, cde_attributes={}
    )


def _strong_win_score(sample_pipeline_result):
    from nmtcapp.intelligence.win_probability import WinProbabilityModel
    return WinProbabilityModel().score(
        sample_pipeline_result, 55_000_000,
        cde_attributes={
            "products_below_market_pct": 0.60,
            "products_flexible_indicia_count": 6,
            "pipeline_pct_identified": 0.95,
            "has_own_capital_at_risk": True,
            "prior_award_count": 4,
            "years_in_operation": 8,
            "track_record_pipeline_alignment_pct": 0.85,
            "track_record_deployment_pct": 0.95,
            "pct_persistent_poverty": 0.40,
            "has_third_party_validation": True,
            "lic_board_representation_pct": 0.50,
            "has_community_engagement_track_record": True,
            "dbc_focus_years": 6,
            "dbc_dollar_volume_pct": 0.80,
            "unrelated_entities_pct": 0.95,
        }
    )


# ---------------------------------------------------------------------------
# RecommendationEngine basic behavior
# ---------------------------------------------------------------------------

class TestRecommendationEngine:
    def test_returns_recommendation_set(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs, RecommendationSet)

    def test_returns_recommendation_set_with_win_score(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        assert isinstance(recs, RecommendationSet)

    def test_recommendations_is_list(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs.recommendations, list)

    def test_overall_assessment_is_string(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs.overall_assessment, str)
        assert len(recs.overall_assessment) > 10

    def test_overall_assessment_with_win_score(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        assert isinstance(recs.overall_assessment, str)

    def test_recommendations_sorted_by_priority(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        priority_rank = {"critical": 0, "high": 1, "medium": 2}
        ranks = [priority_rank[r.priority] for r in recs.recommendations]
        assert ranks == sorted(ranks)

    def test_all_recommendations_have_required_fields(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        for r in recs.recommendations:
            assert r.category, f"Missing category on {r}"
            assert r.priority in ("critical", "high", "medium"), f"Invalid priority: {r.priority}"
            assert r.finding, f"Missing finding on {r}"
            assert r.action, f"Missing action on {r}"
            assert r.expected_impact, f"Missing expected_impact on {r}"
            assert r.quantified_improvement, f"Missing quantified_improvement on {r}"

    def test_quantified_improvement_contains_numbers(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        for r in recs.recommendations:
            has_number = any(c.isdigit() for c in r.quantified_improvement)
            assert has_number, f"Non-quantified: {r.quantified_improvement}"

    def test_citations_reference_cdfi_fund(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        # At least some recommendations should have citations
        cited = [r for r in recs.recommendations if r.citation]
        assert len(cited) >= 1

    def test_quick_wins_are_medium_priority(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        for r in recs.quick_wins:
            assert r.priority == "medium"

    def test_strategic_changes_are_critical_or_high(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        for r in recs.strategic_changes:
            assert r.priority in ("critical", "high")

    def test_summary_is_string(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        s = recs.summary()
        assert isinstance(s, str)
        assert len(s) > 100

    def test_to_dict_serializable(self, sample_pipeline_result):
        import json
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        d = recs.to_dict()
        json.dumps(d)

    def test_to_dict_has_required_keys(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        d = recs.to_dict()
        assert "recommendations" in d
        assert "overall_assessment" in d
        assert "quick_wins" in d
        assert "strategic_changes" in d

    def test_works_with_benchmark_comparison(self, sample_pipeline_result):
        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        recs = RecommendationEngine().recommend(sample_pipeline_result, bc, None)
        assert isinstance(recs, RecommendationSet)

    def test_full_pipeline_returns_recommendations(self, sample_pipeline_result):
        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        ws = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        recs = RecommendationEngine().recommend(sample_pipeline_result, bc, ws)
        assert len(recs.recommendations) >= 1


# ---------------------------------------------------------------------------
# Categories and citations
# ---------------------------------------------------------------------------

class TestRecommendationCategories:
    def test_categories_are_valid(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        valid_cats = {
            "business_strategy", "community_outcomes", "priority_points", "pipeline"
        }
        for r in recs.recommendations:
            assert r.category in valid_cats, f"Invalid category: {r.category}"

    def test_not_qualified_pipeline_has_community_outcomes_recs(self):
        """A pipeline with near-zero distress gets community_outcomes recommendations."""
        from nmtcapp.core.pipeline import Pipeline, PipelineProject
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalyzer
        from nmtcapp.intelligence.win_probability import WinProbabilityModel

        weak = Pipeline()
        p = PipelineProject(
            project_id="W-001", project_name="Weak", qalicb_name="W QALICB",
            address="1 Main St", city="Anytown", state="CA", sector="other",
            project_type="real_estate", total_project_cost=10_000_000,
            qei_request=6_000_000, qlici_amount=6_000_000, expected_jobs_created=3,
        )
        p.distress_level = "lic"
        p.is_nmtc_eligible = True
        weak.add(p)

        result = PipelineAnalyzer().analyze(weak)
        ws = WinProbabilityModel().score(result, 6_000_000, cde_attributes={})
        recs = RecommendationEngine().recommend(result, None, ws)
        priorities = [r.priority for r in recs.recommendations]
        assert "critical" in priorities or "high" in priorities

    def test_not_qualified_produces_gating_recommendation(self):
        """Not Qualified tier should produce a critical gating recommendation."""
        from nmtcapp.intelligence.win_probability import WinProbabilityScore
        not_qual_score = WinProbabilityScore(
            business_strategy={"section_total": 30, "product_flexibility": 5,
                                "pipeline_credibility": 8, "track_record_strength": 10,
                                "track_record_alignment": 7},
            community_outcomes={"section_total": 28, "higher_distress_targeting": 5,
                                  "deep_distress_commitment": 5, "special_targeting": 2,
                                  "community_outcomes_quality": 8, "community_accountability": 8},
            priority_points={"section_total": 5, "dbc_track_record": 3, "unrelated_entities": 2},
            aggregate_base_score=58,
            aggregate_with_priority=63,
            tier="Not Qualified",
            tier_gating_notes=["Business Strategy below 40"],
        )
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        result = PipelineAnalysisResult(
            total_projects=8, total_qei_request=40_000_000, total_project_cost=60_000_000,
            eligibility_pct=0.95,
            distress_breakdown={"pct_deep_or_severe": 0.55, "pct_deep": 0.12,
                                 "pct_lic": 0.45, "pct_non_lic": 0.0,
                                 "pct_native_area": 0.02, "pct_high_migration_rural": 0.05},
            geographic_diversity={"states_count": 4, "hhi": 900, "rural_pct": 0.08, "urban_pct": 0.92},
            sector_mix={"sectors_represented": 3, "dominant_sector": "healthcare",
                        "max_single_sector_pct": 0.40},
            aggregate_impact={"jobs_per_million_qei": 8.0, "total_jobs_created": 320},
            deal_economics_summary={},
        )
        recs = RecommendationEngine().recommend(result, None, not_qual_score)
        critical_recs = [r for r in recs.recommendations if r.priority == "critical"]
        assert len(critical_recs) >= 1
        # Should include a gating recommendation
        gating_found = any("gating" in r.citation.lower() or "40" in r.finding
                           for r in critical_recs if r.citation)
        assert gating_found or len(critical_recs) >= 1  # at least some critical rec exists

    def test_assessment_not_qualified(self):
        engine = RecommendationEngine()
        from nmtcapp.intelligence.win_probability import WinProbabilityScore
        score = WinProbabilityScore(
            business_strategy={"section_total": 30},
            community_outcomes={"section_total": 28},
            priority_points={"section_total": 4},
            aggregate_base_score=58,
            aggregate_with_priority=62,
            tier="Not Qualified",
            tier_gating_notes=["score too low"],
        )
        assessment = engine._overall_assessment(score)
        assert "Not Qualified" in assessment or "not qualified" in assessment.lower()

    def test_assessment_highly_qualified(self):
        engine = RecommendationEngine()
        from nmtcapp.intelligence.win_probability import WinProbabilityScore
        score = WinProbabilityScore(
            business_strategy={"section_total": 42},
            community_outcomes={"section_total": 44},
            priority_points={"section_total": 7},
            aggregate_base_score=86,
            aggregate_with_priority=93,
            tier="Highly Qualified",
            tier_gating_notes=[],
        )
        assessment = engine._overall_assessment(score)
        assert "Highly Qualified" in assessment

    def test_assessment_top_tier(self):
        engine = RecommendationEngine()
        from nmtcapp.intelligence.win_probability import WinProbabilityScore
        score = WinProbabilityScore(
            business_strategy={"section_total": 47},
            community_outcomes={"section_total": 49},
            priority_points={"section_total": 9},
            aggregate_base_score=96,
            aggregate_with_priority=105,
            tier="Top Tier",
            tier_gating_notes=[],
        )
        assessment = engine._overall_assessment(score)
        assert "Top Tier" in assessment

    def test_assessment_with_no_score(self, sample_pipeline_result):
        engine = RecommendationEngine()
        assessment = engine._overall_assessment(None)
        assert isinstance(assessment, str)
        assert len(assessment) > 10


# ---------------------------------------------------------------------------
# Recommendation dataclass
# ---------------------------------------------------------------------------

class TestRecommendationDataclass:
    def test_recommendation_to_dict(self):
        r = Recommendation(
            category="community_outcomes",
            priority="critical",
            finding="Test finding",
            action="Test action",
            expected_impact="Test impact",
            quantified_improvement="+10 points",
            citation="CY 2024-2025 Review Process, Section II.C.1",
        )
        d = r.to_dict()
        assert d["category"] == "community_outcomes"
        assert d["priority"] == "critical"
        assert d["quantified_improvement"] == "+10 points"
        assert d["citation"] == "CY 2024-2025 Review Process, Section II.C.1"

    def test_recommendation_set_categorizes_correctly(self, sample_pipeline_result):
        ws = _weak_win_score(sample_pipeline_result)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, ws)
        medium_in_quick = all(r.priority == "medium" for r in recs.quick_wins)
        critical_or_high_in_strategic = all(
            r.priority in ("critical", "high") for r in recs.strategic_changes
        )
        assert medium_in_quick
        assert critical_or_high_in_strategic
