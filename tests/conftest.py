"""Shared test fixtures."""
import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
from nmtcapp.data.schema import ValidationResult


@pytest.fixture
def sample_cde() -> CDEProfile:
    return CDEProfile.sample()


@pytest.fixture
def sample_pipeline() -> Pipeline:
    return Pipeline.sample(n=20)


@pytest.fixture
def small_pipeline() -> Pipeline:
    return Pipeline.sample(n=5)


@pytest.fixture
def sample_project() -> PipelineProject:
    return PipelineProject(
        project_id="TEST-001",
        project_name="Test Health Center",
        qalicb_name="Test HC QALICB LLC",
        address="100 Main St",
        city="Chicago",
        state="IL",
        sector="healthcare",
        project_type="real_estate",
        total_project_cost=10_000_000,
        qei_request=7_000_000,
        qlici_amount=7_000_000,
        expected_jobs_created=40,
        expected_jobs_retained=10,
        census_tract="17031010100",
        is_nmtc_eligible=True,
        distress_level="deep",
        is_native_area=False,
        is_high_migration_rural=False,
        is_opportunity_zone=False,
    )


@pytest.fixture
def sample_application(sample_cde, sample_pipeline) -> Application:
    app = Application(cde=sample_cde, requested_allocation=65_000_000)
    app.add_pipeline(sample_pipeline)
    return app


@pytest.fixture
def passing_validation() -> ValidationResult:
    return ValidationResult(check_name="test_check", passed=True, issues=[], warnings=[])


@pytest.fixture
def failing_validation() -> ValidationResult:
    return ValidationResult(
        check_name="test_check",
        passed=False,
        issues=["Something is wrong"],
        warnings=["Also a warning"],
    )


@pytest.fixture
def sample_pipeline_result(sample_pipeline) -> PipelineAnalysisResult:
    from nmtcapp.intelligence.distress_analysis import analyze_distress_concentration
    from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity
    from nmtcapp.intelligence.sector_analysis import analyze_sector_mix
    from nmtcapp.intelligence.impact_aggregator import aggregate_impact

    return PipelineAnalysisResult(
        total_projects=len(sample_pipeline),
        total_qei_request=sum(p.qei_request for p in sample_pipeline),
        total_project_cost=sum(p.total_project_cost for p in sample_pipeline),
        eligibility_pct=1.0,
        distress_breakdown=analyze_distress_concentration(sample_pipeline),
        geographic_diversity=analyze_geographic_diversity(sample_pipeline),
        sector_mix=analyze_sector_mix(sample_pipeline),
        aggregate_impact=aggregate_impact(sample_pipeline),
        deal_economics_summary={
            "total_qei": 130_000_000,
            "total_nmtcs": 50_700_000,
            "total_investor_equity": 42_081_000,
            "total_leverage_loans": 104_000_000,
            "total_cde_fees": 3_250_000,
            "total_net_subsidy": 126_750_000,
            "project_count": 20,
            "avg_leverage_ratio": 0.80,
        },
    )
