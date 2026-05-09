"""Tests for geographic diversity analysis."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.geographic_analysis import analyze_geographic_diversity


def _make_project(project_id: str, state: str, qei: float) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"Project {project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state=state,
        sector="healthcare", project_type="real_estate",
        total_project_cost=qei * 1.5, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=10, expected_jobs_retained=2,
        is_nmtc_eligible=True, distress_level="deep",
        census_tract="17031010100", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def test_analyze_geographic_empty_pipeline():
    result = analyze_geographic_diversity(Pipeline())
    assert result["states_count"] == 0
    assert result["meets_diversity_minimum"] is False


def test_states_count():
    projects = [
        _make_project("P1", "IL", 5_000_000),
        _make_project("P2", "OH", 5_000_000),
        _make_project("P3", "TX", 5_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["states_count"] == 3


def test_single_state_pipeline():
    projects = [_make_project(f"P{i}", "IL", 1_000_000) for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["states_count"] == 1
    assert result["meets_diversity_minimum"] is False
    assert result["geographic_concentration_label"] == "highly_concentrated"


def test_diverse_pipeline_meets_minimum():
    projects = [
        _make_project("P1", "IL", 2_000_000),
        _make_project("P2", "TX", 2_000_000),
        _make_project("P3", "NY", 2_000_000),
        _make_project("P4", "GA", 2_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["meets_diversity_minimum"] is True


def test_hhi_single_state():
    projects = [_make_project(f"P{i}", "IL", 1_000_000) for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["hhi"] == pytest.approx(10_000, abs=1)


def test_hhi_diverse_states():
    projects = [_make_project(f"P{i}", ["IL", "TX", "NY", "GA", "FL"][i], 1_000_000)
                for i in range(5)]
    result = analyze_geographic_diversity(Pipeline(projects))
    assert result["hhi"] < 5_000


def test_state_breakdown_table():
    projects = [
        _make_project("P1", "IL", 6_000_000),
        _make_project("P2", "TX", 4_000_000),
    ]
    result = analyze_geographic_diversity(Pipeline(projects))
    breakdown = result["state_breakdown"]
    assert "IL" in breakdown
    assert breakdown["IL"]["qei_dollars"] == 6_000_000
    assert breakdown["IL"]["project_count"] == 1
    assert breakdown["TX"]["pct_of_total_qei"] == pytest.approx(0.40)


def test_sample_pipeline_diversity(sample_pipeline):
    result = analyze_geographic_diversity(sample_pipeline)
    assert result["states_count"] >= 10
    assert result["meets_diversity_minimum"] is True
