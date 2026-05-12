"""Win Alignment Scorer — score application against CDFI Fund CY 2024-2025 framework."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
import streamlit as st

from nmtcapp.core.pipeline import Pipeline
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    TOP_TIER_AGGREGATE_MIN, TOP_TIER_SECTION_MIN,
)

from utils import (
    fmt_pct,
    get_or_create_app,
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
    "Score this application against the CDFI Fund's published CY 2024-2025 Review Process "
    "criteria — Business Strategy (50 pts) + Community Outcomes (50 pts) + Priority Points (10 pts)."
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
            "No pipeline analysis found. Using sample pipeline. "
            "Run the Pipeline Analyzer first to use your own data."
        )
    st.markdown("---")
    st.markdown(
        f"**Highly Qualified gate:** {HIGHLY_QUALIFIED_AGGREGATE_MIN}+ aggregate AND "
        f"{HIGHLY_QUALIFIED_SECTION_MIN}+ in each section"
    )
    st.markdown(
        f"**Top Tier gate:** {TOP_TIER_AGGREGATE_MIN}+ aggregate AND "
        f"{TOP_TIER_SECTION_MIN}+ in each section"
    )

# ---------------------------------------------------------------------------
# Score button
# ---------------------------------------------------------------------------
score_clicked = st.button("▶  Score Application", type="primary")

if score_clicked:
    try:
        with st.spinner("Computing CDFI Fund framework score…"):
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
tier = score.tier
agg = score.aggregate_base_score
agg_with_pp = score.aggregate_with_priority
bs = score.business_strategy
co = score.community_outcomes
pp = score.priority_points

# ---------------------------------------------------------------------------
# Tier badge + top metrics
# ---------------------------------------------------------------------------
tier_colors = {
    "Top Tier": SUCCESS,
    "Highly Qualified": MID_BLUE,
    "Not Qualified": DANGER,
}
tier_color = tier_colors.get(tier, NEUTRAL)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Aggregate Base Score", f"{agg} / 100")
col2.metric("With Priority Points", f"{agg_with_pp} / 110")
col3.metric("Business Strategy", f"{bs['section_total']} / 50",
            delta="✓ meets min" if bs['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN else "✗ below min",
            delta_color="normal" if bs['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN else "inverse")
col4.metric("Community Outcomes", f"{co['section_total']} / 50",
            delta="✓ meets min" if co['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN else "✗ below min",
            delta_color="normal" if co['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN else "inverse")

# Tier badge
st.markdown(
    f"""
    <div style="display:inline-block; padding:8px 20px; border-radius:20px;
                background:{tier_color}22; border:2px solid {tier_color};
                font-size:18px; font-weight:700; color:{tier_color}; margin:8px 0;">
        {tier.upper()}
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<small>{score.peer_comparison}</small>", unsafe_allow_html=True)

# Gating notes
if score.tier_gating_notes:
    st.markdown("---")
    st.warning("**Gating status:**")
    for note in score.tier_gating_notes:
        st.markdown(f"⚠️ {note}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Two-section bar chart + gauge
# ---------------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    st.subheader("Section breakdown")

    # Sub-scores for Business Strategy
    bs_labels = [
        "Product Flexibility", "Pipeline Credibility",
        "Track Record Strength", "Track Record Alignment"
    ]
    bs_keys = [
        "product_flexibility", "pipeline_credibility",
        "track_record_strength", "track_record_alignment"
    ]
    bs_maxes = [10, 15, 15, 10]

    co_labels = [
        "Higher Distress Targeting", "Deep Distress Commitment",
        "Special Targeting", "Outcomes Quality", "Community Accountability"
    ]
    co_keys = [
        "higher_distress_targeting", "deep_distress_commitment",
        "special_targeting", "community_outcomes_quality", "community_accountability"
    ]
    co_maxes = [15, 10, 5, 10, 10]

    all_labels = [f"BS: {l}" for l in bs_labels] + [f"CO: {l}" for l in co_labels]
    all_values = [bs.get(k, 0) for k in bs_keys] + [co.get(k, 0) for k in co_keys]
    all_maxes = bs_maxes + co_maxes
    all_colors = [NAVY] * len(bs_labels) + [BLUE] * len(co_labels)

    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(
        y=all_labels,
        x=all_values,
        orientation="h",
        marker_color=all_colors,
        text=[f"{v}/{m}" for v, m in zip(all_values, all_maxes)],
        textposition="outside",
        textfont=dict(color=TEXT_LIGHT, size=10),
        name="Score",
    ))
    fig_bars.add_trace(go.Bar(
        y=all_labels,
        x=[m - v for v, m in zip(all_values, all_maxes)],
        orientation="h",
        marker_color="#ffffff22",
        showlegend=False,
        hoverinfo="skip",
    ))

    fig_bars = style_plotly_fig(fig_bars, height=480)
    fig_bars.update_layout(
        barmode="stack",
        xaxis=dict(range=[0, 20], title="Points scored"),
        yaxis=dict(title=None, tickfont=dict(size=10)),
        showlegend=False,
        margin=dict(l=10, r=60, t=10, b=20),
        bargap=0.25,
        annotations=[
            dict(
                x=-0.5, y=3.5, xref="x", yref="y",
                text="◀ Business Strategy", showarrow=False,
                font=dict(size=10, color=NAVY), xanchor="right",
            ),
            dict(
                x=-0.5, y=-1, xref="x", yref="y",
                text="◀ Community Outcomes", showarrow=False,
                font=dict(size=10, color=BLUE), xanchor="right",
            ),
        ],
    )
    st.plotly_chart(fig_bars, use_container_width=True, config=PLOTLY_CONFIG)

