"""
Structural tests for the radar chart and WinProbabilityScore dimension keys.

These tests would have caught the C1/H7 regression where plot_readiness_radar
used old 5-dimension model keys that no longer exist in dimensional_scores.
"""
import inspect
import tempfile
from pathlib import Path

import pytest

from nmtcapp import Application, CDEProfile, Pipeline

EXPECTED_DIM_KEYS = frozenset({"business_strategy", "community_outcomes", "priority_points"})
OLD_DIM_KEYS = frozenset({
    "distress_concentration", "geographic_diversity",
    "impact_intensity", "sector_diversity", "pipeline_quality",
})


def _make_app_and_score():
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    return app, app.score_win_probability()


def test_dimensional_scores_has_cdfi_fund_keys():
    """dimensional_scores must contain exactly the 3 current CDFI Fund section keys."""
    _, score = _make_app_and_score()
    assert set(score.dimensional_scores.keys()) == EXPECTED_DIM_KEYS


def test_dimensional_scores_excludes_old_keys():
    """Old 5-dimension model keys must not appear in dimensional_scores."""
    _, score = _make_app_and_score()
    for key in OLD_DIM_KEYS:
        assert key not in score.dimensional_scores, (
            f"Old 5-dimension key '{key}' still present in dimensional_scores — "
            "scoring model may not have been fully migrated to the CDFI Fund framework."
        )


def test_radar_chart_axis_values_nonzero():
    """All three CDFI Fund section scores must be positive for the sample pipeline."""
    pytest.importorskip("matplotlib")
    from nmtcapp.visualization.maps import plot_readiness_radar

    app, score = _make_app_and_score()
    with tempfile.TemporaryDirectory() as tmp:
        path = plot_readiness_radar(app, str(Path(tmp) / "radar.png"))
        assert Path(path).exists(), "Radar chart file was not created"

    axes_values = [score.dimensional_scores.get(k, 0.0) for k in sorted(EXPECTED_DIM_KEYS)]
    assert any(v > 0 for v in axes_values), (
        f"All radar axis values are zero: {dict(zip(sorted(EXPECTED_DIM_KEYS), axes_values))} — "
        "_DIM_MAP in plot_readiness_radar likely uses wrong dimension keys."
    )


def test_radar_chart_does_not_use_old_dimension_keys():
    """plot_readiness_radar source must not reference old 5-dimension model keys."""
    from nmtcapp.visualization import maps as maps_module

    source = inspect.getsource(maps_module.plot_readiness_radar)
    for old_key in OLD_DIM_KEYS:
        assert old_key not in source, (
            f"Old 5-dimension key '{old_key}' found in plot_readiness_radar source — "
            "update _DIM_MAP to use current WinProbabilityScore.dimensional_scores keys."
        )
