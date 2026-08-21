"""Shared test fixtures."""
import os

import pytest

from nmtcapp.core.application import Application, ApplicationAnalysis
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
from nmtcapp.validation.readiness_score import compute_readiness_score
from nmtcapp.data.schema import ValidationResult


def templates_dir() -> str:
    """Absolute path to the packaged templates directory.

    Resolved from the INSTALLED nmtcapp package, not from the repo root.
    Templates moved into nmtcapp/templates/ in 1.2.0 so the wheel would
    carry them; resolving them as package data is also what lets the sdist
    test job run against the tarball, whose test directory deliberately
    contains no ``nmtcapp/`` tree to shadow the installed package.
    """
    import nmtcapp
    return os.path.join(os.path.dirname(nmtcapp.__file__), "templates")


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
def application_analysis(sample_cde, sample_pipeline, sample_pipeline_result) -> ApplicationAnalysis:
    from datetime import datetime
    from nmtcapp.data.schema import ValidationResult
    val = ValidationResult(check_name="eligibility", passed=True, issues=[], warnings=[])
    readiness = compute_readiness_score(sample_pipeline_result, [val, val, val])
    return ApplicationAnalysis(
        cde_name=sample_cde.name,
        requested_allocation=65_000_000,
        application_round="CY2025",
        pipeline_result=sample_pipeline_result,
        distress_analysis=sample_pipeline_result.distress_breakdown,
        geographic_analysis=sample_pipeline_result.geographic_diversity,
        sector_analysis=sample_pipeline_result.sector_mix,
        impact_summary=sample_pipeline_result.aggregate_impact,
        deal_economics=sample_pipeline_result.deal_economics_summary,
        validation_results=[val, val, val],
        readiness_score=readiness,
        analyzed_at=datetime.now().isoformat(),
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


# ---------------------------------------------------------------------------
# The `network` marker: OFF unless asked for, whatever else -m says.
#
# WHY A HOOK AND NOT `addopts = "-m 'not network'"`. A command-line -m REPLACES
# addopts' -m rather than combining with it, and both CI jobs pass their own
# (`-m "not wheel"`). So an addopts-based default would be silently cancelled
# by the exact invocations that matter -- a gate disabled by the thing that was
# supposed to configure it, which is this suite's recurring shape.
#
# This hook reads the marker expression that was actually used and skips
# network tests unless it mentions `network` affirmatively. Composes with
# `-m "not wheel"`, and with no -m at all.
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(config, items):
    expression = config.getoption("-m", default="") or ""
    requested = "network" in expression and "not network" not in expression
    if requested:
        return
    skip = pytest.mark.skip(
        reason="reaches the public internet; run with `-m network` to enable. "
               "Skipped by default so CI never depends on a federal website "
               "being reachable."
    )
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
