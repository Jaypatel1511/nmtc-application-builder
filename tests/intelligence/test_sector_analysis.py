"""Tests for sector mix analysis."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.sector_analysis import analyze_sector_mix


def _make_project(project_id: str, sector: str, qei: float) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"Project {project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector=sector, project_type="real_estate",
        total_project_cost=qei * 1.5, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=10, expected_jobs_retained=2,
        is_nmtc_eligible=True, distress_level="deep",
        census_tract="17031010100", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def test_analyze_sector_empty_pipeline():
    result = analyze_sector_mix(Pipeline())
    assert result["sectors_represented"] == 0
    assert result["dominant_sector"] is None


def test_sector_breakdown_counts():
    projects = [
        _make_project("P1", "healthcare", 3_000_000),
        _make_project("P2", "healthcare", 2_000_000),
        _make_project("P3", "education", 5_000_000),
    ]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["sector_breakdown"]["healthcare"]["count"] == 2
    assert result["sector_breakdown"]["education"]["count"] == 1


def test_sector_breakdown_dollars():
    projects = [
        _make_project("P1", "healthcare", 4_000_000),
        _make_project("P2", "education", 6_000_000),
    ]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["sector_breakdown"]["healthcare"]["qei_dollars"] == 4_000_000
    assert result["sector_breakdown"]["education"]["qei_dollars"] == 6_000_000


def test_dominant_sector():
    projects = [
        _make_project("P1", "healthcare", 8_000_000),
        _make_project("P2", "education", 3_000_000),
    ]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["dominant_sector"] == "healthcare"


def test_sector_diversity_score_single_sector():
    projects = [_make_project(f"P{i}", "healthcare", 1_000_000) for i in range(5)]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["sector_diversity_score"] == pytest.approx(0.0)


def test_sector_diversity_score_diverse():
    sectors = ["healthcare", "education", "small_business", "affordable_housing"]
    projects = [_make_project(f"P{i}", sectors[i], 2_500_000) for i in range(4)]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["sector_diversity_score"] > 90.0  # near-perfect even split


def test_pct_sums_to_one():
    projects = [
        _make_project("P1", "healthcare", 4_000_000),
        _make_project("P2", "education", 3_000_000),
        _make_project("P3", "small_business", 3_000_000),
    ]
    result = analyze_sector_mix(Pipeline(projects))
    total_pct = sum(v["pct"] for v in result["sector_breakdown"].values())
    assert total_pct == pytest.approx(1.0)


def test_high_priority_pct():
    projects = [
        _make_project("P1", "healthcare", 5_000_000),
        _make_project("P2", "affordable_housing", 3_000_000),
        _make_project("P3", "other", 2_000_000),
    ]
    result = analyze_sector_mix(Pipeline(projects))
    assert result["high_priority_pct"] == pytest.approx(0.80)
