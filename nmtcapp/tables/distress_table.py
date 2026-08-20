"""Distress documentation table for NMTC applications."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from nmtcapp.renderers._methodology import ACS_VINTAGE
from nmtcapp.renderers.styles import DISTRESS_DISPLAY

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ACS data year cited in methodology. Imported rather than retyped so a per-row
# "ACS Vintage" cell and the methodology appendix that explains it cannot name
# two different releases of the same dataset.
_ACS_YEAR = ACS_VINTAGE
_ELIGIBILITY_SOURCE = "CDFI Fund NMTC Eligibility Table (2016–2020 ACS)"

# ---------------------------------------------------------------------------
# NATIVE AREA IS THE CDE'S OWN DECLARATION. THE CHAIN, END TO END.
#
# `nmtcapp analyze` printed "Native Area: 10%" under a heading of tool-derived
# distress shares, on a package whose dependency no longer publishes the field.
# Traced from the rendered line back to its source:
#
#   1. RENDERED   intelligence/pipeline_analyzer.summary() prints
#                 distress_breakdown["pct_native_area"].
#   2. COMPUTED   intelligence/distress_analysis.analyze_distress_concentration
#                 sums p.qei_request over projects where `p.is_native_area` is
#                 truthy and divides by total_qei.
#   3. FIELD      core/pipeline.PipelineProject.is_native_area, Optional[bool],
#                 default None.
#   4. POPULATED  core/pipeline.Pipeline.from_csv reads the `native_area` CSV
#                 column through _optional_bool (pipeline.py:305), and
#                 core/upload_handler maps the spreadsheet header
#                 "Native Area (Y/N)" to the same field. Both are cells the CDE
#                 fills in on the shipped template, which documents the column
#                 as "native_area -> drives pct_native_area".
#   5. NOT THE DEPENDENCY. integrations/nmtc_mapper_adapter deliberately does
#                 not assign it (nmtc_mapper_adapter.py:181-189), and
#                 tests/integrations/test_mapper_contract.py:192 fails if any
#                 enrichment path ever does.
#
# SO IT IS POSSIBILITY (1): a CDE-supplied declaration. Not the dependency, not
# a default, not an inference. nmtc-mapper 0.5.0 dropped is_nmtc_native_area
# and nothing here noticed because nothing here read it.
#
# THAT DOES NOT MAKE THE RENDERING CORRECT. The CDFI Fund publishes no
# tract-keyed NMTC Native Areas resource to check it against: the four classes
# are Census AIANNH legal geographies whose GEOIDs carry no state or county
# component and cannot nest into SSCCCTTTTTT, and the determination is a
# spatial intersection against the Fund's CIMS map, not a join. This tool
# therefore cannot verify the declaration and must not present it beside shares
# it derived itself. Special Targeting awards up to 1.25 Priority Points for
# NMTC Native Areas, so a figure here is a scored figure.
#
# Every surface that prints it now says whose it is.
#
# ONE DENOMINATOR CAVEAT, stated because 1.2.0's fix pass corrected the banner
# covering the distress shares without auditing each site: pct_native_area
# divides by the SAME total_qei as those shares, and an undeclared project
# (is_native_area None) falls to the "not native" side. It is a lower bound
# over declared values, on a full-pipeline denominator.
NATIVE_AREA_BASIS = "CDE-declared; not verified by this tool"

# ---------------------------------------------------------------------------
# THE DISTRESS ROW LABELS, STATED ONCE (1.3.1 F2)
#
# Every generated document names each share's DENOMINATOR on the figure's own
# face — "QEI in LIC (Standard Eligible) Tracts", not "LIC". The Streamlit
# Distress tab printed two of the same shares as `st.metric("LIC (standard)")`
# and `st.metric("Native area (CDE-declared)")`, which drops the basis from the
# one surface that shows the figure with no document around it.
#
# This is the QEI/QLICI labelling fix of 1.2.1 and 1.3.0 reaching the surface
# it never reached, and the wording is CARRIED, not composed. What ships in the
# documents was hostile-audited across three rounds; a fresh paraphrase written
# for a metric label has not been, and a paraphrase of a denominator disclosure
# is a new claim about the denominator.
#
# BYTE-IDENTICAL TO WHAT SECTION B HAS RENDERED. These are the literals that
# stood in sections/section_b_outcomes, moved here and imported back, so the
# four committed baselines do not move.
# ---------------------------------------------------------------------------

#: Share of QEI in Low-Income Community (standard eligible) tracts.
LIC_ROW_LABEL = "QEI in LIC (Standard Eligible) Tracts"

#: Share of QEI in NMTC Native Areas — the CDE's own declaration, never the
#: tool's determination; see NATIVE_AREA_BASIS above.
NATIVE_AREA_ROW_LABEL = (
    "QEI in NMTC Native Areas (CDE-declared, not verified by this tool)"
)

#: Share of QEI in High Migration Rural counties.
HMR_ROW_LABEL = "QEI in High Migration Rural (HMR) Tracts"


def build_distress_table(pipeline: "Pipeline") -> pd.DataFrame:
    """Build the distress documentation table per CDFI Fund requirements.

    Includes census tract demographics, distress classification, and
    source citations for each pipeline project.

    Example::

        df = build_distress_table(pipeline)
        print(df[["Project Name", "Distress Level", "Poverty Rate"]].head())
    """
    rows = []
    for p in pipeline:
        rows.append({
            "Project ID":                  p.project_id,
            "Project Name":                p.project_name,
            "City, State":                 f"{p.city}, {p.state}",
            "Census Tract (GEOID)":        _tract_cell(p),
            "NMTC Eligible":               "Yes" if p.is_nmtc_eligible else (
                                               "No" if p.is_nmtc_eligible is False else "Unverified"),
            "Distress Level":              _distress_cell(p),
            "Severely Distressed Flag":    _severely_distressed_flag(p),
            "NMTC Native Area (CDE-declared)": _flag(p.is_native_area),
            "High Migration Rural (HMR)":  _flag(p.is_high_migration_rural),
            "Opportunity Zone":            _flag(p.is_opportunity_zone),
            "Poverty Rate (%)":            _fmt_pct(p),
            "Median Family Income":        "See ACS",
            "Unemployment Rate (%)":       "See ACS",
            "Data Source":                 _row_source(p),
            "ACS Vintage":                 _row_vintage(p),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Summary row
    total = len(df)
    deep = df["Severely Distressed Flag"].str.lower().eq("yes").sum()
    native = df["NMTC Native Area (CDE-declared)"].str.lower().eq("yes").sum()
    df.loc[len(df)] = {
        "Project ID": "SUMMARY",
        "Project Name": f"{total} total projects",
        "City, State": "",
        "Census Tract (GEOID)": "",
        "NMTC Eligible": f"{(df['NMTC Eligible'].str.lower()=='yes').sum()}/{total}",
        "Distress Level": "",
        "Severely Distressed Flag": f"{deep}/{total} ({deep/total:.0%})",
        "NMTC Native Area (CDE-declared)": f"{native}/{total}",
        "High Migration Rural (HMR)": "",
        "Opportunity Zone": "",
        "Poverty Rate (%)": "",
        "Median Family Income": "",
        "Unemployment Rate (%)": "",
        "Data Source": "",
        "ACS Vintage": "",
    }
    return df


def build_distress_summary_table(pipeline: "Pipeline") -> pd.DataFrame:
    """Build a 5-column distress summary for Word/PDF body sections.

    Example::

        df = build_distress_summary_table(pipeline)
    """
    rows = []
    for p in pipeline:
        rows.append({
            "Project ID":           p.project_id,
            "Census Tract (GEOID)": _tract_cell(p),
            "Distress Level":       _distress_cell(p),
            "Severely Distressed":  _severely_distressed_flag(p),
            "Native Area (CDE-declared)": _flag(p.is_native_area),
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _fmt_pct(p) -> str:
    """Poverty rate column: always "See ACS".

    The per-row Data Source column cites the CDFI Fund eligibility table —
    a figure inferred from the distress LABEL (">30%"/">20%") would be a
    fabricated ACS statistic under that citation. Actual rates live in the
    ACS source the row already points to.
    """
    return "See ACS"


def _row_source(p) -> str:
    """Cite the eligibility source only on rows that actually carry its data.

    Stamping every row with the CDFI Fund citation put a source attribution
    on rows whose eligibility was never determined — including whole tables
    produced on a run where the download failed.
    """
    if not p.is_enriched:
        return "Unverified — no eligibility data loaded for this project"
    return _ELIGIBILITY_SOURCE


def _row_vintage(p) -> str:
    """ACS vintage, or an explicit dash where no ACS data was used."""
    if not p.is_enriched:
        return "—"
    return _ACS_YEAR


def _tract_cell(p) -> str:
    """Census tract, or the CDE's declared tract labelled as such.

    A CDE-declared tract is shown rather than discarded — the shipped template
    collects one — but never bare, because the same row cites the CDFI Fund
    eligibility table and nothing checked the declared GEOID against it.
    """
    if p.census_tract:
        return str(p.census_tract)
    if getattr(p, "declared_census_tract", None):
        return f"{p.declared_census_tract} (CDE-declared, not verified)"
    return "Unverified" if p.geocode_success is False else "Pending Geocode"


def _distress_cell(p) -> str:
    """Distress level, or the CDE's declared level labelled as such."""
    if p.distress_level:
        return DISTRESS_DISPLAY.get(p.distress_level, "Not Assessed")
    declared = getattr(p, "declared_distress_level", None)
    if declared:
        label = DISTRESS_DISPLAY.get(str(declared).strip().lower(), str(declared))
        return f"{label} (CDE-declared, not verified)"
    return "Not Assessed"


def _flag(value) -> str:
    """Render a tri-state eligibility flag: None is unverified, never 'No'."""
    if value is None:
        return "—"
    return "Yes" if value else "No"


def _severely_distressed_flag(p) -> str:
    """Severely-distressed flag; an unenriched project is unverified.

    INCLUDING "deep" HERE IS CORRECT AND MUST STAY. Deep distress is a strict
    subset of severe distress in the CDFI Fund's own workbook — across all
    85,395 tracts, zero are flagged deep without also being flagged severe
    (see intelligence/distress_analysis.DEEP_IS_SUBSET_OF_SEVERE for the
    counts). A deep-distress project IS severely distressed, so a "No" here
    for a deep tract would be a false statement about the CDE's pipeline.

    This column was the RIGHT half of 1.2.1's B-1 contradiction: Section B
    printed a bucket that excluded deep distress under the heading "QEI in
    Severely Distressed Tracts", and this flag disagreed with it in the same
    filing. Section B was corrected to match this column, not the reverse.
    """
    if p.distress_level is None:
        return "Unverified"
    return "Yes" if p.distress_level in ("deep", "severe") else "No"
