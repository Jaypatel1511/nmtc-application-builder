"""Tests for eligibility validation."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.schema import ValidationResult
from nmtcapp.validation.eligibility_check import check_eligibility


def _make_project(project_id: str, eligible: bool, distress: str,
                   qei: float = 5_000_000) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"P{project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=qei * 1.5, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=10, expected_jobs_retained=2,
        is_nmtc_eligible=eligible, distress_level=distress,
        census_tract="17031010100", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def test_check_eligibility_returns_validation_result(sample_pipeline):
    result = check_eligibility(sample_pipeline)
    assert isinstance(result, ValidationResult)
    assert result.check_name == "eligibility_check"


def test_check_eligibility_all_eligible():
    projects = [_make_project(f"P{i}", True, "deep") for i in range(5)]
    result = check_eligibility(Pipeline(projects))
    assert result.passed is True
    assert len(result.issues) == 0


def test_check_eligibility_some_ineligible():
    projects = [
        _make_project("P1", True, "deep"),
        _make_project("P2", False, "ineligible"),
    ]
    result = check_eligibility(Pipeline(projects))
    assert result.passed is False
    assert any("P2" in issue for issue in result.issues)


def test_check_eligibility_empty_pipeline():
    result = check_eligibility(Pipeline())
    assert result.passed is False
    assert len(result.issues) > 0


def test_check_eligibility_not_enriched():
    project = PipelineProject(
        project_id="P_UNENRICHED", project_name="Unenriched",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_500_000, qlici_amount=3_500_000,
        expected_jobs_created=10,
    )
    result = check_eligibility(Pipeline([project]))
    assert len(result.warnings) > 0


def test_check_eligibility_low_deep_distress_warns():
    projects = [_make_project(f"P{i}", True, "lic") for i in range(10)]
    result = check_eligibility(Pipeline(projects))
    assert any("distress" in w.lower() for w in result.warnings)


def test_check_eligibility_sample_pipeline_passes(sample_pipeline):
    result = check_eligibility(sample_pipeline)
    # Sample pipeline is all eligible
    assert result.passed is True
