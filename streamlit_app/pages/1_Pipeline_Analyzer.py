"""Pipeline Analyzer — full intelligence report for a project pipeline.

IMPORTANT: do not use `i` as a loop variable anywhere in this file.
`i` is reserved for `i = analysis.impact_summary` (a dict) used in Tab 4.
Use `idx` for all enumerate indexes.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.core.upload_handler import load_uploaded_pipeline

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nmtcapp.core.sample_identity import SampleDataError
from nmtcapp.renderers._disclosure import join_truncated
from nmtcapp.tables.distress_table import LIC_ROW_LABEL, NATIVE_AREA_ROW_LABEL
from nmtcapp.data.schema import GRADE_THRESHOLDS, TARGET_DISTRESS_THRESHOLDS
from nmtcapp.data.historical_awards import (
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
)
from nmtcapp.renderers._question_25 import Q25_QEI_BASIS_CLAUSE, q25_basis_note
from nmtcapp.renderers._question_22 import (
    Q22_METRO_LABEL, Q22_NON_METRO_LABEL, Q22_NON_METRO_METRIC_LABEL,
    Q22_UNDETERMINED_LABEL, q22_basis_note, q22_undetermined_caveat,
)
from utils import (
    fmt_millions,
    fmt_pct,
    get_or_create_app,
    apply_theme,
    _scoring_attrs_only,
    metric_classification,
)
from chart_style import (
    apply_matplotlib_theme, style_matplotlib_axes, style_plotly_fig,
    bar_gradient, PLOTLY_CONFIG, PLOTLY_LAYOUT,
    NAVY, BLUE, MID_BLUE, LIGHT_BLUE, ACCENT, SUCCESS, DANGER, NEUTRAL,
    TEXT_DARK, TEXT_MUTED, TEXT_LIGHT, PANEL_BG, GRID, BORDER,
)

apply_matplotlib_theme()

# ---------------------------------------------------------------------------
# Provenance for the two geographic reference points (B3)
# ---------------------------------------------------------------------------
#: Rendered directly beneath the two WINNER_GEOGRAPHIC_PATTERNS figures on this
#: page. It exists because those two numbers used to be labelled "Winner
#: median states" and "Winner mean HHI" with nothing on the screen saying whose
#: numbers they were. The docstring in benchmarks.py is in the source; this is
#: the artifact. Kept deliberately short -- a caption a CDE will actually read
#: beats a paragraph it will scroll past.
_GEO_REFERENCE_METHODOLOGY = (
    "Both reference points are THIS TOOL'S OWN HOUSE ESTIMATES, not CDFI Fund "
    "figures and not measurements of past Allocatees. The Fund does publish "
    "Allocatee-level deployment data (NMTC Public Data Release 2003-2023, "
    "released 7 August 2026), but it reports QLICI-dollar-denominated REALIZED "
    "DEPLOYMENT, while these are QEI-denominated APPLICATION-PIPELINE figures; "
    "this package has not reconciled the two. Treat them as a prompt about "
    "your own pipeline, not as a bar you must clear."
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
    os.path.dirname(__file__), "..", "..", "nmtcapp", "templates", "pipeline_template.xlsx"
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
                help="Pre-formatted with dropdowns and sample rows. Fill in your projects, save, and upload the .xlsx directly.",
                use_container_width=True,
            )

    data_source = st.radio(
        "Choose pipeline source",
        ["Use sample data (20 projects)", "Upload your own file"],
        index=0,
    )

    uploaded_file = None
    if data_source == "Upload your own file":
        uploaded_file = st.file_uploader(
            "Upload your pipeline file (CSV or Excel v1.1 template)",
            type=["csv", "xlsx", "xls"],
        )
        st.caption(
            "**Excel v1.1 template** (recommended): upload the downloaded `.xlsx` file "
            "directly — all column mapping is handled automatically. Include the "
            "'CDE Profile' sheet for full scoring. "
            "**CSV files**: use the snake_case column names from `pipeline_template.csv` "
            "(project_id, project_name, qalicb_name, address, city, state, sector, "
            "project_type, total_project_cost, qei_request, qlici_amount, "
            "expected_jobs_created). Values must be raw dollars, not millions. "
            "UTF-8 and Windows-1252 (Excel default) encodings are both accepted."
        )

    st.markdown("---")
    st.caption(
        "The sample pipeline includes 20 realistic projects across 19 states, "
        "pre-enriched with eligibility and distress data — no API calls needed."
    )


# ---------------------------------------------------------------------------
# Helper: load pipeline
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_sample_pipeline(n: int = 20) -> Pipeline:
    return Pipeline.sample(n=n)


# ---------------------------------------------------------------------------
# Graceful-degradation: map missing CDE attrs to their default impact
# ---------------------------------------------------------------------------
_CDE_DEFAULTS_DISCLOSURE: dict[str, str] = {
    "products_below_market_pct":            "0 (no Product Flexibility credit from below-market pct)",
    "products_flexible_indicia_count":      "0 (no Product Flexibility credit from indicia count)",
    "pipeline_pct_identified":              "0.65 (moderate Pipeline Credibility credit)",
    "has_own_capital_at_risk":              "False (no Track Record bonus)",
    "prior_award_count":                    "0 (no Track Record Strength credit)",
    "years_in_operation":                   "0 (no Track Record Strength credit)",
    "track_record_pipeline_alignment_pct":  "0 (no Track Record Alignment credit)",
    "track_record_deployment_pct":          "0 (no Track Record Alignment credit)",
    "pct_persistent_poverty":               "computed from pipeline flags or 0",
    "pct_us_territories":                   "computed from pipeline flags or 0",
    "has_quantified_outcomes":              "True (assumed)",
    "has_third_party_validation":           "False (no Outcomes Quality bonus)",
    "lic_board_representation_pct":         "0 (no Community Accountability credit)",
    "has_community_engagement_track_record":"False (no Community Accountability bonus)",
    "dbc_focus_years":                      "0 (no DBC Priority Points)",
    "dbc_dollar_volume_pct":                "computed from pipeline flags or 0",
    "unrelated_entities_pct":               "computed from pipeline flags or 0",
}


def _summarise_cde_defaults(cde_extra: dict | None) -> dict[str, str]:
    """Return {key: default_note} for scoring attrs that will rely on defaults."""
    provided = set(cde_extra.keys()) if cde_extra else set()
    return {
        k: v
        for k, v in _CDE_DEFAULTS_DISCLOSURE.items()
        if k not in provided
        # Suppress pipeline-computed ones if that data is available (handled in loader)
    }


# ---------------------------------------------------------------------------
# Main — run analysis
# ---------------------------------------------------------------------------
run_clicked = st.button("▶  Run Analysis", type="primary", use_container_width=False)

if run_clicked:
    pipeline = None
    _cde_extra: dict | None = None
    _is_user_upload = data_source == "Upload your own file"

    if _is_user_upload:
        if uploaded_file is None:
            st.error("Please upload a file first.")
            st.stop()
        try:
            with st.spinner("Reading file…"):
                pipeline, _cde_extra = load_uploaded_pipeline(
                    uploaded_file.read(), uploaded_file.name
                )
            # Strip identity and blanks BEFORE reporting what was provided.
            # _summarise_cde_defaults reported "nothing missing" on a template
            # upload because the sheet arrived fully populated with the sample
            # CDE's values — affirmatively telling the user their own data had
            # been read. Whatever this reports has to be true of what actually
            # reaches the scorer, so it must see the same dict the scorer does.
            _cde_extra = _scoring_attrs_only(_cde_extra or {}, is_demo=False)
            _missing_cde = _summarise_cde_defaults(_cde_extra)
            st.success(f"Loaded {len(pipeline)} projects from {uploaded_file.name}")
            # THE COLUMN THE CDE DID NOT SUPPLY (1.3.0 S3). Read off the flag
            # each project carries, not re-derived from qlici_amount ==
            # qei_request — the two are equal in every fixture this package
            # ships and in plenty of real pipelines.
            _no_qlici = [p.project_id for p in pipeline if not p.qlici_amount_supplied]
            if _no_qlici:
                st.warning(
                    f"**No `qlici_amount` column in this file** — "
                    f"{len(_no_qlici)} of {len(pipeline)} projects. Each "
                    "project's QEI request was used in its place so the "
                    "pipeline could load, but that is not your QLICI amount "
                    "and the document does not present it as one: Appendix A's "
                    "**Total QLICI ($)** reads *not supplied [CDE TO "
                    "COMPLETE]*, and the QLICI ≤ QEI consistency check is "
                    "reported as not checkable rather than passed. Add a "
                    "`qlici_amount` column and re-upload before filing."
                )
            if _missing_cde:
                st.info(
                    "Some CDE Profile fields were not provided — the scorer will apply "
                    "conservative defaults for those sub-scores:\n\n"
                    + "\n".join(f"- **{k}** — not provided, sub-score defaulted to {v}"
                                for k, v in _missing_cde.items())
                )
        except SampleDataError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            st.error(f"Failed to read file: {exc}")
            st.stop()
    else:
        with st.spinner("Loading sample pipeline…"):
            pipeline = load_sample_pipeline(n=20)

    try:
        with st.spinner("Running full pipeline analysis — this may take a moment…"):
            app = get_or_create_app(
                pipeline=pipeline,
                is_demo=not _is_user_upload,
                cde_extra=_cde_extra,
            )
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

_degraded = getattr(pr, "eligibility_data_status", "ok") != "ok"
if _degraded:
    st.error(
        "**Eligibility data unavailable** — "
        f"{getattr(pr, 'eligibility_data_error', None) or 'reason unknown'}. "
        "Eligibility and distress figures are unverified, and the readiness "
        "score is partial: computed without eligibility verification "
        "(4 of 6 components)."
    )
elif getattr(pr, "unverified_project_ids", None):
    st.warning(
        f"**{len(pr.unverified_project_ids)} project(s) could not be "
        "location-verified** and remain unverified (no census tract "
        "assigned): " + join_truncated(pr.unverified_project_ids)
    )

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
    # AN F RENDERED WITH AN UP ARROW, AND delta_color DID NOT REMOVE IT
    # (1.5.1 T4, completed by the 1.5.1 audit F1). T4 found that
    # st.metric(delta="Grade F") drew a GREEN UP arrow and fixed it with
    # delta_color="off", stating the result was GRAY/NONE. Executed against
    # the pinned Streamlit, "off" yields GRAY/**UP** — Streamlit computes
    # DIRECTION from the delta's sign before it consults delta_color, and
    # delta_color only ever picks a colour. The F kept pointing up, greyer.
    # The grade is no longer a delta at all. See utils.metric_classification.
    metric_classification(
        c3,
        "Readiness score" + (" (partial)" if _degraded else ""),
        f"{readiness:.1f} / 100",
        f"Grade {grade}",
    )
    c4.metric("NMTC-eligible", "Unverified" if _degraded else fmt_pct(eligible_pct))

    st.markdown("---")

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

    # --- H: Readiness score breakdown ---
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

        # THREE HAND-TYPED NUMBERS, TWO OF THEM TWINS OF A LIVE CONSTANT
        # (1.5.2 T4). This ladder read ``50 / 70 / 85``. The 70 and the 85 are
        # GRADE_THRESHOLDS["B"] and ["A"] re-typed, and the 50 was an ORPHAN --
        # it is not a grade cut at all (C is 55, D is 40), so the colour
        # boundary a CDE saw on this chart matched no band this package
        # defines anywhere.
        #
        # tests/pinned_constants.txt's WAIVE row for GRADE_THRESHOLDS has
        # documented these twins since 1.5.1 and closed with "no gate reads
        # either". One does now: tests/test_grade_threshold_twins.py.
        #
        # The ladder is now one statement. Deleting GRADE_THRESHOLDS cannot
        # leave this chart drawing bands that no longer exist, and re-basing
        # the grades moves the colours with them.
        _A = GRADE_THRESHOLDS["A"]
        _B = GRADE_THRESHOLDS["B"]
        _C = GRADE_THRESHOLDS["C"]

        def _score_color(score: float) -> str:
            if score < _C:
                return DANGER
            if score < _B:
                return ACCENT
            if score < _A:
                return MID_BLUE
            return SUCCESS

        bar_colors = [_score_color(s) for s in breakdown_df["Score"]]

        fig, ax = plt.subplots(figsize=(8, max(3, len(breakdown_df) * 0.55)))
        bars = ax.barh(breakdown_df["Dimension"], breakdown_df["Score"], color=bar_colors, height=0.6)
        # "COMPETITIVE" WAS A CLAIM ABOUT THE FUND WITH NO FUND REFERENT
        # (1.5.2 T4). This line was drawn at a hardcoded 70 and labelled
        # "Competitive (70)" — the same defect shape as the false attribution
        # T2 removed from schema.py, except rendered to a CDE instead of
        # hidden in a comment. The CDFI Fund publishes no readiness score and
        # no grade, so it publishes no competitiveness bar on this axis;
        # nothing about 70 makes an application competitive, and a dashed
        # reference line beside a chart of six sub-scores is exactly where a
        # reader takes a word like that literally.
        #
        # What survives is the true statement: 70 is where THIS TOOL's grade B
        # begins. Interpolated, so the line and the label cannot drift from
        # the constant or from each other.
        ax.axvline(x=_B, color=NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.8)
        ax.text(_B + 0.5, ax.get_ylim()[1] * 0.98,
                f"This tool's grade-B cut ({_B:.0f})\nnot a CDFI Fund threshold",
                color=NEUTRAL, fontsize=8, va="top", ha="left")
        for bar, score in zip(bars, breakdown_df["Score"]):
            ax.text(score + 1, bar.get_y() + bar.get_height() / 2, f"{score:.1f}",
                    va="center", ha="left", fontsize=9, color=TEXT_DARK)
        ax.set_xlim(0, 118)
        style_matplotlib_axes(ax, xlabel="Score (0–100)")
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

    # THE FIFTH SURFACE (1.3.0 B1 ride-along).
    #
    # 1.3.0 S4 swept the four GENERATED DOCUMENT renderers — markdown, Word,
    # PDF, Excel — for a distress share printed with no denominator in its
    # label. This screen carried the same defect and was not in that sweep,
    # because the sweep was scoped to nmtcapp/renderers and nmtcapp/sections
    # and this file is in streamlit_app/, a package that produces no filed
    # artifact and so was read as out of scope. A CDE reads a figure off a
    # screen and types it into a form exactly the way it reads one off a
    # workbook; producing no file is not the same as reaching no filing.
    #
    # AND IT WAS WORSE HERE THAN ON THE FOUR. The workbook printed a bare
    # share. This printed a bare share under a VERDICT — "Meets target" /
    # "Below target" — against TARGET_DISTRESS_THRESHOLDS, which data/schema.py
    # labels a HOUSE HEURISTIC in capitals and warns must not be presented as a
    # Fund figure. The `nmtcapp analyze` block prints the same comparison and
    # has said "this tool's own band — not a CDFI Fund threshold" since 1.2.0.
    # This one said "target", unqualified, next to a percentage a reader has
    # every reason to believe is the Question 25 answer.
    _target = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]
    c1, c2, c3 = st.columns(3)
    # A VERDICT IS NOT A MOVEMENT EITHER (1.5.1 audit, F1 sweep). This passed
    # "Meets/Below this tool's own >=X% band" as `delta`. Neither string
    # carries a sign, so BOTH rendered with an UP arrow — "Below ... band"
    # arrived in red, pointing up. Same defect as the readiness grade above,
    # eleven lines down, and not on T4's list.
    metric_classification(
        c1,
        f"Deep / Severe distress ({Q25_QEI_BASIS_CLAUSE})",
        fmt_pct(deep_severe_pct),
        (f"{'Meets' if meets_target else 'Below'} this tool's own "
         f"\u2265{_target:.0%} band"),
        tone="good" if meets_target else "bad",
        help="NOT a CDFI Fund threshold, and NOT an answer to Question 25. "
             f"The {_target:.0%} band is this tool's own heuristic. The Fund's "
             "distress commitments are measured on QLICIs, not on QEI, and "
             "every share on this screen is a share of QEI. See the basis "
             "note below.",
    )
    # THE SIXTH SURFACE, AND THE LABEL IS CARRIED (1.3.1 F2).
    #
    # 1.3.0's B1 ride-along put Q25_QEI_BASIS_CLAUSE on the Deep/Severe metric
    # above and stopped there. These two carried the same class of defect one
    # column across: `st.metric("LIC (standard)")` and
    # `st.metric("Native area (CDE-declared)")` print a share of QEI with no
    # denominator on its face, beside a metric that names its own. Every
    # generated document names the basis on all three — "QEI in LIC (Standard
    # Eligible) Tracts" — and a CDE reads a figure off a screen and types it
    # into a form exactly the way it reads one off a workbook.
    #
    # The wording is IMPORTED, not paraphrased. What ships in the documents
    # was hostile-audited across three rounds; a metric label written fresh
    # for this screen has not been, and a paraphrase of a denominator
    # disclosure is a new claim about the denominator.
    c2.metric(LIC_ROW_LABEL, fmt_pct(lic_pct))
    # CDE-DECLARED, and the label says so. This share comes from the
    # `native_area` column the CDE fills in, never from nmtc-mapper (which
    # dropped is_nmtc_native_area at 0.5.0), and the CDFI Fund publishes no
    # tract-keyed Native Areas resource to check it against. See
    # NATIVE_AREA_BASIS in nmtcapp/tables/distress_table.
    c3.metric(NATIVE_AREA_ROW_LABEL, fmt_pct(native_pct),
              help="This tool cannot verify a Native Area. The figure is the "
                   "share of QEI in projects the CDE itself declared as NMTC "
                   "Native Areas on its pipeline submission.")

    st.markdown("---")
    left, right = st.columns([1, 1])

    with left:
        # --- A: QEI distribution donut ---
        labels = ["Deep / Severe", "LIC (standard)", "Non-LIC"]
        values = [deep_severe_pct, lic_pct, non_lic_pct]
        total_v = sum(values) or 1.0
        values = [v / total_v for v in values]
        center_text = f"{fmt_millions(total_qei)}<br>Total QEI"

        fig_pie = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                marker_colors=[NAVY, ACCENT, NEUTRAL],
                textinfo="label+percent",
                hovertemplate="%{label}: %{percent}<extra></extra>",
            )
        )
        fig_pie = style_plotly_fig(fig_pie, title="QEI distribution by distress level", height=340)
        fig_pie.update_traces(
            textfont=dict(color="#FFFFFF", size=12),
            insidetextfont=dict(color="#FFFFFF", size=12),
            outsidetextfont=dict(color=TEXT_LIGHT, size=11),
        )
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left",
                        font=dict(color=TEXT_LIGHT)),
            margin=dict(l=0, r=120, t=60, b=20),
            annotations=[dict(
                text=center_text,
                x=0.38, y=0.5,
                font=dict(size=13, color=TEXT_LIGHT),
                showarrow=False,
                xref="paper", yref="paper",
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        # --- B: distress concentration vs. this tool's own screening band ---
        #
        # WITHDRAWN IN 1.2.0. This chart used to read "Benchmarks vs. historical
        # winners" and plot three hardcoded values:
        #
        #     WINNER_MEDIAN = 0.82 ; winner_p25 = 0.72 ; winner_p75 = 0.91
        #
        # labelled "Winner p25 / Winner median / Winner p75", with a green/red
        # "up above median" / "down below median" delta against the user's
        # pipeline and no disclaimer anywhere on the page.
        #
        # There is no such distribution. The three values are copies of
        # WINNER_DISTRESS_PATTERNS in nmtcapp/data/historical_awards.py, whose
        # own module docstring records that the publication it cites DOES NOT
        # EXIST and that "Every value under them is unsourced" — and they were
        # hardcoded here separately, so correcting that module would not have
        # corrected this page. The CDFI Fund publishes winner-level award data
        # but no distribution of applicant distress concentration, so no
        # percentile of winners can be computed from anything public.
        #
        # Same policy as the F28 impact-band relabel and the >=75% deep-distress
        # band: the claim is WITHDRAWN, not re-cited and not softened. What
        # replaces it is the only comparator this tool can honestly draw — its
        # own screening band, labelled on its face as its own.
        st.markdown("**Distress concentration vs. this tool's screening band**")
        screening_band = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]

        bench_labels = ["Your pipeline", "This tool's band"]
        bench_values = [deep_severe_pct * 100, screening_band * 100]
        bar_colors = [ACCENT, LIGHT_BLUE]

        fig_bench, ax_bench = plt.subplots(figsize=(6, 3.5))
        _bars = ax_bench.bar(bench_labels, bench_values, color=bar_colors, width=0.5)
        ax_bench.axhline(y=screening_band * 100, color=NEUTRAL, linestyle="--",
                         linewidth=1.2, alpha=0.8)
        for bar, val in zip(_bars, bench_values):
            ax_bench.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                          f"{val:.1f}", ha="center", va="bottom", fontsize=9)
        ax_bench.set_ylim(0, 108)
        style_matplotlib_axes(ax_bench, ylabel="% of QEI in deep/severe tracts")
        ax_bench.tick_params(axis="x", rotation=10)
        fig_bench.tight_layout()
        st.pyplot(fig_bench, use_container_width=True)
        plt.close(fig_bench)
        st.caption(
            f"The {screening_band:.0%} line is **this tool's own screening band**, "
            "not a CDFI Fund threshold and not a percentile of past winners. The "
            "CDFI Fund publishes no distribution of applicant distress "
            "concentration, so no such percentile exists. The published CY "
            "2024-2025 bar for full Community Outcomes credit is 85% of QLICIs "
            "in areas of higher distress (Allocation Application, Question 25(a)) "
            "— **a share of QLICIs, while the bars above are shares of QEI**. "
            "This tool computes no QLICI-denominated share, so nothing on this "
            "chart answers that bar or may be compared to it."
        )

    # THE BASIS NOTE, ON THE SCREEN THAT PRINTS THE SHARE (1.3.0 B1
    # ride-along). The metric above points at it, so it has to be here — the
    # defect this whole round is about is a pointer to something the reader
    # cannot reach. Same string, from the same function, as Section B and the
    # workbook's Q25 Basis Note sheet.
    #
    # Expanded by default rather than collapsed: a disclosure behind a click
    # is a disclosure the reader under deadline does not open, and this one
    # exists because the figure above it invites a specific wrong use.
    st.markdown("---")
    with st.expander("BASIS NOTE — what these shares are, and what they are "
                     "not an answer to", expanded=True):
        st.markdown(q25_basis_note())


# =============================================================================
# TAB 2 — Geographic
# =============================================================================
with tabs[2]:
    st.subheader("Geographic diversity")

    states_count = g.get("states_count", 0)
    hhi = g.get("hhi", 0)
    conc_label = g.get("geographic_concentration_label", "N/A")
    non_metro_pct = g.get("non_metro_pct", 0.0)
    metro_pct = g.get("metro_pct", 0.0)
    undetermined_pct = g.get("metro_undetermined_pct", 0.0)
    metro_qei = g.get("metro_status_qei", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("States represented", states_count)
    c2.metric("Geographic HHI", f"{hhi:,.0f}")
    c3.metric("Concentration level", conc_label)
    # WAS: metric("Rural share", fmt_pct(rural_pct)) — a bare percentage whose
    # denominator was invisible and whose basis was a twelve-state list.
    # tests/test_streamlit_metric_basis.py ruled this exact metric for 1.4.0.
    # The label now names the denominator on the figure's own face, as the
    # generated documents do for every distress share.
    c4.metric(Q22_NON_METRO_METRIC_LABEL, fmt_pct(non_metro_pct))

    st.markdown("---")

    # --- C: State QEI bar chart ---
    app_obj = st.session_state.get("app")
    if app_obj and app_obj.pipeline:
        df = app_obj.pipeline.to_dataframe()
        state_qei = (
            df.groupby("state")["qei_request"]
            .sum()
            .reset_index()
            .rename(columns={"qei_request": "QEI ($)"})
            .sort_values("QEI ($)", ascending=False)
            .reset_index(drop=True)
        )
        state_qei["QEI ($M)"] = state_qei["QEI ($)"] / 1_000_000

        n_states = len(state_qei)
        state_colors = [
            NAVY if i < 3 else MID_BLUE for i in range(n_states)
        ]
        avg_qei = state_qei["QEI ($M)"].mean()

        fig_states, ax_states = plt.subplots(figsize=(9, 4))
        ax_states.bar(state_qei["state"], state_qei["QEI ($M)"], color=state_colors, width=0.7)
        ax_states.axhline(y=avg_qei, color=NEUTRAL, linestyle="--", linewidth=1.1, alpha=0.8)
        ax_states.text(n_states - 0.5, avg_qei + 0.1, f"Avg ${avg_qei:.1f}M",
                       color=NEUTRAL, fontsize=8, ha="right", va="bottom")
        for idx, val in enumerate(state_qei["QEI ($M)"]):
            ax_states.text(idx, val + 0.1, f"{val:.1f}", ha="center", va="bottom", fontsize=8)
        ax_states.tick_params(axis="x", rotation=45)
        style_matplotlib_axes(ax_states, title="QEI by state", ylabel="QEI ($ millions)")
        fig_states.tight_layout()
        st.pyplot(fig_states, use_container_width=True)
        plt.close(fig_states)

    # --- D: Urban / rural donut ---
    left, right = st.columns(2)
    msa_count = g.get("msa_count", "N/A")
    with left:
        fig_ur = go.Figure(
            go.Pie(
                # THREE SLICES, ALWAYS (1.4.0 R2). The two-slice
                # Urban/Rural donut drew a ring that summed to 100% out of a
                # figure computed as 1 − (QEI in twelve states), so every
                # unverified dollar was drawn as urban. A donut that silently
                # drops undetermined dollars is the same defect as a numerator
                # that silently excludes them — it just fails in colour.
                #
                # The undetermined slice is passed even when it is zero:
                # Plotly renders a zero-value slice as nothing but keeps it in
                # the legend, so the category stays visible as a category.
                labels=[Q22_METRO_LABEL, Q22_NON_METRO_LABEL,
                        Q22_UNDETERMINED_LABEL],
                values=[metro_pct, non_metro_pct, undetermined_pct],
                sort=False,
                hole=0.5,
                marker_colors=[BLUE, ACCENT, NEUTRAL],
                textinfo="label+percent",
                hovertemplate="%{label}: %{percent}<extra></extra>",
            )
        )
        fig_ur = style_plotly_fig(
            fig_ur, title="QEI by Non-Metropolitan County status", height=300)
        fig_ur.update_traces(
            textfont=dict(color="#FFFFFF", size=12),
            insidetextfont=dict(color="#FFFFFF", size=12),
            outsidetextfont=dict(color=TEXT_LIGHT, size=11),
        )
        fig_ur.update_layout(
            showlegend=True,
            legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left",
                        font=dict(color=TEXT_LIGHT)),
            margin=dict(l=0, r=100, t=60, b=20),
            annotations=[dict(
                text=f"{msa_count}<br>MSAs",
                x=0.37, y=0.5,
                font=dict(size=13, color=TEXT_LIGHT),
                showarrow=False,
                xref="paper", yref="paper",
            )],
        )
        st.plotly_chart(fig_ur, use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        st.markdown("**Geographic benchmarks**")
        # THREE HAND-TYPED CONSTANTS SAT HERE, NOT ONE (1.4.0 R5). "Winner
        # median states: **7**", "Winner mean HHI: **620**" and "Winner rural
        # mean: **18%**" were all literals beside a live figure, and all three
        # are keys of WINNER_GEOGRAPHIC_PATTERNS. Two are now interpolated from
        # the constant, which is this package's rule and the fix for six
        # recorded instances of a hand-typed number going stale.
        # THE WORD "Winner" IS DELETED FROM BOTH LABELS (B3), AND THAT IS THE
        # WHOLE FIX -- the constants themselves are unchanged and still
        # scored. Until this change these lines read "Winner median states: 7"
        # and "Winner mean HHI: 620". Both numbers are HOUSE constants of
        # WINNER_GEOGRAPHIC_PATTERNS, and the label asserted -- in the label
        # itself, with no caveat within a screen of it -- that they were
        # MEASUREMENTS OF REAL ALLOCATEES. They are not, and the module that
        # holds them says so. A number a CDE reads as "what winners do" is a
        # federal-sounding claim; a number it reads as "this tool's reference
        # point" is a prompt. Only the second one is true here.
        #
        # NOT REMOVED FROM SCORING, and that was ruled on evidence rather than
        # assumed. See benchmarks._METHODOLOGY and the 1.5.0 CHANGELOG entry:
        # the case for withdrawing these two metrics rested on the median CDE
        # in the Fund's Public Data Release serving 2-3 states, which is an
        # UNWEIGHTED median over 350 CDE names dominated by small subsidiary
        # CDEs and measures REALIZED CUMULATIVE DEPLOYMENT, not an application
        # pipeline. Restricted to the ~141 CDEs with 50+ transactions -- about
        # the number of Allocatees in a round, and 80% of all QLICI dollars --
        # the median is 9 states, and among the top 50 by dollars it is 21.
        # The CY 2024-2025 Award Book puts 65 of 142 Allocatees on a national
        # service area and 39 more on a multistate one. The bands are not
        # measuring the wrong thing by an order of magnitude; the LABELS were.
        st.markdown(
            f"- This tool's median-states reference point: "
            f"**{WINNER_GEOGRAPHIC_PATTERNS['p50_states']:.0f}**  |  "
            f"Your pipeline: **{states_count}**"
        )
        st.markdown(
            f"- This tool's mean-HHI reference point: "
            f"**{WINNER_GEOGRAPHIC_PATTERNS['mean_hhi']:,.0f}**  |  "
            f"Your pipeline: **{hhi:,.0f}**"
        )
        st.caption(_GEO_REFERENCE_METHODOLOGY)
        # THE THIRD ONE IS NOT INTERPOLATED — IT IS DELETED. 18% traces to
        # WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"], so it was pinnable; the
        # ruling is that it should not be rendered at all. That constant is one
        # of the values data/historical_awards.py's own header describes as
        # citing a publication that does not exist, it is the exact complement
        # of urban_pct_mean, and Question 22 asks the Applicant to COMMIT to a
        # percentage of QLICIs rather than to report a pipeline share — so
        # there is no question this comparison answers. Pinning the number
        # would have made a misleading comparison reproducible.
        # See renderers/_question_22 and intelligence/benchmarks.
        st.markdown(f"- MSAs represented: **{msa_count}**")

    st.markdown("---")
    st.markdown("**Non-Metropolitan County status of pipeline QEI**")
    d1, d2, d3 = st.columns(3)
    d1.metric(
        f"{Q22_NON_METRO_LABEL} (QEI)", fmt_pct(non_metro_pct),
        help=f"{metro_qei.get('non_metro_projects', 0)} project(s)",
    )
    d2.metric(
        f"{Q22_METRO_LABEL} (QEI)", fmt_pct(metro_pct),
        help=f"{metro_qei.get('metro_projects', 0)} project(s)",
    )
    d3.metric(
        f"{Q22_UNDETERMINED_LABEL} (QEI)", fmt_pct(undetermined_pct),
        help=f"{metro_qei.get('undetermined_projects', 0)} project(s) — "
             "counted as neither",
    )
    caveat = q22_undetermined_caveat(undetermined_pct)
    if caveat:
        st.warning(caveat)
    with st.expander("What this figure is, and what Question 22 asks for"):
        st.markdown(q22_basis_note())

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

    # --- E: Sector horizontal bar chart ---
    app_obj = st.session_state.get("app")
    if app_obj and app_obj.pipeline:
        df = app_obj.pipeline.to_dataframe()
        sector_qei = (
            df.groupby("sector")["qei_request"]
            .sum()
            .reset_index()
            .rename(columns={"qei_request": "QEI ($)"})
            .sort_values("QEI ($)", ascending=True)
            .reset_index(drop=True)
        )
        sector_qei["QEI ($M)"] = sector_qei["QEI ($)"] / 1_000_000
        sector_qei["sector_label"] = sector_qei["sector"].str.replace("_", " ").str.title()

        # Add count and % per sector
        sector_counts = (
            df.groupby("sector")["qei_request"]
            .count()
            .reset_index()
            .rename(columns={"qei_request": "count"})
        )
        sector_qei = sector_qei.merge(sector_counts, on="sector")
        total_sec = sector_qei["QEI ($)"].sum() or 1.0
        sector_qei["pct"] = sector_qei["QEI ($)"] / total_sec * 100

        n_sec = len(sector_qei)
        sec_colors = bar_gradient(n_sec, lo=LIGHT_BLUE, hi=NAVY)
        avg_sec = sector_qei["QEI ($M)"].mean()
        max_val = sector_qei["QEI ($M)"].max()

        fig_sector, ax_sector = plt.subplots(figsize=(8, max(3.5, n_sec * 0.55)))
        ax_sector.barh(sector_qei["sector_label"], sector_qei["QEI ($M)"],
                       color=sec_colors, height=0.6)
        # Mean reference line
        ax_sector.axvline(x=avg_sec, color=NEUTRAL, linestyle="--", linewidth=1.1, alpha=0.8)
        ax_sector.text(avg_sec + max_val * 0.01, n_sec - 0.5,
                       f"Avg ${avg_sec:.1f}M", color=NEUTRAL, fontsize=8, va="top")
        # Label: "$XM (N proj, Y%)" at end of each bar
        for idx, (val, cnt, pct) in enumerate(zip(
                sector_qei["QEI ($M)"], sector_qei["count"], sector_qei["pct"])):
            ax_sector.text(val + max_val * 0.02, idx,
                           f"${val:.1f}M ({cnt} proj, {pct:.0f}%)",
                           va="center", ha="left", fontsize=8, color=TEXT_DARK)
        ax_sector.set_xlim(0, max_val * 1.55)
        style_matplotlib_axes(ax_sector, title="QEI allocation by sector",
                               xlabel="QEI ($ millions)")
        fig_sector.tight_layout()
        st.pyplot(fig_sector, use_container_width=True)
        plt.close(fig_sector)

    # Sector QEI share breakdown table
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
    # 1.2.1 B-2: aggregate_impact returns None when no project supplied a
    # figure, and a supplied 0 when one did. `if total_units:` collapsed the
    # two — a CDE that entered 0 for every project saw the metric vanish, the
    # same as a CDE that entered nothing.
    total_units = i.get("total_units_built")
    total_sqft = i.get("total_sq_ft")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total jobs created", f"{total_jobs:,}")
    c2.metric("Jobs retained", f"{total_retained:,}")
    c3.metric("Jobs per $1MM QEI", f"{jpm:.1f}")

    if total_units is None:
        st.metric("Affordable housing units", "—",
                  help="No project in this pipeline supplied a units figure.")
    else:
        st.metric("Affordable housing units", f"{total_units:,}")

    st.markdown("---")

    left, right = st.columns([1, 1])

    with left:
        # --- F: Jobs/$1MM QEI vs. this tool's winner figures ---
        #
        # FOUR MORE HAND-TYPED TWINS, AND TWO MORE COMPETITIVENESS CLAIMS
        # (1.5.2 T4, found by the gate written for the readiness chart above
        # rather than known in advance). These four literals were exact copies
        # of WINNER_IMPACT_BENCHMARKS's p25/p50/p75/top-decile keys, retyped
        # into a chart on the same page — the same L-3 duplication as the
        # GRADE_THRESHOLDS ladder, and the shape that let maps._MED_PRIORITY
        # drift out of agreement with schema.
        #
        # AND THE CONSTANT THEY COPY IS RULED UNSOURCED. tests/
        # scoring_attribution.txt marks all seven WINNER_IMPACT_BENCHMARKS
        # keys HOUSE, and historical_awards.py's own header states that the
        # "Source: CDFI Fund Annual Reports" comment above the dict cites a
        # publication that DOES NOT EXIST and that "Every value under them is
        # unsourced". That header exempted them as "NOT SHIP-BLOCKING" on the
        # narrow ground that "none of these constants reaches a rendered
        # application", verified by grepping the four GENERATED DOCUMENTS for
        # "winner" and "p75".
        #
        # THE EXEMPTION NEVER COVERED THIS SCREEN. The same header lists "the
        # Streamlit pages" among the consumers. This chart prints all four
        # values under the labels "Winner p25 / Winner median / Winner p75 /
        # Winner top 10%" — a claim about a POPULATION OF PAST ALLOCATEES,
        # with no such population behind it — and then drew a shaded
        # "Competitive zone" across them and stamped "✓ Competitive range" on
        # the CDE's own bar. That is 1.3.0 B1 exactly: "A CDE reads a figure
        # off a screen and types it into a form exactly the way it reads one
        # off a workbook; producing no file is not the same as reaching no
        # filing."
        #
        # WHAT CHANGES HERE IS THE LABELLING AND THE DUPLICATION, NOT THE
        # NUMBERS. Re-deriving what a winner percentile actually is would be
        # methodology and needs a source this package does not have; that is
        # recorded, not attempted. The values now come from the constant, and
        # the chart says whose figures they are.
        _WIB = WINNER_IMPACT_BENCHMARKS
        WIN_P25   = _WIB["p25_jobs_per_mm_qei"]
        WIN_MED   = _WIB["p50_jobs_per_mm_qei"]
        WIN_P75   = _WIB["p75_jobs_per_mm_qei"]
        WIN_TOP10 = _WIB["top_decile_jobs_per_mm_qei"]

        bench_lbls = ["Your pipeline", "p25", "median", "p75", "top decile"]
        bench_vals = [jpm, WIN_P25, WIN_MED, WIN_P75, WIN_TOP10]
        # ACCENT for "Your pipeline", graduated blues for winners
        winner_blues = bar_gradient(4, lo=LIGHT_BLUE, hi=NAVY)
        jpm_colors = [ACCENT] + winner_blues

        fig_jpm, ax_jpm = plt.subplots(figsize=(7, 3.5))
        # The band states its own extent instead of pronouncing on it.
        ax_jpm.axhspan(WIN_P25, WIN_TOP10, alpha=0.07, color=SUCCESS, zorder=0)
        ax_jpm.text(4.42, (WIN_P25 + WIN_TOP10) / 2, "p25 to\ntop decile",
                    color=SUCCESS, fontsize=8, ha="right", va="center", style="italic")
        _jpm_bars = ax_jpm.bar(bench_lbls, bench_vals, color=jpm_colors, width=0.6)
        for bar, val in zip(_jpm_bars, bench_vals):
            ax_jpm.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                        f"{val:.1f}", ha="center", va="bottom", fontsize=9)
        # A POSITION, NOT A VERDICT. This stamped "✓ Competitive range" in
        # white bold across the CDE's own bar — a tick mark and the word
        # "competitive", over a band whose endpoints are unsourced.
        if WIN_P25 <= jpm <= WIN_TOP10:
            ax_jpm.text(
                _jpm_bars[0].get_x() + _jpm_bars[0].get_width() / 2,
                _jpm_bars[0].get_height() / 2,
                "within\nthe band",
                ha="center", va="center", fontsize=8,
                color="white", fontweight="bold",
            )
        ax_jpm.tick_params(axis="x", rotation=15)
        style_matplotlib_axes(
            ax_jpm,
            title="Jobs/$1MM QEI vs. this tool's own winner figures",
            ylabel="Jobs / $1MM QEI",
        )
        fig_jpm.tight_layout()
        st.pyplot(fig_jpm, use_container_width=True)
        plt.close(fig_jpm)
        st.caption(
            "The p25 / median / p75 / top-decile lines are "
            "`WINNER_IMPACT_BENCHMARKS`, **this tool's own unsourced figures** "
            "— this package's constant registry rules all seven of its keys "
            "HOUSE, and the \"CDFI Fund Annual Reports\" series the dict once "
            "cited does not exist. The CDFI Fund publishes no jobs-per-QEI "
            "figure in any denominator and no distribution, so these are not "
            "percentiles of any measured population of past Allocatees and "
            "your position against them is not evidence about your application."
        )

    with right:
        st.markdown("**Impact summary**")
        st.markdown(f"- Total jobs created: **{total_jobs:,}**")
        st.markdown(f"- Total jobs retained: **{total_retained:,}**")
        if total_units:
            st.markdown(f"- Affordable units: **{total_units:,}**")
        if total_sqft is None:
            st.markdown("- Commercial sq ft: **—** (not supplied by any project)")
        else:
            st.markdown(f"- Commercial sq ft: **{total_sqft:,.0f}**")
        st.markdown(f"- Jobs / $1MM QEI: **{jpm:.1f}**")

        # --- G: Deal economics waterfall ---
        econ = analysis.deal_economics
        if econ or pr.total_project_cost > 0:
            st.markdown("---")
            qei_val     = econ.get("total_qei", pr.total_qei_request) if econ else pr.total_qei_request
            nmtcs_val   = econ.get("total_nmtcs", qei_val * 0.39) if econ else qei_val * 0.39
            equity_val  = econ.get("total_investor_equity", nmtcs_val * 0.83) if econ else nmtcs_val * 0.83
            cde_fees_val = econ.get("total_cde_fees", qei_val * 0.025) if econ else qei_val * 0.025
            subsidy_val  = econ.get("total_net_subsidy", qei_val - cde_fees_val) if econ else qei_val - cde_fees_val

            if qei_val > 0:
                fig_wf = go.Figure(go.Waterfall(
                    name="Deal Economics",
                    orientation="v",
                    measure=["absolute", "relative", "total"],
                    # NOT "Net Capital to QALICBs": this is QEI less the CDE
                    # fee, ~97.5% of QEI, and it still contains the leverage
                    # loan the QALICB repays. See the note in
                    # nmtcapp/sections/section_d_capitalization.
                    x=["QEI Raised", "− CDE Fees (2.5%)", "QEI less CDE fees"],
                    y=[qei_val / 1e6, -cde_fees_val / 1e6, 0],
                    text=[
                        f"${qei_val / 1e6:.1f}M",
                        f"−${cde_fees_val / 1e6:.1f}M",
                        f"${subsidy_val / 1e6:.1f}M",
                    ],
                    textposition="outside",
                    textfont=dict(color=TEXT_LIGHT, size=11),
                    increasing={"marker": {"color": SUCCESS}},
                    decreasing={"marker": {"color": DANGER}},
                    totals={"marker": {"color": NAVY}},
                    connector={
                        "visible": True,
                        "line": {"color": BORDER, "width": 1, "dash": "dot"},
                    },
                ))
                title_text = (
                    "Deal economics — capital flow to QALICBs"
                    "<br><span style='font-size:11px;color:#9CA3AF'>"
                    "From QEI raised to net capital flowing to QALICBs</span>"
                )
                fig_wf = style_plotly_fig(fig_wf, height=360)
                fig_wf.update_layout(
                    title=dict(text=title_text, font=dict(size=14, color=TEXT_LIGHT),
                               x=0.01, xanchor="left"),
                    yaxis=dict(
                        title="$ Millions",
                        tickprefix="$",
                        ticksuffix="M",
                        gridcolor=GRID,
                        zeroline=False,
                    ),
                    margin=dict(l=50, r=20, t=70, b=50),
                )
                st.plotly_chart(fig_wf, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown("**Deal economics**")
            st.markdown(f"- Total NMTCs: **{fmt_millions(nmtcs_val)}**")
            st.markdown(f"- Investor equity: **{fmt_millions(equity_val)}**")
            st.markdown(f"- Net capital to QALICBs: **{fmt_millions(subsidy_val)}**")
