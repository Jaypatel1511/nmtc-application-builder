"""Pipeline Analyzer — full intelligence report for a project pipeline."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import io
import tempfile

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    ACCENT,
    PRIMARY,
    SUCCESS,
    WARNING,
    DANGER,
    MUTED,
    fmt_millions,
    fmt_pct,
    get_or_create_app,
    apply_theme,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
apply_theme()
st.title("📋 Pipeline Analyzer")
st.markdown(
    "Run a comprehensive intelligence analysis on your NMTC project pipeline — "
    "distress concentration, geographic diversity, sector mix, and impact projections."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — data source selection
# ---------------------------------------------------------------------------
_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "templates", "pipeline_template.xlsx"
)

with st.sidebar:
    st.header("Data source")

    _tmpl_path = os.path.abspath(_TEMPLATE_PATH)
    if os.path.exists(_tmpl_path):
        with open(_tmpl_path, "rb") as _f:
            st.download_button(
                label="📥 Download blank template (Excel)",
                data=_f.read(),
                file_name="nmtc_pipeline_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Pre-formatted with dropdowns and 5 example rows. Edit, save as CSV, then upload.",
                use_container_width=True,
            )

    data_source = st.radio(
        "Choose pipeline source",
        ["Use sample data (20 projects)", "Upload your own CSV"],
        index=0,
    )

    uploaded_file = None
    if data_source == "Upload your own CSV":
        uploaded_file = st.file_uploader(
            "Upload your pipeline file (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
        )
        st.caption(
            "Accepted formats: .csv, .xlsx, .xls — "
            "Required columns: project_id, project_name, state, city, sector, "
            "project_type, qei_millions, total_project_cost_millions, jobs_created. "
            "Optional: jobs_retained, affordable_units, commercial_sqft, "
            "distress_level, urban_rural, census_tract, address, "
            "minority_owned, women_owned, notes."
        )

    st.markdown("---")
    st.caption(
        "The sample pipeline includes 20 realistic projects across 12 states, "
        "pre-enriched with eligibility and distress data — no API calls needed."
    )


# ---------------------------------------------------------------------------
# Helper: load pipeline
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_sample_pipeline(n: int = 20) -> Pipeline:
    return Pipeline.sample(n=n)


def load_uploaded_pipeline(file_bytes: bytes, filename: str) -> Pipeline:
    """Parse an uploaded CSV or Excel file into a Pipeline."""
    ext = filename.rsplit(".", 1)[-1].lower()
    buf = io.BytesIO(file_bytes)

    if ext == "csv":
        df = pd.read_csv(buf)
    elif ext in ("xlsx", "xls"):
        try:
            df = pd.read_excel(buf, sheet_name="Pipeline")
        except Exception:
            buf.seek(0)
            df = pd.read_excel(buf, sheet_name=0)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    # Map user-friendly template column names to the internal names Pipeline expects.
    # Multiply "*_millions" columns by 1e6 before renaming so raw-dollar CSVs pass through unchanged.
    for mil_col, raw_col in (
        ("qei_millions", "qei_request"),
        ("total_project_cost_millions", "total_project_cost"),
    ):
        if mil_col in df.columns:
            df[mil_col] = pd.to_numeric(df[mil_col], errors="coerce").fillna(0) * 1_000_000
            df = df.rename(columns={mil_col: raw_col})

    for src, dst in (
        ("jobs_created", "expected_jobs_created"),
        ("jobs_retained", "expected_jobs_retained"),
        ("affordable_units", "expected_units_built"),
        ("commercial_sqft", "expected_sq_ft"),
    ):
        if src in df.columns:
            df = df.rename(columns={src: dst})

    # Supply defaults for columns required by Pipeline.from_csv() but absent in the template.
    if "qalicb_name" not in df.columns:
        df["qalicb_name"] = df.get("project_name", "")
    if "address" not in df.columns:
        df["address"] = ""
    if "qlici_amount" not in df.columns and "qei_request" in df.columns:
        df["qlici_amount"] = df["qei_request"]

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="") as tmp:
        df.to_csv(tmp, index=False)
        tmp_path = tmp.name

    return Pipeline.from_csv(tmp_path)


# ---------------------------------------------------------------------------
# Main — run analysis
# ---------------------------------------------------------------------------
run_clicked = st.button("▶  Run Analysis", type="primary", use_container_width=False)

if run_clicked:
    # --- Load pipeline ---
    pipeline = None
    if data_source == "Upload your own CSV":
        if uploaded_file is None:
            st.error("Please upload a CSV file first.")
            st.stop()
        try:
            with st.spinner("Reading CSV…"):
                pipeline = load_uploaded_pipeline(uploaded_file.read(), uploaded_file.name)
            st.success(f"Loaded {len(pipeline)} projects from {uploaded_file.name}")
        except Exception as exc:
            st.error(f"Failed to read CSV: {exc}")
            st.stop()
    else:
        with st.spinner("Loading sample pipeline…"):
            pipeline = load_sample_pipeline(n=20)

    # --- Create / update Application in session ---
    try:
        with st.spinner("Running full pipeline analysis — this may take a moment…"):
            app = get_or_create_app(pipeline=pipeline)
            analysis = app.analyze()
        st.session_state["analysis"] = analysis
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

# ---------------------------------------------------------------------------
# Display results (if analysis available in session)
# ---------------------------------------------------------------------------
if "analysis" not in st.session_state:
    st.info("Click **Run Analysis** to begin.")
    st.stop()

analysis = st.session_state["analysis"]
pr = analysis.pipeline_result
d = analysis.distress_analysis
g = analysis.geographic_analysis
s = analysis.sector_analysis
i = analysis.impact_summary
rs = analysis.readiness_score

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs(["Overview", "Distress", "Geographic", "Sector", "Impact"])

# =============================================================================
# TAB 0 — Overview
# =============================================================================
with tabs[0]:
    st.subheader("Pipeline overview")

    c1, c2, c3, c4 = st.columns(4)

    total_qei = pr.total_qei_request
    eligible_pct = pr.eligibility_pct
    readiness = rs.overall_score
    grade = rs.grade

    c1.metric("Total projects", pr.total_projects)
    c2.metric("Total QEI requested", fmt_millions(total_qei))
    c3.metric("Readiness score", f"{readiness:.1f} / 100", delta=grade)
    c4.metric("NMTC-eligible", fmt_pct(eligible_pct))

    st.markdown("---")

    # CDE info
    left, right = st.columns(2)
    with left:
        st.markdown(f"**CDE:** {analysis.cde_name}")
        st.markdown(f"**Application round:** {analysis.application_round}")
        st.markdown(f"**Requested allocation:** {fmt_millions(analysis.requested_allocation)}")
        st.markdown(f"**Analyzed at:** {analysis.analyzed_at[:19]}")

    with right:
        st.markdown("**Validation results**")
        for vr in analysis.validation_results:
            icon = "✅" if vr.passed else "❌"
            st.markdown(f"{icon} `{vr.check_name}`")
            if vr.warnings:
                for w in vr.warnings:
                    st.caption(f"  ⚠️ {w}")
            if vr.issues:
                for iss in vr.issues:
                    st.caption(f"  🚨 {iss}")

    # Readiness breakdown
    st.markdown("---")
    st.markdown("**Readiness score breakdown**")
    breakdown = rs.component_scores if hasattr(rs, "component_scores") else {}
    if breakdown:
        breakdown_df = pd.DataFrame(
            [
                {"Dimension": k.replace("_", " ").title(), "Score": round(v, 1)}
                for k, v in breakdown.items()
            ]
        )
        fig, ax = plt.subplots(figsize=(8, 3))
        bars = ax.barh(breakdown_df["Dimension"], breakdown_df["Score"], color=PRIMARY)
        for bar, score in zip(bars, breakdown_df["Score"]):
            ax.text(score + 1, bar.get_y() + bar.get_height() / 2, f"{score:.1f}",
                    va="center", ha="left", fontsize=9)
        ax.set_xlim(0, 115)
        ax.set_xlabel("Score (0–100)")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.markdown(f"**Overall readiness grade:** `{grade}` ({readiness:.1f}/100)")

# =============================================================================
# TAB 1 — Distress
# =============================================================================
with tabs[1]:
    st.subheader("Distress concentration")

    deep_severe_pct = d.get("pct_deep_or_severe", 0.0)
    lic_pct = d.get("pct_lic", 0.0)
    non_lic_pct = d.get("pct_non_lic", 0.0)
    native_pct = d.get("pct_native_area", 0.0)
    meets_target = d.get("meets_target_threshold", False)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Deep / Severe distress",
        fmt_pct(deep_severe_pct),
        delta="Meets target" if meets_target else "Below target",
        delta_color="normal" if meets_target else "inverse",
    )
    c2.metric("LIC (standard)", fmt_pct(lic_pct))
    c3.metric("Native area", fmt_pct(native_pct))

    st.markdown("---")
    left, right = st.columns([1, 1])

    with left:
        # Pie chart — distress distribution
        labels = ["Deep / Severe", "LIC (standard)", "Non-LIC"]
        values = [deep_severe_pct, lic_pct, non_lic_pct]
        # Normalise just in case
        total = sum(values) or 1.0
        values = [v / total for v in values]

        fig_pie = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=[PRIMARY, ACCENT, MUTED],
                textinfo="label+percent",
                hovertemplate="%{label}: %{percent}<extra></extra>",
            )
        )
        fig_pie.update_layout(
            title="QEI distribution by distress level",
            margin=dict(l=0, r=0, t=40, b=0),
            height=320,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with right:
        st.markdown("**Benchmarks vs. historical winners**")
        winner_p25 = 0.72
        winner_median = 0.82
        winner_p75 = 0.91

        bench_data = {
            "Metric": [
                "Your pipeline",
                "Winner p25",
                "Winner median",
                "Winner p75",
            ],
            "Deep/Severe %": [
                deep_severe_pct * 100,
                winner_p25 * 100,
                winner_median * 100,
                winner_p75 * 100,
            ],
        }
        _bench_colors = {
            "Your pipeline": ACCENT,
            "Winner p25": "#aab7d4",
            "Winner median": "#6680b3",
            "Winner p75": PRIMARY,
        }
        fig_bench, ax_bench = plt.subplots(figsize=(6, 3.5))
        _bars = ax_bench.bar(
            bench_data["Metric"],
            bench_data["Deep/Severe %"],
            color=[_bench_colors[m] for m in bench_data["Metric"]],
        )
        for bar in _bars:
            ax_bench.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9,
            )
        ax_bench.set_ylim(0, 105)
        ax_bench.set_ylabel("% of QEI")
        ax_bench.tick_params(axis="x", rotation=10)
        ax_bench.spines[["top", "right"]].set_visible(False)
        fig_bench.tight_layout()
        st.pyplot(fig_bench, use_container_width=True)
        plt.close(fig_bench)

        vs_hist = d.get("vs_historical_winners", "N/A")
        st.markdown(f"**Historical ranking:** {vs_hist}")

# =============================================================================
# TAB 2 — Geographic
# =============================================================================
with tabs[2]:
    st.subheader("Geographic diversity")

    states_count = g.get("states_count", 0)
    hhi = g.get("hhi", 0)
    conc_label = g.get("geographic_concentration_label", "N/A")
    rural_pct = g.get("rural_pct", 0.0)
    urban_pct = g.get("urban_pct", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("States represented", states_count)
    c2.metric("Geographic HHI", f"{hhi:,.0f}")
    c3.metric("Concentration level", conc_label)
    c4.metric("Rural share", fmt_pct(rural_pct))

    st.markdown("---")

    # State-level bar chart from pipeline DataFrame
    app_obj = st.session_state.get("app")
    if app_obj and app_obj.pipeline:
        df = app_obj.pipeline.to_dataframe()
        state_qei = (
            df.groupby("state")["qei_request"]
            .sum()
            .reset_index()
            .rename(columns={"qei_request": "QEI ($)"})
            .sort_values("QEI ($)", ascending=False)
        )
        state_qei["QEI ($M)"] = state_qei["QEI ($)"] / 1_000_000

        fig_states, ax_states = plt.subplots(figsize=(9, 4))
        ax_states.bar(state_qei["state"], state_qei["QEI ($M)"], color=PRIMARY)
        for idx, val in enumerate(state_qei["QEI ($M)"]):
            ax_states.text(idx, val + 0.05, f"{val:.1f}", ha="center", va="bottom", fontsize=8)
        ax_states.set_xlabel("State")
        ax_states.set_ylabel("QEI ($ millions)")
        ax_states.set_title("QEI by state")
        ax_states.tick_params(axis="x", rotation=45)
        ax_states.spines[["top", "right"]].set_visible(False)
        fig_states.tight_layout()
        st.pyplot(fig_states, use_container_width=True)
        plt.close(fig_states)

    # Urban / rural split
    left, right = st.columns(2)
    with left:
        fig_ur = go.Figure(
            go.Pie(
                labels=["Urban", "Rural"],
                values=[urban_pct, rural_pct],
                hole=0.4,
                marker_colors=[PRIMARY, ACCENT],
                textinfo="label+percent",
                hovertemplate="%{label}: %{percent}<extra></extra>",
            )
        )
        fig_ur.update_layout(
            title="Urban / Rural QEI split",
            margin=dict(l=0, r=0, t=40, b=0),
            height=280,
        )
        st.plotly_chart(fig_ur, use_container_width=True)

    with right:
        st.markdown("**Geographic benchmarks**")
        st.markdown(
            f"- Winner median states: **7**  |  Your pipeline: **{states_count}**"
        )
        st.markdown(
            f"- Winner mean HHI: **620**  |  Your pipeline: **{hhi:,.0f}**"
        )
        st.markdown(
            f"- Winner rural mean: **18%**  |  Your pipeline: **{fmt_pct(rural_pct)}**"
        )
        msa_count = g.get("msa_count", "N/A")
        st.markdown(f"- MSAs represented: **{msa_count}**")

# =============================================================================
# TAB 3 — Sector
# =============================================================================
with tabs[3]:
    st.subheader("Sector mix")

    sectors_count = s.get("sectors_represented", 0)
    dominant = s.get("dominant_sector", "N/A")
    high_priority_pct = s.get("high_priority_pct", 0.0)
    diversity_score = s.get("sector_diversity_score", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sectors represented", sectors_count)
    c2.metric("Dominant sector", dominant.replace("_", " ").title())
    c3.metric("High-priority sector %", fmt_pct(high_priority_pct))
    c4.metric("Diversity score", f"{diversity_score:.1f} / 100")

    st.markdown("---")

    # Sector bar chart by QEI from pipeline DataFrame
    app_obj = st.session_state.get("app")
    if app_obj and app_obj.pipeline:
        df = app_obj.pipeline.to_dataframe()
        sector_qei = (
            df.groupby("sector")["qei_request"]
            .sum()
            .reset_index()
            .rename(columns={"qei_request": "QEI ($)"})
            .sort_values("QEI ($)", ascending=True)
        )
        sector_qei["QEI ($M)"] = sector_qei["QEI ($)"] / 1_000_000
        sector_qei["sector_label"] = sector_qei["sector"].str.replace("_", " ").str.title()

        fig_sector, ax_sector = plt.subplots(figsize=(8, 4))
        ax_sector.barh(sector_qei["sector_label"], sector_qei["QEI ($M)"], color=PRIMARY)
        for idx, val in enumerate(sector_qei["QEI ($M)"]):
            ax_sector.text(val + 0.05, idx, f"{val:.1f}", ha="left", va="center", fontsize=9)
        ax_sector.set_xlabel("QEI ($ millions)")
        ax_sector.set_title("QEI allocation by sector")
        ax_sector.spines[["top", "right"]].set_visible(False)
        fig_sector.tight_layout()
        st.pyplot(fig_sector, use_container_width=True)
        plt.close(fig_sector)

    # Sector QEI share breakdown
    sector_breakdown = s.get("sector_breakdown", {})
    if sector_breakdown:
        st.markdown("**QEI share by sector**")
        share_df = pd.DataFrame(
            [
                {
                    "Sector": k.replace("_", " ").title(),
                    "QEI Share (%)": round(v.get("pct", 0) * 100, 1),
                    "Projects": v.get("count", 0),
                    "Priority": v.get("priority", "N/A").title(),
                }
                for k, v in sorted(sector_breakdown.items(), key=lambda x: -x[1].get("pct", 0))
            ]
        )
        st.dataframe(share_df, use_container_width=True, hide_index=True)

# =============================================================================
# TAB 4 — Impact
# =============================================================================
with tabs[4]:
    st.subheader("Impact projections")

    total_jobs = i.get("total_jobs_created", 0)
    total_retained = i.get("total_jobs_retained", 0)
    jpm = i.get("jobs_per_million_qei", 0.0)
    benchmark_label = i.get("vs_historical_benchmarks", "N/A")
    total_units = i.get("total_units_built", 0)
    total_sqft = i.get("total_sq_ft", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total jobs created", f"{total_jobs:,}")
    c2.metric("Jobs retained", f"{total_retained:,}")
    c3.metric("Jobs per $1MM QEI", f"{jpm:.1f}")
    c4.metric("Benchmark tier", benchmark_label)

    if total_units:
        st.metric("Affordable housing units", f"{total_units:,}")

    st.markdown("---")

    # Jobs benchmark gauge
    left, right = st.columns([1, 1])

    with left:
        # Compare to winner benchmarks
        benchmarks = {
            "Your pipeline": jpm,
            "Winner p25": 6.0,
            "Winner median": 10.0,
            "Winner p75": 18.0,
            "Winner top 10%": 28.0,
        }
        bench_df = pd.DataFrame(
            [{"Metric": k, "Jobs / $1MM QEI": v} for k, v in benchmarks.items()]
        )
        _jpm_colors = {
            "Your pipeline": ACCENT,
            "Winner p25": "#c8d3e8",
            "Winner median": "#7b96c9",
            "Winner p75": "#3d6ab0",
            "Winner top 10%": PRIMARY,
        }
        fig_jpm, ax_jpm = plt.subplots(figsize=(7, 3.5))
        _jpm_bars = ax_jpm.bar(
            bench_df["Metric"],
            bench_df["Jobs / $1MM QEI"],
            color=[_jpm_colors[m] for m in bench_df["Metric"]],
        )
        for bar in _jpm_bars:
            ax_jpm.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9,
            )
        ax_jpm.set_ylabel("Jobs / $1MM QEI")
        ax_jpm.set_title("Jobs/$1MM QEI vs. winner benchmarks")
        ax_jpm.tick_params(axis="x", rotation=15)
        ax_jpm.spines[["top", "right"]].set_visible(False)
        fig_jpm.tight_layout()
        st.pyplot(fig_jpm, use_container_width=True)
        plt.close(fig_jpm)

    with right:
        st.markdown("**Impact summary**")
        st.markdown(f"- Total jobs created: **{total_jobs:,}**")
        st.markdown(f"- Total jobs retained: **{total_retained:,}**")
        if total_units:
            st.markdown(f"- Affordable units: **{total_units:,}**")
        if total_sqft:
            st.markdown(f"- Commercial sq ft: **{total_sqft:,.0f}**")
        st.markdown(f"- Jobs / $1MM QEI: **{jpm:.1f}**")
        st.markdown(f"- Historical benchmark: **{benchmark_label}**")

        # Deal economics waterfall + summary
        econ = analysis.deal_economics
        if econ or pr.total_project_cost > 0:
            st.markdown("---")
            MID_BLUE = "#2E6DB4"
            LIGHT_BLUE = "#9DC3E6"
            total_pc = pr.total_project_cost
            qei_val = econ.get("total_qei", pr.total_qei_request) if econ else pr.total_qei_request
            nmtcs_val = econ.get("total_nmtcs", qei_val * 0.39) if econ else qei_val * 0.39
            equity_val = econ.get("total_investor_equity", nmtcs_val * 0.83) if econ else nmtcs_val * 0.83
            subsidy_val = econ.get("total_net_subsidy", qei_val * 0.95) if econ else qei_val * 0.95

            if total_pc > 0:
                fig_wf = go.Figure(
                    go.Waterfall(
                        measure=["absolute", "absolute", "absolute", "absolute", "absolute"],
                        x=["Total<br>Project Cost", "QEI", "Federal NMTC<br>(39%)", "Investor<br>Equity", "Net Subsidy"],
                        y=[total_pc / 1e6, qei_val / 1e6, nmtcs_val / 1e6, equity_val / 1e6, subsidy_val / 1e6],
                        text=[f"${v / 1e6:.1f}M" for v in [total_pc, qei_val, nmtcs_val, equity_val, subsidy_val]],
                        textposition="outside",
                        increasing={"marker": {"color": PRIMARY}},
                        decreasing={"marker": {"color": DANGER}},
                        connector={"visible": False},
                    )
                )
                fig_wf.update_layout(
                    title="Deal economics waterfall",
                    yaxis_title="$ Millions",
                    height=380,
                    margin=dict(l=0, r=20, t=40, b=0),
                    showlegend=False,
                )
                st.plotly_chart(fig_wf, use_container_width=True)

            st.markdown("**Deal economics**")
            st.markdown(f"- Total NMTCs: **{fmt_millions(nmtcs_val)}**")
            st.markdown(f"- Investor equity: **{fmt_millions(equity_val)}**")
            st.markdown(f"- Net subsidy: **{fmt_millions(subsidy_val)}**")
