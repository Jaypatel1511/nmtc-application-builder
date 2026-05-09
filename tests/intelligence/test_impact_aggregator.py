"""Tests for impact aggregation."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.impact_aggregator import aggregate_impact


def _make_project(project_id: str, qei: float, cost: float,
                   jobs_created: int, jobs_retained: int = 0,
                   units: int = None, sqft: float = None) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"P{project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=cost, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=jobs_created, expected_jobs_retained=jobs_retained,
        expected_units_built=units, expected_sq_ft=sqft,
        is_nmtc_eligible=True, distress_level="deep",
        census_tract="17031010100", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def test_aggregate_impact_empty_pipeline():
    result = aggregate_impact(Pipeline())
    assert result["total_jobs_created"] == 0
    assert result["total_qei"] == 0.0


def test_total_jobs_created():
    projects = [
        _make_project("P1", 5_000_000, 7_000_000, 30),
        _make_project("P2", 3_000_000, 4_000_000, 20),
    ]
    result = aggregate_impact(Pipeline(projects))
    assert result["total_jobs_created"] == 50


def test_total_jobs_retained():
    projects = [
        _make_project("P1", 5_000_000, 7_000_000, 30, jobs_retained=10),
        _make_project("P2", 3_000_000, 4_000_000, 20, jobs_retained=5),
    ]
    result = aggregate_impact(Pipeline(projects))
    assert result["total_jobs_retained"] == 15
    assert result["total_jobs"] == 65


def test_cost_per_job_calculation():
    projects = [_make_project("P1", 10_000_000, 20_000_000, 200)]
    result = aggregate_impact(Pipeline(projects))
    assert result["cost_per_job"] == 100_000


def test_jobs_per_million_qei():
    projects = [_make_project("P1", 10_000_000, 15_000_000, 120)]
    result = aggregate_impact(Pipeline(projects))
    assert result["jobs_per_million_qei"] == pytest.approx(12.0)


def test_units_and_sqft_aggregation():
    projects = [
        _make_project("P1", 5_000_000, 8_000_000, 10, units=40, sqft=10_000),
        _make_project("P2", 5_000_000, 8_000_000, 10, units=20, sqft=5_000),
    ]
    result = aggregate_impact(Pipeline(projects))
    assert result["total_units_built"] == 60
    assert result["total_sq_ft"] == 15_000


def test_vs_historical_benchmarks_above_average():
    # 20 jobs/$MM QEI = top quartile threshold
    projects = [_make_project("P1", 5_000_000, 8_000_000, 100)]
    result = aggregate_impact(Pipeline(projects))
    assert result["vs_historical_benchmarks"] == "top_quartile"
