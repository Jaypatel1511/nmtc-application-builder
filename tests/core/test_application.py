"""Tests for Application."""
import pytest

from nmtcapp.core.application import Application, ApplicationAnalysis
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject


def test_application_creation(sample_cde):
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    assert app.cde == sample_cde
    assert app.requested_allocation == 65_000_000
    assert app.application_round == "CY2025"


def test_application_custom_round(sample_cde):
    app = Application(cde=sample_cde, requested_allocation=50_000_000, application_round="CY2026")
    assert app.application_round == "CY2026"


def test_application_invalid_cde_raises():
    with pytest.raises(TypeError, match="CDEProfile"):
        Application(cde="not a cde", requested_allocation=50_000_000)


def test_application_zero_allocation_raises(sample_cde):
    with pytest.raises(ValueError, match="requested_allocation"):
        Application(cde=sample_cde, requested_allocation=0)


def test_application_add_pipeline(sample_cde, sample_pipeline):
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    app.add_pipeline(sample_pipeline)
    assert len(app.pipeline) == 20


def test_application_add_project(sample_cde, sample_project):
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    app.add_project(sample_project)
    assert len(app.pipeline) == 1


def test_application_analyze_without_pipeline_raises(sample_cde):
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    with pytest.raises(ValueError, match="no pipeline"):
        app.analyze()


def test_application_analyze_returns_analysis(sample_application):
    result = sample_application.analyze()
    assert isinstance(result, ApplicationAnalysis)


def test_application_analyze_has_readiness_score(sample_application):
    from nmtcapp.validation.readiness_score import ReadinessScore
    result = sample_application.analyze()
    assert isinstance(result.readiness_score, ReadinessScore)
    assert 0 <= result.readiness_score.overall_score <= 100


def test_application_analyze_has_pipeline_result(sample_application):
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
    result = sample_application.analyze()
    assert isinstance(result.pipeline_result, PipelineAnalysisResult)
    assert result.pipeline_result.total_projects == 20


def test_application_analyze_has_validation_results(sample_application):
    result = sample_application.analyze()
    assert len(result.validation_results) == 3
    check_names = {v.check_name for v in result.validation_results}
    assert "eligibility_check" in check_names
    assert "completeness_check" in check_names
    assert "consistency_check" in check_names


def test_application_analyze_result_to_dict(sample_application):
    result = sample_application.analyze()
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "cde_name" in d
    assert "readiness_score" in d
    assert "pipeline_result" in d


def test_application_analyze_caches_result(sample_application):
    result1 = sample_application.analyze()
    result2 = sample_application.analyze()
    assert result1 is result2  # same object — cached


def test_application_summary_runs_without_error(sample_application, capsys):
    sample_application.summary()
    captured = capsys.readouterr()
    assert "NMTC APPLICATION ANALYSIS" in captured.out


def test_application_to_dict(sample_application):
    d = sample_application.to_dict()
    assert isinstance(d, dict)
    assert d["cde_name"] == sample_application.cde.name
