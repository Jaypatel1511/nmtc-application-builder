"""M4: eligibility_data_status must default fail-closed.

Auditor probe: a pipeline whose enrichment never ran (or died mid-flight)
retained the constructor default "ok" and rendered as verified-complete.
The default must be "unenriched"; only the adapter's success path (or the
pre-verified sample fixture) may claim "ok".
"""
from unittest.mock import patch

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject


def _unenriched_project(pid: str) -> PipelineProject:
    return PipelineProject(
        project_id=pid, project_name=f"Unenriched {pid}",
        qalicb_name="QALICB LLC", address="100 Main St", city="Springfield",
        state="IL", sector="healthcare", project_type="real_estate",
        total_project_cost=5_000_000, qei_request=3_500_000,
        qlici_amount=3_500_000, expected_jobs_created=10,
    )


def test_pipeline_status_defaults_to_unenriched():
    p = Pipeline([_unenriched_project("UN-01")])
    assert p.eligibility_data_status == "unenriched"
    assert Pipeline().eligibility_data_status == "unenriched"


def test_sample_pipeline_is_ok():
    """The sample fixture ships pre-verified eligibility data for offline
    demos — it is the one construction path that may claim "ok" directly."""
    assert Pipeline.sample(n=20).eligibility_data_status == "ok"


def test_never_enriched_pipeline_renders_degraded_not_verified_complete():
    """Auditor probe: enrichment that silently never sets a status must
    surface as degraded downstream, not as a verified-complete pipeline."""
    app = Application(cde=CDEProfile.sample(), requested_allocation=55_000_000)
    app.add_pipeline(Pipeline([_unenriched_project(f"UN-{i}") for i in range(3)]))

    # Simulate a broken/legacy enrichment path that forgets to set a status
    with patch(
        "nmtcapp.intelligence.pipeline_analyzer.enrich_pipeline_eligibility",
        side_effect=lambda pipeline: pipeline,
    ):
        analysis = app.analyze()

    pr = analysis.pipeline_result
    assert pr.eligibility_data_status != "ok"
    assert "unverified" in pr.summary().lower() or "unavailable" in pr.summary().lower()
    assert analysis.readiness_score.partial is True
    assert "eligibility_quality" not in analysis.readiness_score.component_scores
