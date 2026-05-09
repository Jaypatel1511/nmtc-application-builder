"""Tests for Pipeline and PipelineProject."""
import os
import tempfile

import pandas as pd
import pytest

from nmtcapp.core.pipeline import Pipeline, PipelineProject


def _make_project(**overrides) -> PipelineProject:
    defaults = dict(
        project_id="PRJ-T01",
        project_name="Test Project",
        qalicb_name="Test QALICB LLC",
        address="100 Main St",
        city="Chicago",
        state="IL",
        sector="healthcare",
        project_type="real_estate",
        total_project_cost=5_000_000,
        qei_request=3_500_000,
        qlici_amount=3_500_000,
        expected_jobs_created=20,
        expected_jobs_retained=5,
    )
    defaults.update(overrides)
    return PipelineProject(**defaults)


# PipelineProject tests

def test_pipeline_project_creation():
    p = _make_project()
    assert p.project_id == "PRJ-T01"
    assert p.sector == "healthcare"
    assert p.qei_request == 3_500_000


def test_pipeline_project_optional_fields_default_none():
    p = _make_project()
    assert p.census_tract is None
    assert p.is_nmtc_eligible is None
    assert p.distress_level is None
    assert p.expected_units_built is None


def test_pipeline_project_negative_cost_raises():
    with pytest.raises(ValueError, match="total_project_cost"):
        _make_project(total_project_cost=-1)


def test_pipeline_project_negative_qei_raises():
    with pytest.raises(ValueError, match="qei_request"):
        _make_project(qei_request=0)


def test_pipeline_project_negative_jobs_raises():
    with pytest.raises(ValueError, match="expected_jobs_created"):
        _make_project(expected_jobs_created=-1)


def test_pipeline_project_full_address():
    p = _make_project(address="100 Main St", city="Chicago", state="IL")
    assert p.full_address == "100 Main St, Chicago, IL"


def test_pipeline_project_is_enriched_false_when_none():
    p = _make_project()
    assert p.is_enriched is False


def test_pipeline_project_is_enriched_true_when_set():
    p = _make_project()
    p.is_nmtc_eligible = True
    assert p.is_enriched is True


def test_pipeline_project_is_deep_distress():
    p = _make_project()
    p.distress_level = "deep"
    assert p.is_deep_distress is True
    p.distress_level = "severe"
    assert p.is_deep_distress is True
    p.distress_level = "lic"
    assert p.is_deep_distress is False


def test_pipeline_project_to_dict():
    p = _make_project()
    d = p.to_dict()
    assert isinstance(d, dict)
    assert d["project_id"] == "PRJ-T01"
    assert "qei_request" in d


# Pipeline tests

def test_pipeline_creation_empty():
    p = Pipeline()
    assert len(p) == 0


def test_pipeline_creation_with_projects():
    projects = [_make_project(project_id=f"PRJ-{i:03d}") for i in range(3)]
    p = Pipeline(projects)
    assert len(p) == 3


def test_pipeline_iter():
    projects = [_make_project(project_id=f"PRJ-{i:03d}") for i in range(3)]
    pipeline = Pipeline(projects)
    ids = [p.project_id for p in pipeline]
    assert len(ids) == 3


def test_pipeline_add():
    pipeline = Pipeline()
    pipeline.add(_make_project())
    assert len(pipeline) == 1


def test_pipeline_sample_returns_20():
    pipeline = Pipeline.sample(n=20)
    assert len(pipeline) == 20


def test_pipeline_sample_projects_have_required_fields():
    pipeline = Pipeline.sample(n=5)
    for p in pipeline:
        assert p.project_id
        assert p.project_name
        assert p.state
        assert p.qei_request > 0


def test_pipeline_sample_diverse_states():
    pipeline = Pipeline.sample(n=20)
    states = {p.state for p in pipeline}
    assert len(states) >= 3


def test_pipeline_sample_already_enriched():
    pipeline = Pipeline.sample(n=5)
    for p in pipeline:
        assert p.is_nmtc_eligible is not None
        assert p.distress_level is not None


def test_pipeline_to_dataframe():
    pipeline = Pipeline.sample(n=5)
    df = pipeline.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "project_id" in df.columns
    assert "qei_request" in df.columns


def test_pipeline_from_csv():
    data = {
        "project_id": ["CSV-001"],
        "project_name": ["CSV Project"],
        "qalicb_name": ["CSV QALICB LLC"],
        "address": ["100 Test St"],
        "city": ["Chicago"],
        "state": ["IL"],
        "sector": ["healthcare"],
        "project_type": ["real_estate"],
        "total_project_cost": [8_000_000],
        "qei_request": [6_000_000],
        "qlici_amount": [6_000_000],
        "expected_jobs_created": [30],
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        path = f.name
    try:
        pipeline = Pipeline.from_csv(path)
        assert len(pipeline) == 1
        projects = list(pipeline)
        assert projects[0].project_name == "CSV Project"
    finally:
        os.unlink(path)


def test_pipeline_from_csv_missing_column_raises():
    df = pd.DataFrame({"project_id": ["X"], "project_name": ["Y"]})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        path = f.name
    try:
        with pytest.raises(ValueError, match="missing required columns"):
            Pipeline.from_csv(path)
    finally:
        os.unlink(path)


def test_pipeline_from_csv_file_not_found():
    with pytest.raises(FileNotFoundError):
        Pipeline.from_csv("/nonexistent/pipeline.csv")
