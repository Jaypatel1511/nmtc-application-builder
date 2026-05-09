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
            "Census Tract (GEOID)":        p.census_tract or "Pending Geocode",
            "NMTC Eligible":               "Yes" if p.is_nmtc_eligible else (
                                               "No" if p.is_nmtc_eligible is False else "Pending"),
            "Distress Level":              DISTRESS_DISPLAY.get(p.distress_level, "Not Assessed"),
            "Severely Distressed Flag":    "Yes" if p.distress_level in ("deep", "severe") else "No",
            "NMTC Native Area":            "Yes" if p.is_native_area else "No",
            "High Migration Rural (HMR)":  "Yes" if p.is_high_migration_rural else "No",
            "Opportunity Zone":            "Yes" if p.is_opportunity_zone else "No",
            "Poverty Rate (%)":            _fmt_pct(p),
            "Median Family Income":        "See ACS",
            "Unemployment Rate (%)":       "See ACS",
            "Data Source":                 _ELIGIBILITY_SOURCE,
            "ACS Vintage":                 _ACS_YEAR,
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


def _fmt_pct(p) -> str:
    """Return formatted poverty rate if available via distress level proxy."""
    if p.distress_level == "deep":
        return "> 30%"
    if p.distress_level in ("severe", "lic"):
        return "> 20%"
    return "See ACS"
