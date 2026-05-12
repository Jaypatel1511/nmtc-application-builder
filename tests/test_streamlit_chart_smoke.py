"""Chart smoke tests for every Streamlit page.

Exercises the actual Plotly figure-building code with sample data so that
Plotly API breakages (e.g., 8-char hex colors rejected in Plotly 6.x) are
caught in CI rather than at runtime on Streamlit Cloud.

Strategy: call the chart-construction logic directly without a running
Streamlit server — no AppTest needed.
"""
import sys
import os

# Make streamlit_app helpers importable without a running server
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_STREAMLIT_APP = os.path.join(_REPO_ROOT, "streamlit_app")
for p in [_REPO_ROOT, _STREAMLIT_APP]:
    if p not in sys.path:
        sys.path.insert(0, p)


import plotly.graph_objects as go
import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    TOP_TIER_AGGREGATE_MIN, TOP_TIER_SECTION_MIN,
)
from chart_style import (
    hex_rgba, style_plotly_fig, PLOTLY_CONFIG,
    NAVY, BLUE, MID_BLUE, LIGHT_BLUE, ACCENT, SUCCESS, DANGER, NEUTRAL,
    TEXT_DARK, TEXT_MUTED, TEXT_LIGHT, PANEL_BG, GRID,
)


@pytest.fixture(scope="module")
def sample_score():
    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=20)
    app = Application(cde=cde, requested_allocation=65_000_000, application_round="CY2025")
    app.add_pipeline(pipeline)
    return app.score_win_probability()


