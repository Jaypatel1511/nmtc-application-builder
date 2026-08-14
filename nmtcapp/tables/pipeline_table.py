"""
Section A pipeline detail table — mirrors CDFI Fund CY2025 Excel template format.

Each row represents one QALICB project with eligibility, distress, financial,
and impact data in the columns that CDFI Fund reviewers expect.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from nmtcapp.renderers.styles import DISTRESS_DISPLAY, SECTOR_NAICS

if TYPE_CHECKING:
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def _tract_cell(p) -> str:
    """Census tract, or the CDE's declared tract labelled as such."""
    from nmtcapp.tables.distress_table import _tract_cell as _t
    return _t(p)


def _distress_cell(p) -> str:
    """Distress level, or the CDE's declared level labelled as such."""
    from nmtcapp.tables.distress_table import _distress_cell as _d
    return _d(p)

# Standard credit price for estimated investor equity
_CREDIT_PRICE = 0.83
_CREDIT_RATE = 0.39
_CDE_FEE_RATE = 0.025
_LEVERAGE_RATIO = 0.80


def build_pipeline_table(pipeline: "Pipeline", cde: "CDEProfile" = None) -> pd.DataFrame:
    """Build the Section A pipeline detail table in CDFI Fund CY2025 format.

    Returns a DataFrame where each row is one project and columns match
    the CDFI Fund Excel pipeline attachment template.

    Example::

        df = build_pipeline_table(pipeline)
        print(df[["Project Name", "QEI Request", "Distress Level"]].head())
    """
    rows = []
    for p in pipeline:
        # Derived financial estimates
        qei = p.qei_request
        total_nmtcs = qei * _CREDIT_RATE
        investor_equity = total_nmtcs * _CREDIT_PRICE
        cde_fee = qei * _CDE_FEE_RATE
        leverage_loan = qei * _LEVERAGE_RATIO
        senior_debt = max(0.0, p.total_project_cost - investor_equity - (qei * (1 - _LEVERAGE_RATIO)))
        annual_op_budget = p.total_project_cost * 0.08  # ~8% of total cost, rough estimate

        rows.append({
            "Project ID":                 p.project_id,
            "QALICB Name":                p.qalicb_name,
            "Project Name":               p.project_name,
            "Street Address":             p.address,
            "City":                       p.city,
            "State":                      p.state,
            "ZIP Code":                   "",
            "Census Tract (11-digit)":    _tract_cell(p),
            "NMTC Eligible (Y/N)":        "Y" if p.is_nmtc_eligible else ("N" if p.is_nmtc_eligible is False else "Unverified"),
            "Distress Level":             _distress_cell(p),
            "NMTC Native Area (Y/N)":     _yn_flag(p.is_native_area),
            "High Migration Rural (Y/N)": _yn_flag(p.is_high_migration_rural),
            "Opportunity Zone (Y/N)":     _yn_flag(p.is_opportunity_zone),
            "Sector (NAICS)":             SECTOR_NAICS.get(p.sector, p.sector),
            "Project Type":               p.project_type.replace("_", " ").title(),
            "Total Project Cost ($)":     p.total_project_cost,
            "QEI Request ($)":            qei,
            "QLICI A Loan ($)":           p.qlici_amount * 0.20,   # ~20% QLICI-A
            "QLICI B Loan ($)":           p.qlici_amount * 0.80,   # ~80% QLICI-B
            "Leverage Loan ($)":          leverage_loan,
            "Total NMTCs ($)":            total_nmtcs,
            "Estimated Investor Equity ($)": investor_equity,
            "CDE Fee ($)":                cde_fee,
            "Senior Debt ($)":            senior_debt,
            "Subordinate Debt ($)":       0.0,
            "Annual Operating Budget ($)": annual_op_budget,
            "Construction Start":         p.construction_start or "",
            "Operations Start":           p.operations_start or "",
            "Closing Target Date":        p.closing_target_date or "",
            "Jobs Created":               p.expected_jobs_created,
            "Jobs Retained":              p.expected_jobs_retained,
            "Affordable Units Built":     p.expected_units_built if p.expected_units_built else 0,
            "Square Feet":                int(p.expected_sq_ft) if p.expected_sq_ft else 0,
        })

    if not rows:
        return pd.DataFrame(columns=_PIPELINE_COLUMNS)

    df = pd.DataFrame(rows)
    # Add totals row
    totals = _build_totals_row(df)
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    return df


def _yn_flag(value) -> str:
    """Render a tri-state Y/N flag: None is unverified, never 'N'."""
    if value is None:
        return "—"
    return "Y" if value else "N"


def _build_totals_row(df: pd.DataFrame) -> dict:
    """Add a TOTALS summary row at the bottom."""
    numeric_cols = [
        "Total Project Cost ($)", "QEI Request ($)", "QLICI A Loan ($)", "QLICI B Loan ($)",
        "Leverage Loan ($)", "Total NMTCs ($)", "Estimated Investor Equity ($)", "CDE Fee ($)",
        "Senior Debt ($)", "Annual Operating Budget ($)",
        "Jobs Created", "Jobs Retained", "Affordable Units Built", "Square Feet",
    ]
    row: dict = {c: "" for c in df.columns}
    row["Project ID"] = "TOTALS"
    row["Project Name"] = f"TOTAL ({len(df)} projects)"
    for col in numeric_cols:
        if col in df.columns:
            row[col] = df[col].sum()
    return row


def build_pipeline_summary_table(pipeline: "Pipeline") -> pd.DataFrame:
    """Build a 6-column summary of the pipeline for Word/PDF body sections.

    Full 33-column detail lives in the Excel attachment.  This view gives
    reviewers the key facts on a single portrait page.

    Example::

        df = build_pipeline_summary_table(pipeline)
    """
    rows = []
    for p in pipeline:
        name = p.project_name
        if len(name) > 40:
            name = name[:37] + "..."
        rows.append({
            "Project ID":          p.project_id,
            "Project Name":        name,
            "State":               p.state,
            "Distress Level":      _distress_cell(p),
            "QEI Request ($)":     p.qei_request,
            "Total Project Cost ($)": p.total_project_cost,
        })
    if not rows:
        return pd.DataFrame(columns=["Project ID", "Project Name", "State",
                                     "Distress Level", "QEI Request ($)", "Total Project Cost ($)"])
    df = pd.DataFrame(rows)
    totals = {
        "Project ID": "TOTALS",
        "Project Name": f"{len(df)} projects",
        "State": "",
        "Distress Level": "",
        "QEI Request ($)": df["QEI Request ($)"].sum(),
        "Total Project Cost ($)": df["Total Project Cost ($)"].sum(),
    }
    return pd.concat([df, pd.DataFrame([totals])], ignore_index=True)


_PIPELINE_COLUMNS = [
    "Project ID", "QALICB Name", "Project Name", "Street Address", "City", "State",
    "ZIP Code", "Census Tract (11-digit)", "NMTC Eligible (Y/N)", "Distress Level",
    "NMTC Native Area (Y/N)", "High Migration Rural (Y/N)", "Opportunity Zone (Y/N)",
    "Sector (NAICS)", "Project Type", "Total Project Cost ($)", "QEI Request ($)",
    "QLICI A Loan ($)", "QLICI B Loan ($)", "Leverage Loan ($)", "Total NMTCs ($)",
    "Estimated Investor Equity ($)", "CDE Fee ($)", "Senior Debt ($)", "Subordinate Debt ($)",
    "Annual Operating Budget ($)", "Construction Start", "Operations Start",
    "Closing Target Date", "Jobs Created", "Jobs Retained", "Affordable Units Built",
    "Square Feet",
]
