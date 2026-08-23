"""Win Alignment Scorer — score application against CDFI Fund CY 2024-2025 framework."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
import streamlit as st

from nmtcapp.core.pipeline import Pipeline
from nmtcapp.renderers._round_provenance import round_provenance_paragraphs
from nmtcapp.data.benchmark_thresholds import (
    HIGHLY_QUALIFIED_AGGREGATE_MIN, HIGHLY_QUALIFIED_SECTION_MIN,
    HOUSE_TOP_TIER_AGGREGATE_MIN, HOUSE_TOP_TIER_SECTION_MIN,
)

from utils import (
    md,
    fmt_pct,
    get_or_create_app,
    priority_color,
    render_methodology_warning,
    apply_theme,
    metric_classification,
)
from chart_style import (
    apply_matplotlib_theme, hex_rgba, style_plotly_fig, PLOTLY_CONFIG,
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

# WHICH ROUND, ON THE PAGE THAT SCORES AGAINST IT (1.5.4 T1). This page names
# CY 2024-2025 four times -- in its title docstring, in the sentence under the
# heading, in the sidebar's Highly Qualified citation and in the sub-score
# disclosure -- and said nothing about that round being closed and awarded on
# 23 Dec 2025, or about CY 2026 being announced on 12 Aug 2026 at $5 billion
# and not open. Markdown, Word, Excel and PDF have all carried this note since
# 1.5.0; the gate that put it there enumerates the four Application.generate()
# formats, and a Streamlit page is not one of them.
#
# READ, NOT RETYPED. A fifth hand-typed copy of the round caveat is the exact
# shape _round_provenance was created to remove.
st.info(md(round_provenance_paragraphs()[0]))
st.markdown("---")

# ---------------------------------------------------------------------------
# Ensure we have an Application in session
# ---------------------------------------------------------------------------
app = get_or_create_app()
_is_demo = st.session_state.get("is_demo_data", True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Scoring session")
    if "analysis" in st.session_state and not _is_demo:
        st.success("Scoring your uploaded pipeline.")
    else:
        st.info(
            "No uploaded pipeline found — scoring the Riverbend Community Capital "
            "sample CDE. Run the Pipeline Analyzer first and upload your own CSV "
            "to score your application."
        )
    st.markdown("---")
    # D4, FIFTH SURFACE — found in 1.2.2 round 2, and NOT on round 1's list of
    # four. These two lines render one under the other, in the same weight and
    # the same shape, so a CDE reads them as a matched pair of CDFI Fund gates.
    # Only the first one is. The second is this package's own invented tier, and
    # nothing on the page said so.
    #
    # THE GATE CANNOT SEE THIS STRING. tests/test_fund_attribution_source.py
    # requires an AUTHORITY token, and "Top Tier gate: 95+ aggregate AND 45+ in
    # each section" names no authority at all — the same blind spot that let
    # docs/reference/methodology.md:42 survive the release opened to sweep its
    # siblings, one detector further out. Recorded in CHANGELOG.md under what
    # the gate still cannot see.
    st.markdown(
        f"**Highly Qualified gate (CDFI Fund):** {HIGHLY_QUALIFIED_AGGREGATE_MIN}+ "
        f"aggregate AND {HIGHLY_QUALIFIED_SECTION_MIN}+ in each section — "
        "CY 2024-2025 Review Process, p.3 Step 2"
    )
    st.markdown(
        f"**Top Tier (this tool's label, not a CDFI Fund tier):** "
        f"{HOUSE_TOP_TIER_AGGREGATE_MIN}+ aggregate AND {HOUSE_TOP_TIER_SECTION_MIN}+ "
        "in each section. The CDFI Fund publishes the Highly Qualified gate and "
        "nothing above it; these cut points are an unsourced house heuristic."
    )

# ---------------------------------------------------------------------------
# Demo-mode banner (pre-score)
# ---------------------------------------------------------------------------
if _is_demo:
    st.info(
        "📊 **DEMO MODE** — This page is scoring the sample CDE "
        "**Riverbend Community Capital CDE, LLC** (\\$65M requested, 20-project pipeline). "
        "Scores shown here are NOT your application's scores. "
        "Go to **Pipeline Analyzer** and upload your own CSV first."
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

_partial = getattr(score, "partial", False)
if _partial:
    st.error(
        "**Eligibility data unavailable** — "
        f"{getattr(score, 'eligibility_data_error', None) or 'reason unknown'}. "
        f"{score.partial_note}. Higher Distress Targeting and Deep Distress "
        "Commitment could not be assessed; no tier is assigned."
    )

# ---------------------------------------------------------------------------
# Tier badge + top metrics
# ---------------------------------------------------------------------------
tier_colors = {
    "Top Tier": SUCCESS,
    "Highly Qualified": MID_BLUE,
    "Not Qualified": DANGER,
}
tier_color = tier_colors.get(tier, NEUTRAL)

_bs_max = bs.get("max_available", 50)
_co_max = co.get("max_available", 50)
_agg_max = _bs_max + _co_max
_partial_tag = " (partial)" if _partial else ""

col1, col2, col3, col4 = st.columns(4)
col1.metric("Aggregate Base Score" + _partial_tag, f"{agg} / {_agg_max}")
col2.metric("With Priority Points" + _partial_tag,
            f"{agg_with_pp} / {_agg_max + pp.get('max_available', 10)}")
# GATING VERDICTS, NOT MOVEMENTS (1.5.1 audit, F1 sweep). Both of these passed
# "✓ meets min" / "✗ below min" as `delta`. Neither carries a sign, so BOTH
# rendered with an UP arrow — an application below the published Highly
# Qualified section minimum was shown a red cross pointing upward. Two more
# sites of T4's defect, on the page whose whole subject is the gate.
_bs_meets = bs['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN
metric_classification(
    col3, "Business Strategy", f"{bs['section_total']} / {_bs_max}",
    "✓ meets min" if _bs_meets else "✗ below min",
    tone="good" if _bs_meets else "bad",
)
if _partial:
    col4.metric("Community Outcomes (partial)", f"{co['section_total']} / {_co_max}")
else:
    _co_meets = co['section_total'] >= HIGHLY_QUALIFIED_SECTION_MIN
    metric_classification(
        col4, "Community Outcomes", f"{co['section_total']} / {_co_max}",
        "✓ meets min" if _co_meets else "✗ below min",
        tone="good" if _co_meets else "bad",
    )

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

# Demo-mode banner (post-score, prominent inline with results)
if _is_demo:
    st.warning(
        "⚠️ **DEMO MODE — Sample CDE scores** — The numbers above reflect "
        "**Riverbend Community Capital CDE, LLC**, not your application. "
        "Upload your own pipeline on the **Pipeline Analyzer** page to see your CDE's score."
    )

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
    all_raw = [bs.get(k, 0) for k in bs_keys] + [co.get(k, 0) for k in co_keys]
    # None = component excluded (eligibility data unavailable) — render as n/a
    all_values = [0 if v is None else v for v in all_raw]
    all_maxes = bs_maxes + co_maxes
    all_colors = [NAVY] * len(bs_labels) + [BLUE] * len(co_labels)

    # Normalise every criterion to % of its own maximum so the remainder segment
    # is always proportional (fixes invisible 1-pt remainders on 9/10-style bars).
    all_pcts = [min(v / m * 100, 100) for v, m in zip(all_values, all_maxes)]
    all_remainders = [100 - p for p in all_pcts]

    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(
        y=all_labels,
        x=all_pcts,
        orientation="h",
        marker_color=all_colors,
        text=["n/a" if raw is None else f"{v}/{m}"
              for raw, v, m in zip(all_raw, all_values, all_maxes)],
        textposition="outside",
        textfont=dict(color=TEXT_LIGHT, size=10),
        name="Score",
    ))
    fig_bars.add_trace(go.Bar(
        y=all_labels,
        x=all_remainders,
        orientation="h",
        marker_color=hex_rgba("#ffffff", 0.18),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig_bars = style_plotly_fig(fig_bars, height=480)
    fig_bars.update_layout(
        barmode="stack",
        xaxis=dict(range=[0, 125], title="% of criterion maximum",
                   tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0%", "25%", "50%", "75%", "100%"]),
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
    st.plotly_chart(fig_bars, width="stretch", config=PLOTLY_CONFIG)

with right:
    st.subheader("Aggregate gauge")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=agg,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Aggregate Base Score" + (" (PARTIAL)" if _partial else ""),
               "font": {"size": 12, "color": TEXT_LIGHT}},
        number={"suffix": f" / {_agg_max}", "font": {"size": 22, "color": TEXT_LIGHT}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": TEXT_MUTED,
                # Shorter labels prevent right-edge clipping ("85 (HQ)" → "85 HQ")
                "tickvals": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN, HOUSE_TOP_TIER_AGGREGATE_MIN, 100],
                "ticktext": ["0", f"{HIGHLY_QUALIFIED_AGGREGATE_MIN} HQ",
                             f"{HOUSE_TOP_TIER_AGGREGATE_MIN} TT", "100"],
            },
            # Use ACCENT (gold) for the bar so it contrasts with every step zone colour.
            # The previous tier_color matched the HQ step background (both MID_BLUE),
            # making the bar edge invisible at ~85 and causing the needle to appear
            # stuck at the red/blue zone boundary instead of the actual value.
            "bar": {"color": ACCENT, "thickness": 0.25},
            "bgcolor": PANEL_BG,
            "borderwidth": 1,
            "bordercolor": "#D1D5DB",
            "steps": [
                {"range": [0, HIGHLY_QUALIFIED_AGGREGATE_MIN], "color": hex_rgba(DANGER, 0.27)},
                {"range": [HIGHLY_QUALIFIED_AGGREGATE_MIN, HOUSE_TOP_TIER_AGGREGATE_MIN], "color": hex_rgba(MID_BLUE, 0.27)},
                {"range": [HOUSE_TOP_TIER_AGGREGATE_MIN, 100], "color": hex_rgba(SUCCESS, 0.27)},
            ],
            "threshold": {
                "line": {"color": tier_color, "width": 3},
                "thickness": 0.75,
                "value": HIGHLY_QUALIFIED_AGGREGATE_MIN,
            },
        },
    ))
    fig_gauge.update_layout(
        height=300,
        # r=80 gives enough room for "100" and "95 TT" tick labels at 3 o'clock
        margin=dict(l=20, r=80, t=50, b=10),
        paper_bgcolor=PANEL_BG,
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_DARK),
    )
    st.plotly_chart(fig_gauge, width="stretch", config=PLOTLY_CONFIG)

    # Section minimums status
    st.markdown("**Section minimum status**")
    icon = "✅" if bs["section_total"] >= HIGHLY_QUALIFIED_SECTION_MIN else "❌"
    st.markdown(
        f"{icon} **Business Strategy:** {bs['section_total']}/{_bs_max} "
        f"(min {HIGHLY_QUALIFIED_SECTION_MIN})"
    )
    if _partial:
        st.markdown(
            f"⚠️ **Community Outcomes:** {co['section_total']}/{_co_max} — "
            "partial (eligibility data unavailable); minimum not assessed"
        )
    else:
        icon = "✅" if co["section_total"] >= HIGHLY_QUALIFIED_SECTION_MIN else "❌"
        st.markdown(
            f"{icon} **Community Outcomes:** {co['section_total']}/{_co_max} "
            f"(min {HIGHLY_QUALIFIED_SECTION_MIN})"
        )

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
        f"| Community Outcomes | Higher Distress Targeting | 15 | {'n/a — eligibility data unavailable' if co.get('higher_distress_targeting') is None else co.get('higher_distress_targeting', 0)} |\n"
        f"| Community Outcomes | Deep Distress Commitment | 10 | {'n/a — eligibility data unavailable' if co.get('deep_distress_commitment') is None else co.get('deep_distress_commitment', 0)} |\n"
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
                    # Use the same win_score object already displayed above — never
                    # recompute it here — so recommendation text matches the scores.
                    from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
                    from nmtcapp.intelligence.recommendations import RecommendationEngine
                    _analysis = app.analyze()
                    _bc = HistoricalBenchmarks().compare(
                        _analysis.pipeline_result, app.requested_allocation
                    )
                    recs = RecommendationEngine().recommend(
                        _analysis.pipeline_result, _bc, score
                    )
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
