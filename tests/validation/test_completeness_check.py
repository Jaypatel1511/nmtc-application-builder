"""Tests for completeness validation."""
import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.schema import ValidationResult
from nmtcapp.validation.completeness_check import check_completeness


def test_completeness_returns_validation_result(sample_application):
    result = check_completeness(sample_application)
    assert isinstance(result, ValidationResult)
    assert result.check_name == "completeness_check"


def test_completeness_full_application_passes(sample_application):
    result = check_completeness(sample_application)
    assert result.passed is True


def test_completeness_no_pipeline_fails(sample_cde):
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    result = check_completeness(app)
    assert result.passed is False
    assert any("pipeline" in i.lower() for i in result.issues)


def test_completeness_warns_on_undersized_pipeline(sample_cde):
    small_pipeline = Pipeline.sample(n=5)
    total_qei = sum(p.qei_request for p in small_pipeline)
    # Requested is much larger than pipeline
    app = Application(cde=sample_cde, requested_allocation=total_qei * 3)
    app.add_pipeline(small_pipeline)
    result = check_completeness(app)
    assert any("less than 90%" in w for w in result.warnings)


def test_completeness_warns_on_oversized_pipeline(sample_cde, sample_pipeline):
    total_qei = sum(p.qei_request for p in sample_pipeline)
    # Requested is much smaller than pipeline
    app = Application(cde=sample_cde, requested_allocation=total_qei * 0.3)
    app.add_pipeline(sample_pipeline)
    result = check_completeness(app)
    assert any("pipeline" in w.lower() for w in result.warnings)


def test_completeness_cde_missing_name_fails():
    cde = CDEProfile.sample()
    # Bypass validation to test completeness check directly
    cde.name = ""
    # CDEProfile.__post_init__ would catch this, so we patch after init
    # Use object.__setattr__ to bypass dataclass
    import dataclasses
    cde_bad = CDEProfile(
        name="Valid",
        cde_id="CDE-001",
        certification_date="2020-01-01",
        mission="Mission",
        target_markets=["IL"],
        prior_awards=[],
        contact={},
        governance={},
    )
    # Manually corrupt the name after creation for testing check logic
    object.__setattr__(cde_bad, "name", "")
    app = Application.__new__(Application)
    app.cde = cde_bad
    app.requested_allocation = 50_000_000
    app.application_round = "CY2025"
    app._pipeline = Pipeline.sample(n=5)
    app._analysis_cache = None
    result = check_completeness(app)
    assert result.passed is False


def test_completeness_project_missing_address_fails(sample_cde):
    project = PipelineProject(
        project_id="BAD-001", project_name="Bad Project",
        qalicb_name="Bad QALICB", address="",  # empty
        city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_500_000, qlici_amount=3_500_000,
        expected_jobs_created=10,
    )
    app = Application(cde=sample_cde, requested_allocation=5_000_000)
    app.add_project(project)
    result = check_completeness(app)
    assert result.passed is False
