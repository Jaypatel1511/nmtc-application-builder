"""Tests for PipelineAnalyzer orchestrator."""
import pytest

from nmtcapp.core.pipeline import Pipeline
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalyzer, PipelineAnalysisResult


def test_pipeline_analyzer_returns_result(sample_pipeline):
    analyzer = PipelineAnalyzer()
    result = analyzer.analyze(sample_pipeline)
    assert isinstance(result, PipelineAnalysisResult)


def test_pipeline_analysis_result_has_all_fields(sample_pipeline):
    result = PipelineAnalyzer().analyze(sample_pipeline)
    assert result.total_projects == 20
    assert result.total_qei_request > 0
    assert result.total_project_cost > 0
    assert 0.0 <= result.eligibility_pct <= 1.0
    assert isinstance(result.distress_breakdown, dict)
    assert isinstance(result.geographic_diversity, dict)
    assert isinstance(result.sector_mix, dict)
    assert isinstance(result.aggregate_impact, dict)
    assert isinstance(result.deal_economics_summary, dict)


def test_pipeline_analysis_total_qei(sample_pipeline):
    result = PipelineAnalyzer().analyze(sample_pipeline)
    expected_qei = sum(p.qei_request for p in sample_pipeline)
    assert result.total_qei_request == pytest.approx(expected_qei)


def test_pipeline_analysis_total_projects(sample_pipeline):
    result = PipelineAnalyzer().analyze(sample_pipeline)
    assert result.total_projects == len(sample_pipeline)


def test_pipeline_analysis_summary_method(sample_pipeline):
    result = PipelineAnalyzer().analyze(sample_pipeline)
    summary = result.summary()
    assert isinstance(summary, str)
    assert "PIPELINE ANALYSIS SUMMARY" in summary
    assert "Distress Concentration" in summary
    assert "Impact Projections" in summary


def test_pipeline_analyzer_empty_pipeline():
    result = PipelineAnalyzer().analyze(Pipeline())
    assert result.total_projects == 0
    assert result.total_qei_request == 0.0


def test_pipeline_analysis_to_dict(sample_pipeline):
    result = PipelineAnalyzer().analyze(sample_pipeline)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "total_projects" in d
    assert "distress_breakdown" in d
    assert "deal_economics_summary" in d
