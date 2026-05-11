"""Win Alignment Scorer — score application vs. historical NMTC winner patterns."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
import streamlit as st

from nmtcapp.core.pipeline import Pipeline

from utils import (
    fmt_pct,
    get_or_create_app,
    tier_badge_html,
    priority_color,
    render_methodology_warning,
    apply_theme,
)
from chart_style import (
    apply_matplotlib_theme, style_plotly_fig, PLOTLY_CONFIG,
    NAVY, BLUE, MID_BLUE, LIGHT_BLUE, ACCENT, SUCCESS, DANGER, NEUTRAL,
    TEXT_DARK, TEXT_MUTED, TEXT_LIGHT, PANEL_BG, GRID,
)

apply_matplotlib_theme()

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
apply_theme()
st.title("🎯 Win Alignment Scorer")
st.markdown(
    "Score this application's alignment with patterns observed in historical NMTC "
    "award winners (CY2020–CY2024) across five weighted dimensions."
)
st.markdown("---")

render_methodology_warning()
st.markdown("---")

# ---------------------------------------------------------------------------
# Ensure we have an Application in session
# ---------------------------------------------------------------------------
app = get_or_create_app()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Scoring session")
    if "analysis" in st.session_state:
        st.success("Pipeline analysis available from analyzer page.")
    else:
        st.info(
            "No pipeline analysis found in session. Using sample pipeline. "
            "Run the Pipeline Analyzer first to use your own data."
        )
    st.markdown("---")
    st.caption(
        "Competitive threshold: **55 points** (composite). "
        "Strong alignment: **75+ points**."
    )

# ---------------------------------------------------------------------------
# Score button
# ---------------------------------------------------------------------------
score_clicked = st.button("▶  Score Application", type="primary")

if score_clicked:
    try:
        with st.spinner("Computing alignment score…"):
            win_score = app.score_win_probability()
        st.session_state["win_score"] = win_score
    except Exception as exc:
        st.error(f"Scoring failed: {exc}")
        st.stop()

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
if "win_score" not in st.session_state:
    st.info("Click **Score Application** to compute the alignment score.")
    st.stop()

score = st.session_state["win_score"]
composite = score.composite_score
tier = score.competitive_tier
dim_scores = score.dimensional_scores
baseline = score.acceptance_rate_baseline
COMPETITIVE_THRESHOLD = 55.0

# ---------------------------------------------------------------------------
# Top-line score metrics
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    delta = composite - COMPETITIVE_THRESHOLD
    st.metric(
        "Composite alignment score",
        f"{composite:.1f} / 100",
        delta=f"{delta:+.1f} vs. competitive threshold (55)",
        delta_color="normal" if delta >= 0 else "inverse",
    )

with col2:
    st.metric(
        "Historical acceptance baseline",
        fmt_pct(baseline),
        help="Average acceptance rate across the 4 most recent NMTC rounds.",
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Competitive tier:**")
    st.markdown(tier_badge_html(tier), unsafe_allow_html=True)
    st.markdown(f"<br><small>{score.peer_comparison}</small>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# J: Composite score gauge
# ---------------------------------------------------------------------------
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=composite,
    domain={"x": [0, 1], "y": [0, 1]},
    title={"text": "Composite Alignment Score", "font": {"size": 13, "color": TEXT_LIGHT}},
    number={"suffix": " / 100", "font": {"size": 26, "color": TEXT_LIGHT}},
    gauge={
        "axis": {
            "range": [0, 100],
            "tickwidth": 1,
            "tickcolor": TEXT_MUTED,
            "tickvals": [0, 30, 55, 75, 100],
            "ticktext": ["0", "30", "55 (threshold)", "75", "100"],
        },
        "bar": {"color": NAVY, "thickness": 0.28},
        "bgcolor": PANEL_BG,
        "borderwidth": 1,
        "bordercolor": "#D1D5DB",
        "steps": [
            {"range": [0, 30],  "color": DANGER},
            {"range": [30, 55], "color": ACCENT},
            {"range": [55, 75], "color": MID_BLUE},
            {"range": [75, 100], "color": SUCCESS},
        ],
        "threshold": {
            "line": {"color": NAVY, "width": 3},
            "thickness": 0.75,
            "value": COMPETITIVE_THRESHOLD,
        },
    },
))
fig_gauge.update_layout(
    height=260,
    margin=dict(l=30, r=30, t=50, b=10),
    paper_bgcolor=PANEL_BG,
    font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_DARK),
)
st.plotly_chart(fig_gauge, use_container_width=True, config=PLOTLY_CONFIG)

st.markdown("---")

# ---------------------------------------------------------------------------
# I: Radar chart + dimensional bar chart
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1])

dim_labels = {
    "distress_concentration": "Distress",
    "geographic_diversity": "Geographic",
    "impact_intensity": "Impact",
    "sector_diversity": "Sector",
    "pipeline_quality": "Pipeline",
}

radar_labels = [dim_labels[k] for k in dim_scores]
radar_values = [dim_scores[k] for k in dim_scores]

with left:
    st.subheader("Dimensional radar")

    fig_radar = go.Figure()

    # Winner median reference layer (LIGHT_BLUE dashed)
    fig_radar.add_trace(
        go.Scatterpolar(
            r=[COMPETITIVE_THRESHOLD] * len(radar_labels) + [COMPETITIVE_THRESHOLD],
            theta=radar_labels + [radar_labels[0]],
            fill=None,
            line=dict(dash="dash", color=LIGHT_BLUE, width=2),
            name="Competitive threshold (55)",
        )
    )

    # Your pipeline trace (NAVY filled, 30% opacity)
    fig_radar.add_trace(
        go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            fillcolor=f"rgba(14,47,86,0.30)",
            line=dict(color=NAVY, width=2.5),
            name="Your pipeline",
        )
    )

    fig_radar = style_plotly_fig(fig_radar, height=390)
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 100],
                tickfont=dict(size=10, color=TEXT_MUTED),
                gridcolor=GRID,
            ),
            angularaxis=dict(tickfont=dict(size=11, color=TEXT_LIGHT)),
            bgcolor=PANEL_BG,
        ),
        showlegend=True,
        legend=dict(
            orientation="h", y=-0.18,
            font=dict(size=11, color=TEXT_LIGHT),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=30, r=30, t=30, b=60),
    )
    st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_CONFIG)

with right:
    st.subheader("Dimensional scores")

    bar_labels = [dim_labels[k] for k in dim_scores]
    bar_values = [dim_scores[k] for k in dim_scores]

    fig_bar = go.Figure()

    fig_bar.add_trace(
        go.Bar(
            y=bar_labels,
            x=bar_values,
            orientation="h",
            name="Your score",
            marker_color=[
                NAVY if v >= COMPETITIVE_THRESHOLD else ACCENT for v in bar_values
            ],
            text=[f"{v:.1f}" for v in bar_values],
            textposition="outside",
            textfont=dict(color=TEXT_LIGHT, size=11),
        )
    )

    fig_bar.add_vline(
        x=COMPETITIVE_THRESHOLD,
        line_dash="dash",
        line_color=LIGHT_BLUE,
        line_width=1.5,
        annotation_text="Competitive (55)",
        annotation_position="top",
        annotation_font_size=10,
        annotation_font_color=TEXT_LIGHT,
    )

    fig_bar = style_plotly_fig(fig_bar, height=350)
    fig_bar.update_layout(
        xaxis=dict(range=[0, 115], title="Score (0–100)"),
        yaxis=dict(title=None),
        showlegend=False,
        margin=dict(l=10, r=50, t=20, b=10),
        bargap=0.35,
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

# Weights reference
with st.expander("Dimension weights"):
    st.markdown(
        "| Dimension | Weight | Description |\n"
        "|---|---|---|\n"
        "| Distress Concentration | **35%** | % of QEI in deep/severe distress tracts |\n"
        "| Impact Intensity | **25%** | Jobs per $1MM QEI vs. winner benchmarks |\n"
        "| Geographic Diversity | **20%** | State count, HHI, and rural share |\n"
        "| Sector Diversity | **15%** | Number of sectors and concentration |\n"
        "| Pipeline Quality | **5%** | Eligibility rate, project count, award size fit |"
    )

# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("📋 Get Recommendations", expanded=False):
    rec_clicked = st.button("Generate recommendations", key="rec_btn")

    if rec_clicked or "recommendations" in st.session_state:
        if rec_clicked:
            try:
                with st.spinner("Generating recommendations…"):
                    recs = app.recommendations()
                st.session_state["recommendations"] = recs
            except Exception as exc:
                st.error(f"Failed to generate recommendations: {exc}")
                st.stop()

        recs = st.session_state["recommendations"]

        st.markdown(f"**Assessment:** {recs.overall_assessment}")
        st.markdown("---")

        priority_order = [("critical", "🚨 Critical"), ("high", "🔶 High"), ("medium", "🟢 Medium")]

        for priority, label in priority_order:
            priority_recs = [r for r in recs.recommendations if r.priority == priority]
            if not priority_recs:
                continue
            st.markdown(f"### {label} priority")
            for r in priority_recs:
                color = priority_color(r.priority)
                st.markdown(
                    f"""
                    <div style="border-left:4px solid {color};
                                padding:0.75rem 1rem;
                                margin-bottom:0.75rem;
                                background:#1A1F2E;
                                border-radius:0 8px 8px 0;
                                color:#F3F4F6;
                                box-shadow:0 1px 4px rgba(0,0,0,0.4);">
                        <strong style="color:{color};">[{r.category.upper()}]</strong>
                        &nbsp;{r.finding}<br>
                        <em>Action:</em> {r.action}<br>
                        <small><em>Expected impact:</em> {r.expected_impact}</small><br>
                        <small><em>Estimate:</em> {r.quantified_improvement}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Click **Generate recommendations** to see prioritised actions.")
