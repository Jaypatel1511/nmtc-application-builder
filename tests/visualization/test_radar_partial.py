"""H3 (surface): the readiness radar must label partial-mode renders."""
import os
from unittest.mock import patch

import pytest

pytest.importorskip("matplotlib")

from nmtcmapper import EligibilityDownloadError

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject


def _unenriched_pipeline() -> Pipeline:
    return Pipeline([
        PipelineProject(
            project_id=f"UN-{i:02d}", project_name=f"Unenriched {i}",
            qalicb_name="QALICB LLC", address="100 Main St", city="Springfield",
            state="IL", sector="healthcare", project_type="real_estate",
            total_project_cost=5_000_000, qei_request=3_500_000,
            qlici_amount=3_500_000, expected_jobs_created=10,
        )
        for i in range(1, 4)
    ])


def test_radar_labels_carry_partial_marker():
    from nmtcapp.visualization.maps import _radar_labels

    class _FakeScore:
        composite_score = 32.0
        tier = "Not Rated — eligibility data unavailable"
        partial = True

    title, series_label = _radar_labels(_FakeScore())
    assert "PARTIAL" in title
    assert "PARTIAL" in series_label

    class _FakeFullScore:
        composite_score = 88.0
        tier = "Top Tier"
        partial = False

    title, series_label = _radar_labels(_FakeFullScore())
    assert "PARTIAL" not in title
    assert "PARTIAL" not in series_label


def test_degraded_radar_renders_with_partial_label(tmp_path):
    from nmtcapp.visualization.maps import plot_readiness_radar

    app = Application(cde=CDEProfile.sample(), requested_allocation=55_000_000)
    app.add_pipeline(_unenriched_pipeline())
    out = str(tmp_path / "radar_partial.png")
    with patch("nmtcmapper.NMTCMapper",
               side_effect=EligibilityDownloadError("CDFI Fund download failed")):
        path = plot_readiness_radar(app, out)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    # The score that fed the radar must have been partial
    with patch("nmtcmapper.NMTCMapper",
               side_effect=EligibilityDownloadError("CDFI Fund download failed")):
        assert app.score_win_probability().partial is True