class TestPage2WinAlignmentCharts:
    """Charts on 2_Win_Alignment_Scorer.py."""

    def test_section_breakdown_bar_chart(self, sample_score):
        bs = sample_score.business_strategy
        co = sample_score.community_outcomes

        bs_labels = [
            "Product Flexibility", "Pipeline Credibility",
            "Track Record Strength", "Track Record Alignment",
        ]
        bs_keys = [
            "product_flexibility", "pipeline_credibility",
            "track_record_strength", "track_record_alignment",
        ]
        bs_maxes = [10, 15, 15, 10]

        co_labels = [
            "Higher Distress Targeting", "Deep Distress Commitment",
            "Special Targeting", "Outcomes Quality", "Community Accountability",
        ]
        co_keys = [
            "higher_distress_targeting", "deep_distress_commitment",
            "special_targeting", "community_outcomes_quality", "community_accountability",
        ]
        co_maxes = [15, 10, 5, 10, 10]

        all_labels = [f"BS: {l}" for l in bs_labels] + [f"CO: {l}" for l in co_labels]
        all_values = [bs.get(k, 0) for k in bs_keys] + [co.get(k, 0) for k in co_keys]
        all_maxes_list = bs_maxes + co_maxes
        all_colors = [NAVY] * len(bs_labels) + [BLUE] * len(co_labels)

        assert len(all_labels) == 9, "expected 4 BS + 5 CO sub-criteria"
        assert len(all_values) == len(all_labels)
        assert len(all_maxes_list) == len(all_labels)
        assert all(v is not None for v in all_values), "None in all_values"

        # Percentage-normalised bars: every criterion maps to % of its own max so
        # the remainder segment is always proportional (fixes invisible 1-unit remainders).
        all_pcts = [min(v / m * 100, 100) for v, m in zip(all_values, all_maxes_list)]
        all_remainders = [100 - p for p in all_pcts]

        assert all(r >= 0 for r in all_remainders), "negative remainder"
        assert all(p <= 100 for p in all_pcts), "pct > 100"

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=all_labels,
            x=all_pcts,
            orientation="h",
            marker_color=all_colors,
            text=[f"{v}/{m}" for v, m in zip(all_values, all_maxes_list)],
            textposition="outside",
            textfont=dict(color=TEXT_LIGHT, size=10),
            name="Score",
        ))
        # This trace historically crashed because "#ffffff22" (8-char hex) was used.
        fig.add_trace(go.Bar(
            y=all_labels,
            x=all_remainders,
            orientation="h",
            marker_color=hex_rgba("#ffffff", 0.18),
            showlegend=False,
            hoverinfo="skip",
        ))
        assert len(fig.data) == 2

    def test_aggregate_gauge(self, sample_score):
        agg = sample_score.aggregate_base_score
        tier = sample_score.tier
        tier_colors = {
            "Top Tier": SUCCESS,
            "Highly Qualified": MID_BLUE,
            "Not Qualified": DANGER,
        }
        tier_color = tier_colors.get(tier, NEUTRAL)

        # This historically crashed because DANGER+"44" etc. (8-char hex) was used.
        # Bar colour is ACCENT so it always contrasts with the step zone backgrounds —
        # the previous tier_color (MID_BLUE) blended with the HQ step and made the
        # needle appear stuck at 85 instead of its true value.
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=agg,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Aggregate Base Score"},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickvals": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN, TOP_TIER_AGGREGATE_MIN, 100],
                    "ticktext": ["0", f"{HIGHLY_QUALIFIED_AGGREGATE_MIN} HQ",
                                 f"{TOP_TIER_AGGREGATE_MIN} TT", "100"],
                },
                "bar": {"color": ACCENT, "thickness": 0.25},
                "bgcolor": PANEL_BG,
                "steps": [
                    {"range": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN], "color": hex_rgba(DANGER, 0.27)},
                    {"range": [HIGHLY_QUALIFIED_AGGREGATE_MIN, TOP_TIER_AGGREGATE_MIN], "color": hex_rgba(MID_BLUE, 0.27)},
                    {"range": [TOP_TIER_AGGREGATE_MIN, 100], "color": hex_rgba(SUCCESS, 0.27)},
                ],
                "threshold": {
                    "line": {"color": tier_color, "width": 3},
                    "thickness": 0.75,
                    "value": HIGHLY_QUALIFIED_AGGREGATE_MIN,
                },
            },
        ))
        assert fig.data[0].value == agg

    def test_all_tiers_render_gauge(self):
        """Gauge must render without error for every possible tier value."""
        for tier in ("Top Tier", "Highly Qualified", "Not Qualified"):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=50,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": ACCENT, "thickness": 0.25},
                    "steps": [
                        {"range": [0, 85], "color": hex_rgba(DANGER, 0.27)},
                        {"range": [85, 95], "color": hex_rgba(MID_BLUE, 0.27)},
                        {"range": [95, 100], "color": hex_rgba(SUCCESS, 0.27)},
                    ],
                    "threshold": {
                        "line": {"color": MID_BLUE, "width": 3},
                        "thickness": 0.75,
                        "value": 85,
                    },
                },
            ))
            assert fig is not None, f"Gauge failed for tier={tier}"


class TestHexRgbaHelper:
    """Unit tests for the hex_rgba() utility in chart_style."""

    def test_basic_conversion(self):
        assert hex_rgba("#ff0000", 1.0) == "rgba(255,0,0,1.000)"
        assert hex_rgba("#ffffff", 0.0) == "rgba(255,255,255,0.000)"
        assert hex_rgba("#000000", 0.5) == "rgba(0,0,0,0.500)"

    def test_strips_hash(self):
        # Should work with or without leading hash
        result = hex_rgba("ffffff", 0.13)
        assert result == "rgba(255,255,255,0.130)"

    def test_plotly_accepts_output(self):
        color = hex_rgba("#ffffff", 0.13)
        # Plotly must accept the output as a valid bar marker color
        trace = go.Bar(y=["A"], x=[1], marker_color=color)
        assert trace is not None

    def test_danger_mid_blue_success(self):
        """The three colors used in gauge steps must produce valid rgba strings."""
        for color_str in (DANGER, MID_BLUE, SUCCESS):
            result = hex_rgba(color_str, 0.27)
            assert result.startswith("rgba("), f"Expected rgba() for {color_str}, got {result}"
