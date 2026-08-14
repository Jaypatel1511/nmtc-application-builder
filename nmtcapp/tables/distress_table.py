"""Distress documentation table for NMTC applications."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from nmtcapp.renderers.styles import DISTRESS_DISPLAY

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ACS data year cited in methodology
_ACS_YEAR = "2016–2020 ACS 5-Year Estimates"
_ELIGIBILITY_SOURCE = "CDFI Fund NMTC Eligibility Table (2016–2020 ACS)"


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
            "NMTC Native Area":            _flag(p.is_native_area),
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
    native = df["NMTC Native Area"].str.lower().eq("yes").sum()
    df.loc[len(df)] = {
        "Project ID": "SUMMARY",
        "Project Name": f"{total} total projects",
        "City, State": "",
        "Census Tract (GEOID)": "",
        "NMTC Eligible": f"{(df['NMTC Eligible'].str.lower()=='yes').sum()}/{total}",
        "Distress Level": "",
        "Severely Distressed Flag": f"{deep}/{total} ({deep/total:.0%})",
        "NMTC Native Area": f"{native}/{total}",
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
            "Native Area":          _flag(p.is_native_area),
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
    """Severely-distressed flag; an unenriched project is unverified."""
    if p.distress_level is None:
        return "Unverified"
    return "Yes" if p.distress_level in ("deep", "severe") else "No"
