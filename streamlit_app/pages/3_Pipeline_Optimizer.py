"""Pipeline Optimizer — select the highest-scoring project subset."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from nmtcapp.optimizer.constraints import OptimizationConstraints

from utils import (
    ACCENT,
    PRIMARY,
    SUCCESS,
    WARNING,
    DANGER,
    MUTED,
    VALID_SECTORS,
    fmt_millions,
    fmt_pct,
    get_or_create_app,
)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("⚙️ Pipeline Optimizer")
st.markdown(
    "Automatically select the highest-scoring project subset from your pipeline given "
    "QEI budget, geographic diversity, and sector constraints. Uses a **greedy construction "
    "+ swap-based local search** algorithm — no LP/MIP solver required."
)

st.info(
    "The optimizer maximizes composite alignment with historical NMTC winner patterns. "
    "Alignment score ≠ win probability — see the Win Alignment Scorer for framing guidance."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — optimizer constraints
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Optimization constraints")

    max_total_qei = st.slider(
        "Max total QEI ($M)",
        min_value=20,
        max_value=100,
        value=65,
        step=5,
        help="Maximum total QEI for the selected project subset.",
    )

    min_states = st.slider(
        "Min states",
        min_value=1,
        max_value=15,
        value=5,
        help="Minimum number of distinct states the selected projects must span.",
    )

    min_projects = st.number_input(
        "Min projects",
        min_value=1,
        max_value=50,
        value=8,
        step=1,
        help="Minimum number of projects that must be selected.",
    )

    required_sectors = st.multiselect(
        "Required sectors",
        options=VALID_SECTORS,
        default=[],
        format_func=lambda s: s.replace("_", " ").title(),
        help="Sectors that must be represented in the selected subset.",
    )

    st.markdown("---")
    st.caption(
        "The optimizer will always return a result. If constraints are infeasible "
        "for the current pipeline, the original full pipeline is returned with an "
        "infeasibility notice."
    )

# ---------------------------------------------------------------------------
# Ensure Application in session
# ---------------------------------------------------------------------------
app = get_or_create_app()

# ---------------------------------------------------------------------------
# Run optimizer
# ---------------------------------------------------------------------------
run_clicked = st.button("▶  Run Optimizer", type="primary")

if run_clicked:
    constraints = OptimizationConstraints(
        max_total_qei=max_total_qei * 1_000_000,
        min_states=int(min_states),
        min_projects=int(min_projects),
        required_sectors=list(required_sectors),
    )
    try:
        with st.spinner("Optimizing pipeline… (greedy + local search)"):
            result = app.optimize_pipeline(constraints=constraints)
        st.session_state["opt_result"] = result
        st.session_state["opt_constraints"] = {
            "max_total_qei_m": max_total_qei,
            "min_states": min_states,
            "min_projects": min_projects,
            "required_sectors": required_sectors,
        }
    except Exception as exc:
        st.error(f"Optimization failed: {exc}")
        st.stop()

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
if "opt_result" not in st.session_state:
    st.info("Set constraints in the sidebar and click **Run Optimizer** to begin.")
    st.stop()

result = st.session_state["opt_result"]
constraints_used = st.session_state.get("opt_constraints", {})

score_before = result.alignment_score_before * 100
score_after = result.alignment_score_after * 100
delta = score_after - score_before
selected = result.selected_projects
total_qei_selected = sum(p.qei_request for p in selected)

# ---------------------------------------------------------------------------
# Feasibility notice
# ---------------------------------------------------------------------------
if not result.constraints_satisfied:
    st.warning(
        f"⚠️ **Constraints not fully satisfied:** {result.infeasibility_reason}. "
        "The optimizer returned the best feasible result given the pipeline."
    )
else:
    st.success("✅ All constraints satisfied.")

# ---------------------------------------------------------------------------
# Before / after score comparison
# ---------------------------------------------------------------------------
st.subheader("Score comparison")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Score before", f"{score_before:.1f} / 100", help="Full pipeline alignment score.")
c2.metric(
    "Score after",
    f"{score_after:.1f} / 100",
    delta=f"{delta:+.1f} pts",
    delta_color="normal" if delta >= 0 else "inverse",
)
c3.metric("Projects selected", len(selected), delta=f"of {len(list(app.pipeline))}")
c4.metric("Total QEI selected", fmt_millions(total_qei_selected))

st.markdown("---")

# ---------------------------------------------------------------------------
# Dimensional improvements table
# ---------------------------------------------------------------------------
st.subheader("Dimensional improvements")

dim_improvements = result.dimensional_improvements
if dim_improvements:
    dim_rows = []
    for dim, delta_v in dim_improvements.items():
        delta_pts = delta_v * 100
        arrow = "▲" if delta_pts > 0.05 else ("▼" if delta_pts < -0.05 else "→")
        color = SUCCESS if delta_pts > 0.05 else (DANGER if delta_pts < -0.05 else MUTED)
        dim_rows.append(
            {
                "Dimension": dim.replace("_", " ").title(),
                "Change": f"{arrow} {delta_pts:+.1f} pts",
                "Direction": arrow,
                "_color": color,
                "_delta": delta_pts,
            }
        )
    dim_df = pd.DataFrame(dim_rows)[["Dimension", "Change"]]
    st.dataframe(dim_df, use_container_width=True, hide_index=True)

    # Waterfall-style bar chart
    fig_dims = go.Figure()
    fig_dims.add_trace(
        go.Bar(
            y=[r["Dimension"] for r in dim_rows],
            x=[r["_delta"] for r in dim_rows],
            orientation="h",
            marker_color=[
                SUCCESS if r["_delta"] > 0.05 else (DANGER if r["_delta"] < -0.05 else MUTED)
                for r in dim_rows
            ],
            text=[f"{r['_delta']:+.1f}" for r in dim_rows],
            textposition="outside",
        )
    )
    fig_dims.add_vline(x=0, line_color="black", line_width=1)
    fig_dims.update_layout(
        xaxis_title="Score change (points)",
        yaxis_title=None,
        margin=dict(l=0, r=40, t=10, b=0),
        height=260,
        showlegend=False,
    )
    st.plotly_chart(fig_dims, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Selected projects table
# ---------------------------------------------------------------------------
st.subheader("Selected projects")

if selected:
    proj_data = [
        {
            "Project ID": p.project_id,
            "Project Name": p.project_name,
            "State": p.state,
            "Sector": p.sector.replace("_", " ").title(),
            "QEI Request ($M)": round(p.qei_request / 1_000_000, 2),
            "Jobs Created": p.expected_jobs_created,
            "Distress Level": (p.distress_level or "N/A").title(),
        }
        for p in selected
    ]
    proj_df = pd.DataFrame(proj_data)
    st.dataframe(proj_df, use_container_width=True, hide_index=True)
else:
    st.warning("No projects selected.")

# ---------------------------------------------------------------------------
# Sector pie chart of selected projects
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Selected projects — sector breakdown")

if selected:
    sector_qei: dict = {}
    for p in selected:
        sector_qei[p.sector] = sector_qei.get(p.sector, 0) + p.qei_request

    sector_labels = [k.replace("_", " ").title() for k in sector_qei]
    sector_values = list(sector_qei.values())

    left, right = st.columns([1, 1])

    with left:
        fig_pie = px.pie(
            names=sector_labels,
            values=sector_values,
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Selected QEI by sector",
            hole=0.35,
        )
        fig_pie.update_traces(
            textinfo="label+percent",
            hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
        )
        fig_pie.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            height=340,
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with right:
        st.markdown("**State distribution**")
        state_counts: dict = {}
        for p in selected:
            state_counts[p.state] = state_counts.get(p.state, 0) + 1
        state_df = pd.DataFrame(
            [{"State": k, "Projects": v} for k, v in sorted(state_counts.items())]
        )
        st.dataframe(state_df, use_container_width=True, hide_index=True)

        st.markdown(f"**Unique states:** {len(state_counts)}")
        st.markdown(f"**Total selected QEI:** {fmt_millions(total_qei_selected)}")
        st.markdown(
            f"**Max total QEI constraint:** {fmt_millions(constraints_used.get('max_total_qei_m', 0) * 1_000_000)}"
        )

# ---------------------------------------------------------------------------
# Optimizer methodology note
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("Optimizer methodology note"):
    st.markdown(result.methodology_note)
    st.markdown(f"**Search iterations completed:** {result.iterations}")
