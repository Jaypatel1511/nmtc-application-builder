"""Tests for integration adapters — all external calls are mocked."""
from unittest.mock import MagicMock, patch

import pytest

from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.integrations.cdfidata_adapter import cde_track_record
from nmtcapp.integrations.hmda_adapter import community_need_documentation
from nmtcapp.integrations.impact_adapter import build_impact_portfolio
from nmtcapp.integrations.nmtc_calc_adapter import compute_pipeline_economics
from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility


# ---------------------------------------------------------------------------
# nmtc_mapper_adapter
# ---------------------------------------------------------------------------

def test_enrich_already_enriched_pipeline_is_noop(sample_pipeline):
    """Pipeline.sample() is pre-enriched — adapter should skip API call."""
    original_tracts = [p.census_tract for p in sample_pipeline]
    enrich_pipeline_eligibility(sample_pipeline)
    new_tracts = [p.census_tract for p in sample_pipeline]
    assert original_tracts == new_tracts


def test_enrich_unenriched_pipeline_degrades_without_fabrication():
    """Unenriched pipeline stays unverified when nmtc-mapper raises.

    (v1.1.5: replaces the old fallback expectation — the adapter previously
    substituted hardcoded sample data here, which fabricated application
    content. See tests/integrations/test_no_fabrication.py.)
    """
    from nmtcmapper import NMTCMapperError

    project = PipelineProject(
        project_id="UN-001", project_name="Unenriched",
        qalicb_name="QALICB", address="100 Main", city="Chicago", state="IL",
        sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_500_000, qlici_amount=3_500_000,
        expected_jobs_created=10,
    )
    pipeline = Pipeline([project])

    with patch("nmtcmapper.NMTCMapper",
               side_effect=NMTCMapperError("network error")):
        result = enrich_pipeline_eligibility(pipeline)

    projects = list(result)
    assert result.eligibility_data_status == "unavailable"
    assert projects[0].is_nmtc_eligible is None
    assert projects[0].distress_level is None


def test_enrich_returns_pipeline_instance(sample_pipeline):
    result = enrich_pipeline_eligibility(sample_pipeline)
    assert isinstance(result, Pipeline)


# ---------------------------------------------------------------------------
# nmtc_calc_adapter
# ---------------------------------------------------------------------------

def test_compute_pipeline_economics_returns_dict(sample_pipeline):
    result = compute_pipeline_economics(sample_pipeline)
    assert isinstance(result, dict)


def test_compute_pipeline_economics_has_required_keys(sample_pipeline):
    result = compute_pipeline_economics(sample_pipeline)
    expected_keys = {
        "total_qei", "total_nmtcs", "total_investor_equity",
        "total_cde_fees", "total_net_subsidy", "project_count",
    }
    assert expected_keys.issubset(result.keys())


def test_compute_pipeline_economics_total_qei(sample_pipeline):
    result = compute_pipeline_economics(sample_pipeline)
    expected_qei = sum(p.qei_request for p in sample_pipeline)
    # Allow rounding tolerance
    assert abs(result["total_qei"] - expected_qei) < 1000


def test_compute_pipeline_economics_empty_pipeline():
    result = compute_pipeline_economics(Pipeline())
    assert result["total_qei"] == 0
    assert result["project_count"] == 0


def test_compute_pipeline_economics_net_subsidy_positive(sample_pipeline):
    result = compute_pipeline_economics(sample_pipeline)
    assert result["total_net_subsidy"] > 0


# ---------------------------------------------------------------------------
# hmda_adapter
# ---------------------------------------------------------------------------

def test_community_need_documentation_returns_dict(sample_pipeline):
    result = community_need_documentation(sample_pipeline)
    assert isinstance(result, dict)


def test_community_need_documentation_has_narrative(sample_pipeline):
    result = community_need_documentation(sample_pipeline)
    assert "narrative_summary" in result
    assert len(result["narrative_summary"]) > 50


# ---------------------------------------------------------------------------
# cdfidata_adapter
# ---------------------------------------------------------------------------

def test_cde_track_record_returns_dict(sample_cde):
    result = cde_track_record(sample_cde)
    assert isinstance(result, dict)


def test_cde_track_record_has_required_keys(sample_cde):
    result = cde_track_record(sample_cde)
    assert "total_prior_allocation" in result
    assert "track_record_label" in result
    assert "deployment_narrative" in result


def test_cde_track_record_strong_for_sample_cde(sample_cde):
    result = cde_track_record(sample_cde)
    # Sample CDE has $155MM prior allocation, 2 fully deployed
    assert result["track_record_label"] == "strong"


# ---------------------------------------------------------------------------
# impact_adapter
# ---------------------------------------------------------------------------

def test_build_impact_portfolio_returns_dict(sample_pipeline):
    result = build_impact_portfolio(sample_pipeline)
    assert isinstance(result, dict)


def test_build_impact_portfolio_has_size(sample_pipeline):
    result = build_impact_portfolio(sample_pipeline)
    assert result["portfolio_size"] == 20


def test_build_impact_portfolio_empty_pipeline():
    result = build_impact_portfolio(Pipeline())
    assert result["portfolio_size"] == 0
    assert result["total_deployed"] == 0.0
