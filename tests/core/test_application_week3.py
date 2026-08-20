"""Tests for Week 3 methods on Application: score_win_probability, benchmark,
recommendations, optimize_pipeline."""
import pytest
from nmtcapp.core.application import Application
from nmtcapp.intelligence.benchmarks import BenchmarkComparison
from nmtcapp.intelligence.recommendations import RecommendationSet
from nmtcapp.intelligence.win_probability import WinProbabilityScore
from nmtcapp.optimizer.pipeline_optimizer import OptimizationResult


class TestApplicationScoreWinProbability:
    def test_returns_win_probability_score(self, sample_application):
        score = sample_application.score_win_probability()
        assert isinstance(score, WinProbabilityScore)

    def test_composite_score_in_range(self, sample_application):
        score = sample_application.score_win_probability()
        assert 0.0 <= score.composite_score <= 100.0

    def test_methodology_disclosure_present(self, sample_application):
        score = sample_application.score_win_probability()
        assert score.methodology_disclosure
        assert "alignment" in score.methodology_disclosure.lower()

    def test_methodology_not_win_probability(self, sample_application):
        """CRITICAL: must never claim this is a win probability."""
        score = sample_application.score_win_probability()
        disclosure = score.methodology_disclosure.lower()
        assert "not" in disclosure or "cannot" in disclosure or "alignment" in disclosure

    def test_has_three_dimensions(self, sample_application):
        score = sample_application.score_win_probability()
        assert len(score.dimensional_scores) == 3
        expected_keys = {"business_strategy", "community_outcomes", "priority_points"}
        assert set(score.dimensional_scores.keys()) == expected_keys

    def test_competitive_tier_is_valid(self, sample_application):
        score = sample_application.score_win_probability()
        assert score.competitive_tier in ("strong", "competitive", "marginal", "weak", "not_rated")

    def test_no_pipeline_raises(self):
        from nmtcapp.core.cde import CDEProfile
        cde = CDEProfile.sample()
        app = Application(cde=cde, requested_allocation=55_000_000)
        with pytest.raises(ValueError):
            app.score_win_probability()


class TestApplicationBenchmark:
    def test_returns_benchmark_comparison(self, sample_application):
        bc = sample_application.benchmark()
        assert isinstance(bc, BenchmarkComparison)

    def test_overall_score_in_range(self, sample_application):
        bc = sample_application.benchmark()
        assert 0.0 <= bc.overall_benchmark_score <= 100.0

    def test_methodology_disclosure_present(self, sample_application):
        bc = sample_application.benchmark()
        assert bc.methodology_disclosure
        assert "winner" in bc.methodology_disclosure.lower()

    def test_eight_metrics(self, sample_application):
        """Eight, not nine — the rural benchmark was deleted in 1.4.0.

        The count is DERIVED from the weight table rather than typed, which is
        the whole reason this assertion is worth keeping: a metric added
        without a weight scores at 0.0 and drags the overall benchmark down
        silently, and a weight left behind by a deleted metric is a row nobody
        removed. Comparing the two catches both directions.
        """
        from nmtcapp.data.benchmark_thresholds import BENCHMARK_METRIC_WEIGHTS

        bc = sample_application.benchmark()
        assert len(bc.metrics) == len(BENCHMARK_METRIC_WEIGHTS), (
            f"{len(bc.metrics)} benchmark metrics against "
            f"{len(BENCHMARK_METRIC_WEIGHTS)} weights. "
            f"metrics: {sorted(m.metric for m in bc.metrics)}; "
            f"weights: {sorted(BENCHMARK_METRIC_WEIGHTS)}"
        )
        assert {m.metric for m in bc.metrics} == set(BENCHMARK_METRIC_WEIGHTS)
        assert "min_rural_pct" not in {m.metric for m in bc.metrics}, (
            "the rural benchmark is back. It scored a QEI share computed from "
            "a twelve-state list against an unsourced 'winner mean' that is "
            "the exact complement of its own sibling, for a question the Fund "
            "does not score in Phase I. See intelligence/benchmarks."
        )

    def test_no_pipeline_raises(self):
        from nmtcapp.core.cde import CDEProfile
        cde = CDEProfile.sample()
        app = Application(cde=cde, requested_allocation=55_000_000)
        with pytest.raises(ValueError):
            app.benchmark()


class TestApplicationRecommendations:
    def test_returns_recommendation_set(self, sample_application):
        recs = sample_application.recommendations()
        assert isinstance(recs, RecommendationSet)

    def test_has_recommendations(self, sample_application):
        recs = sample_application.recommendations()
        assert len(recs.recommendations) >= 1

    def test_overall_assessment_is_string(self, sample_application):
        recs = sample_application.recommendations()
        assert isinstance(recs.overall_assessment, str)
        assert len(recs.overall_assessment) > 10

    def test_all_actions_are_specific(self, sample_application):
        recs = sample_application.recommendations()
        for r in recs.recommendations:
            assert len(r.action) >= 20, f"Action too short: {r.action}"

    def test_all_improvements_quantified(self, sample_application):
        recs = sample_application.recommendations()
        for r in recs.recommendations:
            assert any(c.isdigit() for c in r.quantified_improvement), (
                f"Non-quantified improvement: {r.quantified_improvement}"
            )

    def test_no_pipeline_raises(self):
        from nmtcapp.core.cde import CDEProfile
        cde = CDEProfile.sample()
        app = Application(cde=cde, requested_allocation=55_000_000)
        with pytest.raises(ValueError):
            app.recommendations()


class TestApplicationOptimizePipeline:
    def test_returns_optimization_result(self, sample_application):
        result = sample_application.optimize_pipeline()
        assert isinstance(result, OptimizationResult)

    def test_selected_projects_not_empty(self, sample_application):
        result = sample_application.optimize_pipeline()
        assert len(result.selected_projects) >= 1

    def test_methodology_note_present(self, sample_application):
        result = sample_application.optimize_pipeline()
        assert result.methodology_note
        assert len(result.methodology_note) > 50

    def test_with_custom_constraints(self, sample_application):
        from nmtcapp.optimizer.constraints import OptimizationConstraints
        c = OptimizationConstraints(max_projects=5)
        result = sample_application.optimize_pipeline(constraints=c)
        assert len(result.selected_projects) <= 5

    def test_infeasible_constraints_return_result(self, sample_application):
        from nmtcapp.optimizer.constraints import OptimizationConstraints
        c = OptimizationConstraints(required_sectors=["impossible_sector_xyz"])
        result = sample_application.optimize_pipeline(constraints=c)
        assert isinstance(result, OptimizationResult)

    def test_no_pipeline_raises(self):
        from nmtcapp.core.cde import CDEProfile
        cde = CDEProfile.sample()
        app = Application(cde=cde, requested_allocation=55_000_000)
        with pytest.raises(ValueError):
            app.optimize_pipeline()

    def test_dimensional_improvements_dict(self, sample_application):
        result = sample_application.optimize_pipeline()
        assert isinstance(result.dimensional_improvements, dict)

    def test_custom_max_iterations(self, sample_application):
        result = sample_application.optimize_pipeline(max_iterations=10)
        assert isinstance(result, OptimizationResult)
        assert result.iterations <= 10