with right:
    st.subheader("Aggregate gauge")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=agg,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Aggregate Base Score", "font": {"size": 12, "color": TEXT_LIGHT}},
        number={"suffix": " / 100", "font": {"size": 22, "color": TEXT_LIGHT}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": TEXT_MUTED,
                "tickvals": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN, TOP_TIER_AGGREGATE_MIN, 100],
                "ticktext": ["0", f"{HIGHLY_QUALIFIED_AGGREGATE_MIN} (HQ)", f"{TOP_TIER_AGGREGATE_MIN} (TT)", "100"],
            },
            "bar": {"color": tier_color, "thickness": 0.30},
            "bgcolor": PANEL_BG,
            "borderwidth": 1,
            "bordercolor": "#D1D5DB",
            "steps": [
                {"range": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN], "color": DANGER + "44"},
                {"range": [HIGHLY_QUALIFIED_AGGREGATE_MIN, TOP_TIER_AGGREGATE_MIN], "color": MID_BLUE + "44"},
                {"range": [TOP_TIER_AGGREGATE_MIN, 100], "color": SUCCESS + "44"},
            ],
            "threshold": {
                "line": {"color": ACCENT, "width": 3},
                "thickness": 0.75,
                "value": HIGHLY_QUALIFIED_AGGREGATE_MIN,
            },
        },
    ))
    fig_gauge.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor=PANEL_BG,
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_DARK),
    )
    st.plotly_chart(fig_gauge, use_container_width=True, config=PLOTLY_CONFIG)

    # Section minimums status
    st.markdown("**Section minimum status**")
    for section_name, section_total, threshold in [
        ("Business Strategy", bs["section_total"], HIGHLY_QUALIFIED_SECTION_MIN),
        ("Community Outcomes", co["section_total"], HIGHLY_QUALIFIED_SECTION_MIN),
    ]:
        icon = "✅" if section_total >= threshold else "❌"
        st.markdown(f"{icon} **{section_name}:** {section_total}/50 (min {threshold})")

    # Priority Points
    st.markdown(f"**Priority Points:** {pp['section_total']}/10")
    st.markdown(f"  DBC Track Record: {pp.get('dbc_track_record', 0)}/5")
    st.markdown(f"  Unrelated Entities: {pp.get('unrelated_entities', 0)}/5")

st.markdown("---")

# ---------------------------------------------------------------------------
# Section details expander
# ---------------------------------------------------------------------------
with st.expander("Scoring framework reference", expanded=False):
    st.markdown(
        "| Section | Sub-criterion | Max | Your score |\n"
        "|---|---|---|---|\n"
        f"| Business Strategy | Product Flexibility | 10 | {bs.get('product_flexibility', 0)} |\n"
        f"| Business Strategy | Pipeline Credibility | 15 | {bs.get('pipeline_credibility', 0)} |\n"
        f"| Business Strategy | Track Record Strength | 15 | {bs.get('track_record_strength', 0)} |\n"
        f"| Business Strategy | Track Record Alignment | 10 | {bs.get('track_record_alignment', 0)} |\n"
        f"| Community Outcomes | Higher Distress Targeting | 15 | {co.get('higher_distress_targeting', 0)} |\n"
        f"| Community Outcomes | Deep Distress Commitment | 10 | {co.get('deep_distress_commitment', 0)} |\n"
        f"| Community Outcomes | Special Targeting | 5 | {co.get('special_targeting', 0)} |\n"
        f"| Community Outcomes | Outcomes Quality | 10 | {co.get('community_outcomes_quality', 0)} |\n"
        f"| Community Outcomes | Community Accountability | 10 | {co.get('community_accountability', 0)} |\n"
        f"| Priority Points | DBC Track Record | 5 | {pp.get('dbc_track_record', 0)} |\n"
        f"| Priority Points | Unrelated Entities | 5 | {pp.get('unrelated_entities', 0)} |\n"
    )
    st.markdown(
        "> **Sub-score disclosure:** Weights within each section are this tool's interpretation of "
        "the CDFI Fund's CY 2024-2025 Review Process. The CDFI Fund does not publish exact "
        "point values for individual sub-criteria."
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
                citation_html = (
                    f"<small><em>Citation:</em> {r.citation}</small><br>"
                    if r.citation else ""
                )
                st.markdown(
                    f"""
                    <div style="border-left:4px solid {color};
                                padding:0.75rem 1rem;
                                margin-bottom:0.75rem;
                                background:#1A1F2E;
                                border-radius:0 8px 8px 0;
                                color:#F3F4F6;
                                box-shadow:0 1px 4px rgba(0,0,0,0.4);">
                        <strong style="color:{color};">[{r.category.replace('_', ' ').upper()}]</strong>
                        &nbsp;{r.finding}<br>
                        <em>Action:</em> {r.action}<br>
                        <small><em>Expected impact:</em> {r.expected_impact}</small><br>
                        <small><em>Estimate:</em> {r.quantified_improvement}</small><br>
                        {citation_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Click **Generate recommendations** to see prioritised actions.")
