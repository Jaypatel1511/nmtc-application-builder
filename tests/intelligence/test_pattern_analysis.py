"""Tests for intelligence/pattern_analysis.py."""
import pytest
from nmtcapp.intelligence.pattern_analysis import analyze_winning_patterns, compare_to_winners


class TestAnalyzeWinningPatterns:
    def test_returns_dict(self):
        patterns = analyze_winning_patterns()
        assert isinstance(patterns, dict)

    def test_has_required_top_level_keys(self):
        patterns = analyze_winning_patterns()
        for key in ("distress", "geographic", "sector", "impact", "acceptance_rate"):
            assert key in patterns

    def test_acceptance_rate_plausible(self):
        patterns = analyze_winning_patterns()
        assert 0.25 <= patterns["acceptance_rate"] <= 0.45

    def test_distress_percentile_ordering(self):
        d = analyze_winning_patterns()["distress"]
        assert d["p25_pct_deep_or_severe"] <= d["p50_pct_deep_or_severe"]
        assert d["p50_pct_deep_or_severe"] <= d["p75_pct_deep_or_severe"]

    def test_geographic_has_state_percentiles(self):
        g = analyze_winning_patterns()["geographic"]
        for key in ("p25_states", "p50_states", "p75_states", "mean_states"):
            assert key in g

    def test_sector_has_all_major_sectors(self):
        s = analyze_winning_patterns()["sector"]
        for sector in ("healthcare", "affordable_housing", "small_business",
                       "education", "community_facility"):
            assert sector in s

    def test_sector_shares_positive(self):
        s = analyze_winning_patterns()["sector"]
        for key in ("healthcare", "small_business", "education"):
            assert s[key] > 0

    def test_impact_has_percentiles(self):
        i = analyze_winning_patterns()["impact"]
        for key in ("p25_jobs_per_mm_qei", "p50_jobs_per_mm_qei", "p75_jobs_per_mm_qei"):
            assert key in i

    def test_impact_percentiles_ordered(self):
        i = analyze_winning_patterns()["impact"]
        assert i["p25_jobs_per_mm_qei"] <= i["p50_jobs_per_mm_qei"] <= i["p75_jobs_per_mm_qei"]

    def test_geographic_has_hhi(self):
        g = analyze_winning_patterns()["geographic"]
        assert "mean_hhi" in g
        assert g["mean_hhi"] > 0


class TestCompareToWinners:
    def test_returns_dict(self, sample_pipeline_result):
        comparison = compare_to_winners(sample_pipeline_result)
        assert isinstance(comparison, dict)

    def test_has_four_dimensions(self, sample_pipeline_result):
        comparison = compare_to_winners(sample_pipeline_result)
        for dim in ("distress", "geographic", "impact", "sector"):
            assert dim in comparison

    def test_distress_gap_is_numeric(self, sample_pipeline_result):
        comparison = compare_to_winners(sample_pipeline_result)
        assert isinstance(comparison["distress"]["gap_to_winner_median"], float)

    def test_gap_label_valid(self, sample_pipeline_result):
        comparison = compare_to_winners(sample_pipeline_result)
        valid_labels = {
            "above_winner_p75",
            "between_winner_p50_and_p75",
            "between_winner_p25_and_p50",
            "below_winner_p25",
        }
        for dim in ("distress", "geographic", "impact"):
            assert comparison[dim]["gap_label"] in valid_labels

    def test_distress_has_winner_percentiles(self, sample_pipeline_result):
        d = compare_to_winners(sample_pipeline_result)["distress"]
        for key in ("winner_p25", "winner_p50", "winner_p75", "winner_mean"):
            assert key in d

    def test_geographic_has_states_gap(self, sample_pipeline_result):
        g = compare_to_winners(sample_pipeline_result)["geographic"]
        assert "gap_to_winner_median_states" in g
        assert isinstance(g["gap_to_winner_median_states"], int)

    def test_sector_has_above_ceiling_flag(self, sample_pipeline_result):
        s = compare_to_winners(sample_pipeline_result)["sector"]
        assert "above_ceiling" in s
        assert isinstance(s["above_ceiling"], bool)

    def test_impact_has_winner_benchmarks(self, sample_pipeline_result):
        i = compare_to_winners(sample_pipeline_result)["impact"]
        for key in ("winner_p25", "winner_p50", "winner_p75"):
            assert key in i

    def test_high_distress_result_above_p25(self):
        """A PipelineAnalysisResult with high deep distress should be above p25."""
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
        result = PipelineAnalysisResult(
            total_projects=10,
            total_qei_request=40_000_000,
            total_project_cost=55_000_000,
            eligibility_pct=0.97,
            distress_breakdown={"pct_deep_or_severe": 0.90, "pct_lic": 0.07,
                                 "pct_non_lic": 0.03, "pct_native_area": 0.05},
            geographic_diversity={"states_count": 8, "hhi": 500, "rural_pct": 0.18,
                                   "urban_pct": 0.82},
            sector_mix={"sectors_represented": 4, "dominant_sector": "healthcare",
                        "max_single_sector_pct": 0.30},
            aggregate_impact={"jobs_per_million_qei": 14.0, "total_jobs_created": 560},
            deal_economics_summary={},
        )
        comparison = compare_to_winners(result)
        label = comparison["distress"]["gap_label"]
        assert label in ("above_winner_p75", "between_winner_p50_and_p75",
                         "between_winner_p25_and_p50")

    def test_serializable_to_json(self, sample_pipeline_result):
        import json
        comparison = compare_to_winners(sample_pipeline_result)
        json.dumps(comparison)  # should not raise
