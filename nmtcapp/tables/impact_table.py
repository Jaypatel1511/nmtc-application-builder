"""Section B impact projections table (per-project CDFI Fund format)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def build_impact_table(pipeline: "Pipeline") -> pd.DataFrame:
    """Build per-project impact projections in CDFI Fund Section B format.

    Example::

        df = build_impact_table(pipeline)
    """
    rows = []
    for p in pipeline:
        cost_per_job = (
            p.total_project_cost / p.expected_jobs_created
            if p.expected_jobs_created > 0 else 0.0
        )
        qei_per_job = (
            p.qei_request / p.expected_jobs_created
            if p.expected_jobs_created > 0 else 0.0
        )
        rows.append({
            "Project ID":            p.project_id,
            "Project Name":          p.project_name,
            "State":                 p.state,
            "Sector":                p.sector.replace("_", " ").title(),
            "Project Type":          p.project_type.replace("_", " ").title(),
            "QEI ($)":               p.qei_request,
            "Total Project Cost ($)":p.total_project_cost,
            "Jobs Created":          p.expected_jobs_created,
            "Jobs Retained":         p.expected_jobs_retained,
            "Total Jobs":            p.expected_jobs_created + p.expected_jobs_retained,
            "Cost per Job ($)":      round(cost_per_job),
            "QEI per Job ($)":       round(qei_per_job),
            "Affordable Units":      p.expected_units_built if p.expected_units_built else 0,
            "Commercial Sq Ft":      int(p.expected_sq_ft) if p.expected_sq_ft else 0,
            "Distress Level":        p.distress_level or "Pending",
            "Native Area":           "Yes" if p.is_native_area else "No",
            "HMR":                   "Yes" if p.is_high_migration_rural else "No",
            "OZ":                    "Yes" if p.is_opportunity_zone else "No",
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    total_qei = df["QEI ($)"].sum()
    total_cost = df["Total Project Cost ($)"].sum()
    total_jobs_c = df["Jobs Created"].sum()
    total_jobs_r = df["Jobs Retained"].sum()
    df.loc[len(df)] = {
        "Project ID": "TOTALS",
        "Project Name": f"{len(df)} Projects",
        "State": "",
        "Sector": "",
        "Project Type": "",
        "QEI ($)": total_qei,
        "Total Project Cost ($)": total_cost,
        "Jobs Created": total_jobs_c,
        "Jobs Retained": total_jobs_r,
        "Total Jobs": total_jobs_c + total_jobs_r,
        "Cost per Job ($)": round(total_cost / total_jobs_c) if total_jobs_c > 0 else 0,
        "QEI per Job ($)": round(total_qei / total_jobs_c) if total_jobs_c > 0 else 0,
        "Affordable Units": df["Affordable Units"].sum(),
        "Commercial Sq Ft": df["Commercial Sq Ft"].sum(),
        "Distress Level": "",
        "Native Area": "",
        "HMR": "",
        "OZ": "",
    }
    return df
