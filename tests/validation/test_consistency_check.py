"""Tests for consistency validation."""
import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.schema import ValidationResult
from nmtcapp.validation.consistency_check import check_consistency


def _make_app_with_project(sample_cde, **project_overrides) -> Application:
    defaults = dict(
        project_id="CON-001", project_name="Test Project",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=10_000_000, qei_request=7_000_000, qlici_amount=7_000_000,
        expected_jobs_created=30, expected_jobs_retained=5,
        census_tract="17031010100", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    )
    defaults.update(project_overrides)
    project = PipelineProject(**defaults)
    app = Application(cde=sample_cde, requested_allocation=10_000_000)
    app.add_project(project)
    return app


def test_consistency_returns_validation_result(sample_application):
    result = check_consistency(sample_application)
    assert isinstance(result, ValidationResult)
    assert result.check_name == "consistency_check"


def test_consistency_valid_application_passes(sample_application):
    result = check_consistency(sample_application)
    assert result.passed is True


def test_consistency_qlici_exceeds_qei_fails(sample_cde):
    app = _make_app_with_project(
        sample_cde,
        qei_request=5_000_000,
        qlici_amount=6_000_000,  # exceeds QEI
    )
    result = check_consistency(app)
    assert result.passed is False
    assert any("QLICI" in i for i in result.issues)


def test_consistency_no_pipeline_warns(sample_cde):
    app = Application(cde=sample_cde, requested_allocation=10_000_000)
    result = check_consistency(app)
    assert result.passed is True  # no issues, just warning
    assert len(result.warnings) > 0


def test_consistency_zero_project_cost_fails(sample_cde):
    with pytest.raises(ValueError):
        # PipelineProject.__post_init__ catches this
        _make_app_with_project(sample_cde, total_project_cost=0)


def test_consistency_negative_jobs_fails(sample_cde):
    with pytest.raises(ValueError):
        _make_app_with_project(sample_cde, expected_jobs_created=-1)


def test_consistency_pipeline_qei_below_allocation_warns(sample_cde):
    project = PipelineProject(
        project_id="P1", project_name="Small Project",
        qalicb_name="QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_000_000, qlici_amount=3_000_000,
        expected_jobs_created=10,
        census_tract="17031010100", is_nmtc_eligible=True, distress_level="deep",
        is_native_area=False, is_high_migration_rural=False, is_opportunity_zone=False,
    )
    # Allocation much larger than pipeline
    app = Application(cde=sample_cde, requested_allocation=50_000_000)
    app.add_project(project)
    result = check_consistency(app)
    assert any("below" in w.lower() for w in result.warnings)


def test_consistency_date_order_warns(sample_cde):
    app = _make_app_with_project(
        sample_cde,
        construction_start="2026-06-01",
        operations_start="2025-01-01",  # before construction
    )
    result = check_consistency(app)
    assert any("operations_start" in w or "construction_start" in w for w in result.warnings)
