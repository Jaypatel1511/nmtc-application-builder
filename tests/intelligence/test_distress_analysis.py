"""Tests for distress concentration analysis."""
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.intelligence.distress_analysis import analyze_distress_concentration


def _make_project(project_id: str, qei: float, distress: str,
                   native: bool = False, hmr: bool = False) -> PipelineProject:
    return PipelineProject(
        project_id=project_id, project_name=f"Project {project_id}",
        qalicb_name="Test QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=qei * 1.5, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=10, expected_jobs_retained=2,
        is_nmtc_eligible=distress != "ineligible", distress_level=distress,
        is_native_area=native, is_high_migration_rural=hmr,
        census_tract="17031010100", is_opportunity_zone=False,
    )


def test_analyze_distress_empty_pipeline():
    result = analyze_distress_concentration(Pipeline())
    assert result["pct_deep_or_severe"] == 0.0
    assert result["total_qei"] == 0.0
    assert result["meets_min_threshold"] is False


def test_analyze_distress_all_deep():
    projects = [_make_project(f"P{i}", 1_000_000, "deep") for i in range(5)]
    pipeline = Pipeline(projects)
    result = analyze_distress_concentration(pipeline)
    assert result["pct_deep"] == pytest.approx(1.0)
    assert result["pct_deep_or_severe"] == pytest.approx(1.0)
    assert result["meets_target_threshold"] is True


def test_analyze_distress_mixed():
    projects = [
        _make_project("P1", 4_000_000, "deep"),
        _make_project("P2", 2_000_000, "severe"),
        _make_project("P3", 2_000_000, "lic"),
        _make_project("P4", 2_000_000, "ineligible"),
    ]
    pipeline = Pipeline(projects)
    result = analyze_distress_concentration(pipeline)
    assert result["pct_deep"] == pytest.approx(0.40)
    assert result["pct_severe"] == pytest.approx(0.20)
    assert result["pct_deep_or_severe"] == pytest.approx(0.60)
    assert result["pct_lic"] == pytest.approx(0.20)


def test_pct_deep_distress_calculation():
    projects = [
        _make_project("P1", 7_500_000, "deep"),
        _make_project("P2", 2_500_000, "lic"),
    ]
    result = analyze_distress_concentration(Pipeline(projects))
    assert result["pct_deep"] == pytest.approx(0.75)


def test_dollars_in_each_category():
    projects = [
        _make_project("P1", 5_000_000, "deep"),
        _make_project("P2", 3_000_000, "lic"),
    ]
    result = analyze_distress_concentration(Pipeline(projects))
    assert result["dollars_by_distress"]["deep"] == 5_000_000
    assert result["dollars_by_distress"]["lic"] == 3_000_000


def test_native_area_pct():
    projects = [
        _make_project("P1", 4_000_000, "deep", native=True),
        _make_project("P2", 6_000_000, "deep", native=False),
    ]
    result = analyze_distress_concentration(Pipeline(projects))
    assert result["pct_native_area"] == pytest.approx(0.40)


def test_vs_historical_winners_strong():
    projects = [_make_project(f"P{i}", 1_000_000, "deep") for i in range(9)]
    projects.append(_make_project("P9", 1_000_000, "lic"))
    result = analyze_distress_concentration(Pipeline(projects))
    assert result["vs_historical_winners"] in ("top_quartile", "competitive")


def test_vs_historical_winners_weak():
    projects = [_make_project(f"P{i}", 1_000_000, "ineligible") for i in range(5)]
    result = analyze_distress_concentration(Pipeline(projects))
    assert result["vs_historical_winners"] == "uncompetitive"
