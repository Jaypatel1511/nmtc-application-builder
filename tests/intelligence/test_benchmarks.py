"""Tests for intelligence/benchmarks.py."""
import pytest
from nmtcapp.intelligence.benchmarks import (
    BenchmarkComparison,
    HistoricalBenchmarks,
    MetricBenchmark,
    _normal_cdf,
)


class TestNormalCdf:
    def test_at_zero_is_half(self):
        assert abs(_normal_cdf(0.0) - 0.5) < 1e-10

    def test_large_positive_near_one(self):
        assert _normal_cdf(5.0) > 0.999

    def test_large_negative_near_zero(self):
        assert _normal_cdf(-5.0) < 0.001

    def test_symmetric(self):
        assert abs(_normal_cdf(1.0) + _normal_cdf(-1.0) - 1.0) < 1e-10


class TestHistoricalBenchmarks:
    def test_returns_benchmark_comparison(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        assert isinstance(bc, BenchmarkComparison)

    def test_metric_set_matches_the_weight_table(self, sample_pipeline_result):
        """Derived, not typed — it was ``== 9`` and 1.4.0 made it 8.

        A hand-typed count says nothing about WHICH metrics are present, and
        this package has six recorded instances of a hand-typed number going
        stale. The weight table is the list of metrics that count toward the
        overall score, so agreeing with it is the property worth holding.
        """
        from nmtcapp.data.benchmark_thresholds import BENCHMARK_METRIC_WEIGHTS

        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        assert {m.metric for m in bc.metrics} == set(BENCHMARK_METRIC_WEIGHTS)

    def test_the_rural_benchmark_stays_deleted(self, sample_pipeline_result):
        """1.4.0 premise ruling — no non-metro share is scored against a mean.

        The share itself survives as an unbenchmarked characterisation on the
        CLI and the Streamlit Geographic tab. What was removed is comparing it
        to a "winner mean" and folding the result into a score: the winner mean
        is one of the values data/historical_awards.py's own header records as
        unsourced, it is the exact complement of its sibling, and Question 22
        asks the Applicant to COMMIT to a percentage of QLICIs rather than to
        report a pipeline share. See renderers/_question_22.
        """
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        labels = " ".join(f"{m.metric} {m.label} {m.note}" for m in bc.metrics)
        assert "rural" not in labels.lower(), (
            f"a rural/non-metro benchmark is back in the metric set: {labels}"
        )

    def test_overall_score_in_range(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        assert 0.0 <= bc.overall_benchmark_score <= 100.0

    def test_tier_summary_has_all_tiers(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        for tier in ("strong", "competitive", "weak", "below_weak"):
            assert tier in bc.tier_summary

    def test_tier_summary_counts_sum_to_metric_count(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        total = sum(bc.tier_summary.values())
        assert total == len(bc.metrics)

    def test_methodology_disclosure_present(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        assert bc.methodology_disclosure
        assert len(bc.methodology_disclosure) > 50

    def test_methodology_mentions_winner(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        assert "winner" in bc.methodology_disclosure.lower()

    def test_all_metrics_have_valid_tiers(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        valid_tiers = {"strong", "competitive", "weak", "below_weak"}
        for m in bc.metrics:
            assert m.tier in valid_tiers

    def test_all_metric_scores_in_range(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        for m in bc.metrics:
            assert 0.0 <= m.score <= 100.0

    def test_percentiles_in_range(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        for m in bc.metrics:
            assert 0.0 <= m.percentile_vs_winners <= 1.0

    def test_thresholds_present_on_metrics(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        for m in bc.metrics:
            assert m.threshold_strong >= 0
            assert m.threshold_competitive >= 0

    def test_summary_is_string(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        s = bc.summary()
        assert isinstance(s, str)
        assert "BENCHMARK" in s.upper()

    def test_to_dict_serializable(self, sample_pipeline_result):
        import json
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        d = bc.to_dict()
        json.dumps(d)  # should not raise

    def test_to_dict_has_required_keys(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        d = bc.to_dict()
        assert "overall_benchmark_score" in d
        assert "tier_summary" in d
        assert "metrics" in d
        assert "methodology_disclosure" in d

    def test_higher_distress_metric_gets_better_tier(self):
        """Directly test that a high deep-distress value gets strong/competitive tier."""
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        strong_result = PipelineAnalysisResult(
            total_projects=15,
            total_qei_request=55_000_000,
            total_project_cost=80_000_000,
            eligibility_pct=0.97,
            distress_breakdown={"pct_deep_or_severe": 0.88, "pct_lic": 0.09,
                                 "pct_non_lic": 0.03, "pct_native_area": 0.08},
            geographic_diversity={"states_count": 10, "hhi": 450, "rural_pct": 0.22,
                                   "urban_pct": 0.78},
            sector_mix={"sectors_represented": 5, "dominant_sector": "healthcare",
                        "max_single_sector_pct": 0.28},
            aggregate_impact={"jobs_per_million_qei": 20.0, "total_jobs_created": 1100},
            deal_economics_summary={},
        )
        bc = HistoricalBenchmarks().compare(strong_result, 55_000_000)
        distress_metric = next(m for m in bc.metrics if m.metric == "min_deep_distress_pct")
        assert distress_metric.tier in ("strong", "competitive")

    def test_metric_benchmarks_have_notes(self, sample_pipeline_result):
        bc = HistoricalBenchmarks().compare(sample_pipeline_result, 55_000_000)
        for m in bc.metrics:
            assert m.note, f"Metric {m.metric} has empty note"
