"""Tests for intelligence/recommendations.py."""
import pytest
from nmtcapp.intelligence.recommendations import (
    Recommendation,
    RecommendationEngine,
    RecommendationSet,
)


class TestRecommendationEngine:
    def test_returns_recommendation_set(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs, RecommendationSet)

    def test_recommendations_is_list(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs.recommendations, list)

    def test_overall_assessment_is_string(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        assert isinstance(recs.overall_assessment, str)
        assert len(recs.overall_assessment) > 10

    def test_all_recommendations_have_required_fields(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        for r in recs.recommendations:
            assert r.category
            assert r.priority in ("critical", "high", "medium")
            assert r.finding
            assert r.action
            assert r.expected_impact
            assert r.quantified_improvement

    def test_recommendations_sorted_by_priority(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        priority_rank = {"critical": 0, "high": 1, "medium": 2}
        ranks = [priority_rank[r.priority] for r in recs.recommendations]
        assert ranks == sorted(ranks)

    def test_quantified_improvement_is_specific(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        for r in recs.recommendations:
            # Must contain either a % or a number — not just generic text
            text = r.quantified_improvement
            has_number = any(c.isdigit() for c in text)
            assert has_number, f"Non-quantified recommendation: {text}"

    def test_quick_wins_are_medium_priority(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        for r in recs.quick_wins:
            assert r.priority == "medium"

    def test_strategic_changes_are_critical_or_high(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        for r in recs.strategic_changes:
            assert r.priority in ("critical", "high")

    def test_summary_is_string(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        s = recs.summary()
        assert isinstance(s, str)
        assert len(s) > 100

    def test_to_dict_serializable(self, sample_pipeline_result):
        import json
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        d = recs.to_dict()
        json.dumps(d)

    def test_to_dict_has_required_keys(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
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

    def test_works_with_win_probability_score(self, sample_pipeline_result):
        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        win_score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, win_score)
        assert isinstance(recs, RecommendationSet)

    def test_full_pipeline_returns_recommendations(self, sample_pipeline_result):
        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        from nmtcapp.intelligence.win_probability import WinProbabilityModel
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        ws = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        recs = RecommendationEngine().recommend(sample_pipeline_result, bc, ws)
        assert len(recs.recommendations) >= 1

    def test_weak_pipeline_has_critical_recommendations(self):
        """A pipeline with very low distress should get critical recommendations."""
        from nmtcapp.core.pipeline import Pipeline, PipelineProject
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalyzer

        weak = Pipeline()
        p = PipelineProject(
            project_id="W-001",
            project_name="Weak Project",
            qalicb_name="Weak QALICB",
            address="1 Main St",
            city="Anytown",
            state="CA",
            sector="other",
            project_type="real_estate",
            total_project_cost=10_000_000,
            qei_request=6_000_000,
            qlici_amount=6_000_000,
            expected_jobs_created=3,
        )
        p.distress_level = "lic"
        p.is_nmtc_eligible = True
        weak.add(p)

        result = PipelineAnalyzer().analyze(weak)
        recs = RecommendationEngine().recommend(result, None, None)
        priorities = [r.priority for r in recs.recommendations]
        assert "critical" in priorities or "high" in priorities

    def test_assessment_changes_with_score_tier(self, sample_pipeline_result):
        from nmtcapp.intelligence.win_probability import WinProbabilityModel, WinProbabilityScore
        weak_score = WinProbabilityScore(
            composite_score=20.0,
            dimensional_scores={},
            acceptance_rate_baseline=0.34,
            competitive_tier="weak",
            peer_comparison="Weak.",
        )
        engine = RecommendationEngine()
        assessment = engine._overall_assessment(sample_pipeline_result, weak_score)
        assert "weak" in assessment.lower() or "significant" in assessment.lower() or "restructur" in assessment.lower()


class TestRecommendationDataclass:
    def test_recommendation_to_dict(self):
        r = Recommendation(
            category="distress",
            priority="critical",
            finding="Test finding",
            action="Test action",
            expected_impact="Test impact",
            quantified_improvement="+10 points",
        )
        d = r.to_dict()
        assert d["category"] == "distress"
        assert d["priority"] == "critical"
        assert d["quantified_improvement"] == "+10 points"

    def test_recommendation_set_categorizes_correctly(self, sample_pipeline_result):
        recs = RecommendationEngine().recommend(sample_pipeline_result, None, None)
        medium_in_quick = all(r.priority == "medium" for r in recs.quick_wins)
        critical_or_high_in_strategic = all(
            r.priority in ("critical", "high") for r in recs.strategic_changes
        )
        assert medium_in_quick
        assert critical_or_high_in_strategic
