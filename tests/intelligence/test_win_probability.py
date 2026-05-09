"""Tests for intelligence/win_probability.py."""
import pytest
from nmtcapp.intelligence.win_probability import WinProbabilityModel, WinProbabilityScore


class TestWinProbabilityModel:
    def test_returns_score_object(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert isinstance(score, WinProbabilityScore)

    def test_composite_score_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert 0.0 <= score.composite_score <= 100.0

    def test_methodology_disclosure_always_present(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.methodology_disclosure
        assert len(score.methodology_disclosure) > 50

    def test_methodology_not_called_probability(self, sample_pipeline_result):
        """Disclosure must clarify this is NOT a win probability."""
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        disclosure = score.methodology_disclosure.lower()
        # Must explicitly state the limitation
        assert "not" in disclosure or "cannot" in disclosure or "alignment" in disclosure

    def test_methodology_mentions_alignment(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert "alignment" in score.methodology_disclosure.lower()

    def test_five_dimensional_scores(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        expected_dims = {
            "distress_concentration", "geographic_diversity",
            "impact_intensity", "sector_diversity", "pipeline_quality"
        }
        assert expected_dims == set(score.dimensional_scores.keys())

    def test_all_dimensional_scores_in_range(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        for dim, val in score.dimensional_scores.items():
            assert 0.0 <= val <= 100.0, f"Dimension {dim} = {val} out of range"

    def test_valid_competitive_tier(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert score.competitive_tier in ("strong", "competitive", "marginal", "weak")

    def test_acceptance_rate_baseline_plausible(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert 0.25 <= score.acceptance_rate_baseline <= 0.45

    def test_peer_comparison_is_string(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        assert isinstance(score.peer_comparison, str)
        assert len(score.peer_comparison) > 10

    def test_summary_contains_score(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        s = score.summary()
        assert str(int(score.composite_score)) in s or f"{score.composite_score:.1f}" in s

    def test_summary_contains_methodology(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        s = score.summary()
        assert "METHODOLOGY" in s.upper() or "NOTE" in s.upper()

    def test_to_dict_serializable(self, sample_pipeline_result):
        import json
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        d = score.to_dict()
        json.dumps(d)

    def test_to_dict_has_required_keys(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000)
        d = score.to_dict()
        for key in ("composite_score", "dimensional_scores", "acceptance_rate_baseline",
                    "competitive_tier", "peer_comparison", "methodology_disclosure"):
            assert key in d

    def test_high_distress_pipeline_scores_higher(self):
        """A PipelineAnalysisResult with high deep distress should score higher."""
        from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

        def _make_result(deep_pct: float):
            return PipelineAnalysisResult(
                total_projects=12,
                total_qei_request=55_000_000,
                total_project_cost=80_000_000,
                eligibility_pct=0.95,
                distress_breakdown={"pct_deep_or_severe": deep_pct, "pct_lic": 1 - deep_pct,
                                     "pct_non_lic": 0.0, "pct_native_area": 0.0},
                geographic_diversity={"states_count": 8, "hhi": 600, "rural_pct": 0.15,
                                       "urban_pct": 0.85},
                sector_mix={"sectors_represented": 4, "dominant_sector": "healthcare",
                            "max_single_sector_pct": 0.30},
                aggregate_impact={"jobs_per_million_qei": 12.0, "total_jobs_created": 660},
                deal_economics_summary={},
            )

        high = _make_result(0.88)
        low = _make_result(0.20)
        score_high = WinProbabilityModel().score(high, 55_000_000)
        score_low = WinProbabilityModel().score(low, 55_000_000)
        assert score_high.dimensional_scores["distress_concentration"] > \
               score_low.dimensional_scores["distress_concentration"]

    def test_application_round_accepted(self, sample_pipeline_result):
        score = WinProbabilityModel().score(sample_pipeline_result, 55_000_000, "CY2026")
        assert isinstance(score, WinProbabilityScore)

    def test_tier_threshold_strong_at_75(self, sample_pipeline_result):
        model = WinProbabilityModel()
        assert model._classify_tier(75.0) == "strong"
        assert model._classify_tier(74.9) == "competitive"

    def test_tier_threshold_marginal_at_35(self, sample_pipeline_result):
        model = WinProbabilityModel()
        assert model._classify_tier(35.0) == "marginal"
        assert model._classify_tier(34.9) == "weak"
