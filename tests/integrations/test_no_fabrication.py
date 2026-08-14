"""Negative-path tests: the adapter must never fabricate eligibility data.

nmtc-mapper 0.3.4 raises typed errors instead of serving sample data. The
adapter must surface those failures as explicit unavailable/unverified
markers — never substitute hardcoded tracts or eligibility values.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from nmtcmapper import EligibilityDownloadError, NMTCMapperError

from nmtcapp.core.pipeline import Pipeline, PipelineProject

# The first tract of the old hardcoded fallback table — a fabricated
# deep-distress POSITIVE that must never appear in adapter output.
FABRICATED_TRACT = "17031838200"


def _unenriched_project(pid: str = "UN-001") -> PipelineProject:
    return PipelineProject(
        project_id=pid, project_name=f"Unenriched {pid}",
        qalicb_name="QALICB LLC", address="100 Main St", city="Springfield",
        state="IL", sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_500_000,
        qlici_amount=3_500_000, expected_jobs_created=10,
    )


def _unenriched_pipeline(n: int = 3) -> Pipeline:
    return Pipeline([_unenriched_project(f"UN-{i:03d}") for i in range(1, n + 1)])


def _assert_no_fabricated_values(pipeline: Pipeline) -> None:
    for p in pipeline:
        rendered = str(p.to_dict())
        assert FABRICATED_TRACT not in rendered, (
            f"fabricated fallback tract leaked into project {p.project_id}"
        )


# ---------------------------------------------------------------------------
# 1. Mapper construction failure → explicit degraded mode, no fallback
# ---------------------------------------------------------------------------

def test_mapper_failure_degrades_explicitly():
    from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

    pipeline = _unenriched_pipeline()
    with patch("nmtcmapper.NMTCMapper",
               side_effect=EligibilityDownloadError("CDFI Fund download failed")):
        result = enrich_pipeline_eligibility(pipeline)

    assert result.eligibility_data_status == "unavailable"
    assert "CDFI Fund download failed" in result.eligibility_data_error
    for p in result:
        assert p.census_tract is None
        assert p.is_nmtc_eligible is None
        assert p.distress_level is None
        assert p.is_native_area is None
        assert p.is_high_migration_rural is None
        assert p.is_opportunity_zone is None
    _assert_no_fabricated_values(result)


# ---------------------------------------------------------------------------
# 2. The hardcoded fallback table is gone
# ---------------------------------------------------------------------------

def test_no_fallback_table_exists():
    import nmtcapp.integrations.nmtc_mapper_adapter as adapter_mod

    with pytest.raises(AttributeError):
        getattr(adapter_mod, "_FALLBACK_ELIGIBILITY")


# ---------------------------------------------------------------------------
# 3. Per-project geocode failure → unverified, never a substitute tract
# ---------------------------------------------------------------------------

def _geocode_failed_result(address: str) -> SimpleNamespace:
    # Mirrors nmtc-mapper 0.3.4: geocode failure returns an
    # "ineligible"-shaped result with geocode_success=False.
    return SimpleNamespace(
        address=address, tract_id=None, geocode_success=False,
        nmtc_eligible=False, distress_level="ineligible",
        is_high_migration_rural=False,
        is_opportunity_zone=False,
    )


def test_geocode_failure_is_unverified():
    from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

    pipeline = _unenriched_pipeline(n=2)
    mock_mapper = MagicMock()
    mock_mapper.data_source = "cdfi_fund"
    mock_mapper.check_address.side_effect = [
        _geocode_failed_result("100 Main St, Springfield, IL"),
        NMTCMapperError("geocoder unavailable"),
    ]

    with patch("nmtcmapper.NMTCMapper", return_value=mock_mapper):
        result = enrich_pipeline_eligibility(pipeline)

    for p in result:
        assert p.geocode_success is False
        assert p.census_tract is None
        # UNVERIFIED, not ineligible: eligibility fields must stay None
        assert p.is_nmtc_eligible is None
        assert p.distress_level is None
        assert "unverified" in p.eligibility_status
        assert "unverified" in str(p.to_dict())
    _assert_no_fabricated_values(result)


# ---------------------------------------------------------------------------
# 4. Sample-data mapper is rejected (defense-in-depth provenance check)
# ---------------------------------------------------------------------------

def test_sample_data_source_rejected():
    from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

    pipeline = _unenriched_pipeline()
    sample_mapper = MagicMock()
    sample_mapper.data_source = "sample"

    with patch("nmtcmapper.NMTCMapper", return_value=sample_mapper):
        result = enrich_pipeline_eligibility(pipeline)

    assert result.eligibility_data_status == "unavailable"
    assert "sample" in result.eligibility_data_error
    sample_mapper.check_address.assert_not_called()
    for p in result:
        assert p.is_nmtc_eligible is None
        assert p.distress_level is None
        assert p.census_tract is None


# ---------------------------------------------------------------------------
# 5. Degraded mode: scores exclude the eligibility component, labeled partial
# ---------------------------------------------------------------------------

def test_degraded_score_labeled_partial():
    from nmtcapp import Application, CDEProfile

    app = Application(cde=CDEProfile.sample(), requested_allocation=55_000_000)
    app.add_pipeline(_unenriched_pipeline(n=5))

    with patch("nmtcmapper.NMTCMapper",
               side_effect=EligibilityDownloadError("CDFI Fund download failed")):
        analysis = app.analyze()

    # Analyzer surfaces the outage prominently, at the top of the summary
    pa_summary = analysis.pipeline_result.summary()
    banner_pos = pa_summary.lower().find("eligibility data unavailable")
    assert banner_pos != -1
    assert banner_pos < pa_summary.find("PIPELINE ANALYSIS SUMMARY")
    assert "CDFI Fund download failed" in pa_summary

    # Readiness score: eligibility components excluded, rendered as partial
    rs = analysis.readiness_score
    assert "eligibility_quality" not in rs.component_scores
    assert "distress_concentration" not in rs.component_scores
    rs_summary = rs.summary()
    assert "score computed without eligibility verification (4 of 6 components)" in rs_summary
    assert "eligibility data unavailable" in rs_summary.lower()

    # Win-alignment score: distress components excluded, labeled partial
    with patch("nmtcmapper.NMTCMapper",
               side_effect=EligibilityDownloadError("CDFI Fund download failed")):
        win = app.score_win_probability()
    win_summary = win.summary()
    assert "eligibility data unavailable" in win_summary.lower()
    assert "without eligibility verification" in win_summary
    assert win.community_outcomes["higher_distress_targeting"] is None
    assert win.community_outcomes["deep_distress_commitment"] is None


def test_degraded_composite_alignment_excludes_eligibility_component():
    from nmtcapp.optimizer.objectives import (
        composite_alignment_score,
        eligibility_components_available,
    )

    projects = list(_unenriched_pipeline(n=4))
    assert eligibility_components_available(projects) is False

    # Distress-alignment weight (0.35) must be excluded — an all-unverified
    # pipeline must score identically whatever the distress weight, because
    # the component simply is not computed.
    base = composite_alignment_score(projects, 55_000_000)
    heavy = composite_alignment_score(
        projects, 55_000_000,
        weights={"distress": 0.90, "geographic": 0.025, "impact": 0.025,
                 "sector": 0.025, "pipeline": 0.025},
    )
    light = composite_alignment_score(
        projects, 55_000_000,
        weights={"distress": 0.0, "geographic": 0.25, "impact": 0.25,
                 "sector": 0.25, "pipeline": 0.25},
    )
    assert heavy == pytest.approx(light)

    # Default weights with distress zeroed-out must match the default score:
    # the excluded component's weight is irrelevant.
    no_distress_default = composite_alignment_score(
        projects, 55_000_000,
        weights={"distress": 0.0, "geographic": 0.20, "impact": 0.25,
                 "sector": 0.15, "pipeline": 0.05},
    )
    assert base == pytest.approx(no_distress_default)


# ---------------------------------------------------------------------------
# 6. Unexpected (non-NMTCMapperError) exceptions propagate
# ---------------------------------------------------------------------------

def test_unexpected_exception_propagates():
    from nmtcapp.integrations.nmtc_mapper_adapter import enrich_pipeline_eligibility

    pipeline = _unenriched_pipeline()
    with patch("nmtcmapper.NMTCMapper", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            enrich_pipeline_eligibility(pipeline)


# ---------------------------------------------------------------------------
# 7. The HMDA adapter stays removed (1.1.6)
#
# It could not reach real HMDA data by any code path — the success branch
# called hmdaanalyzer.load_sample() (synthetic), and generate_disparity_report()
# returns a str in every published version, so the .get() raised and the
# module-level literals 0.28 / 2.1 became "application prose". It is gone; a
# silent reappearance must fail here rather than in a CDE's filing.
# ---------------------------------------------------------------------------

def test_hmda_adapter_module_is_gone():
    import importlib

    with pytest.raises(ImportError):
        importlib.import_module("nmtcapp.integrations.hmda_adapter")


def test_community_need_documentation_is_not_exported():
    import nmtcapp.integrations as integrations

    assert not hasattr(integrations, "community_need_documentation"), (
        "the HMDA community-need adapter is exported again — it published "
        "hardcoded disparity literals as application narrative"
    )
    assert "community_need_documentation" not in integrations.__all__


def test_hmda_analyzer_is_not_a_declared_dependency():
    """The dependency goes with the adapter, rather than having its floor raised."""
    import importlib.metadata as md

    requires = md.requires("nmtc-application-builder") or []
    names = [r.split(";")[0].strip().lower() for r in requires]
    assert not any(n.startswith("hmda-analyzer") for n in names), (
        f"hmda-analyzer is declared again: {names}"
    )
    assert not any(n.startswith("cra-scraper") for n in names), (
        f"cra-scraper is declared again (it has never had a single import): {names}"
    )
