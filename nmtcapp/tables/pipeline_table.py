"""
Section A pipeline detail table — the per-project attachment.

Each row is one QALICB project with eligibility, distress, financial and impact
data drawn from the CDE's own pipeline submission.

WHAT THE CDFI FUND ACTUALLY ASKS FOR, AND WHAT THIS TABLE USED TO INVENT

This module's docstring used to say it "mirrors CDFI Fund CY2025 Excel template
format". 1.2.1 retrieved the form. The Fund's per-project pipeline attachment is
TABLE A5: PROPOSED TRANSACTIONS in the CY 2024-2025 NMTC Allocation Application
(cdfifund.gov, CY_2024-2025_NMTC_Program_Allocation_Application.pdf, Exhibit A,
pp. 82-84). Its complete field list is:

    (a1) Project/Business Name        (i)  Total Non-QLICI Sources
    (a2) Description                  (j)  Total QEIs from unaffiliated CDEs
    (b)  Address City / State         (k)  Total number of unaffiliated CDEs
    (c)  Census Tract                 (l)  Activity Type
    (d)  Non-Metropolitan County?     (m)  Small Dollar / Revolving Loan Fund
    (e)  Projected QLICI Closing Date (n)  Business Type
    (f)  Total Project Costs          (o)  Planned uses of financing
    (g)  Total Applicant QEI          (p)  Targeted Community Outcomes
    (h)  Total Applicant QLICIs

Five columns this table printed as data appear NOWHERE in that form, and a
full-text search of all 142 pages of the application returns zero occurrences of
"QLICI B", "Senior Debt", "Subordinate Debt", "Annual Operating Budget" and
"Investor Equity". The Fund does not split QLICIs into A and B tranches at all;
it collects one figure, row (h). So they are removed rather than bracketed:

  QLICI A Loan ($) / QLICI B Loan ($)
      a flat 20/80 split of the CDE's qlici_amount. The A/B tranche split is a
      deal-specific structural fact the CDE knows and this tool guessed. The
      CDE's own total is now printed instead, as "Total QLICI ($)" — the figure
      Table A5 row (h) asks for, and the number the CDE actually supplied.
  Senior Debt ($)
      a plug: total_project_cost - investor_equity - 20% of QEI. It was not
      disjoint from the Leverage Loan column beside it — on the shipped 20-
      project sample the two summed to $204MM against a $170.6MM project cost.
  Subordinate Debt ($)
      asserted as $0 for every project in every pipeline. Not "none"; unknown.
  Annual Operating Budget ($)
      8% of total project cost. A QALICB financial-statement line, invented
      from a construction budget, under a heading a reviewer reads as reported.

WHY DELETED AND NOT BRACKETED AS [CDE TO COMPLETE]. 1.2.0 settled the investor
table that way, and the precedent would have carried here if the form shape
were real: bracketing keeps a form's rows while asserting nothing. It is not
real. Bracketing five fields the Fund never asks for would invite a CDE to
research and fill in five figures that have nowhere to go, and would leave this
attachment claiming a template parity it does not have. The docstring's claim
goes with them.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from nmtcapp.data.schema import NMTC_PROGRAM_CONSTRAINTS
from nmtcapp.renderers.styles import DISTRESS_DISPLAY

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

# Deal-economics parameters. READ FROM THE ONE CONSTANT, not retyped: these
# were three module-local literals (0.83 / 0.39 / 0.025) duplicating
# NMTC_PROGRAM_CONSTRAINTS, so Appendix A and Section D computed the same
# figures from two independent copies of the same three numbers.
_CREDIT_PRICE = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
_CREDIT_RATE = NMTC_PROGRAM_CONSTRAINTS["credit_rate"]
_CDE_FEE_RATE = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]


def leverage_loan_for(qei: float) -> float:
    """The leverage loan implied by a QEI, as the residual of QEI less equity.

    THE SINGLE DEFINITION. Appendix A used to size this as ``qei * 0.80`` from
    a module-local _LEVERAGE_RATIO while Section D took nmtc-calc's figure,
    which is this identity — so one document reported two leverage totals for
    one pipeline. Measured on the shipped 20-project sample: Appendix A
    $98,000,000, Section D $82,846,750, a $15.15MM contradiction that
    validation/consistency_check passed.

    The identity is the one that is true of the structure the document
    describes: the investment fund's sources are the leverage loan plus the
    investor's equity, and their sum is the QEI. A flat 80% is a rule of thumb
    about a ratio that the credit price already determines
    (1 - 0.39 * 0.83 = 0.6763), and it cannot hold simultaneously with the
    equity figure printed in the next column.

    ``NMTC_PROGRAM_CONSTRAINTS["leverage_ratio_typical"]`` is left in place as a
    published dict key — 1.2.1 is a patch — but nothing sizes anything with it.
    """
    return max(0.0, qei - (qei * _CREDIT_RATE * _CREDIT_PRICE))


def build_pipeline_table(pipeline: "Pipeline", cde: "CDEProfile" = None) -> pd.DataFrame:
    """Build the Section A pipeline detail table.

    Returns a DataFrame where each row is one project. Every financial column
    is either a figure the CDE supplied or a stated function of one; see the
    module docstring for the five invented columns 1.2.1 removed and the CDFI
    Fund form (Table A5) that establishes they were never asked for.

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
        leverage_loan = leverage_loan_for(qei)

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
            # CDE-DECLARED, and the header says so. See NATIVE_AREA_BASIS in
            # tables/distress_table for the full provenance chain.
            "NMTC Native Area (CDE-declared, Y/N)": _yn_flag(p.is_native_area),
            "High Migration Rural (Y/N)": _yn_flag(p.is_high_migration_rural),
            "Opportunity Zone (Y/N)":     _yn_flag(p.is_opportunity_zone),
            # Was SECTOR_NAICS.get(p.sector, p.sector) under a "Sector
            # (NAICS)" heading — an invented industry code. See the note
            # where SECTOR_NAICS used to live in renderers/styles.py.
            "Sector (as supplied)":       (p.sector or "").replace("_", " ").title() or "Not supplied",
            "Project Type":               p.project_type.replace("_", " ").title(),
            "Total Project Cost ($)":     p.total_project_cost,
            "QEI Request ($)":            qei,
            # The CDE's own qlici_amount, whole. It used to appear only as a
            # 20/80 A/B split this tool invented; the Fund's Table A5 row (h)
            # collects one total and defines no tranches.
            "Total QLICI ($)":            p.qlici_amount,
            "Leverage Loan ($)":          leverage_loan,
            "Total NMTCs ($)":            total_nmtcs,
            "Estimated Investor Equity ($)": investor_equity,
            "CDE Fee ($)":                cde_fee,
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
        "Total Project Cost ($)", "QEI Request ($)", "Total QLICI ($)",
        "Leverage Loan ($)", "Total NMTCs ($)", "Estimated Investor Equity ($)",
        "CDE Fee ($)",
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
    "NMTC Native Area (CDE-declared, Y/N)", "High Migration Rural (Y/N)",
    "Opportunity Zone (Y/N)",
    "Sector (as supplied)", "Project Type", "Total Project Cost ($)", "QEI Request ($)",
    "Total QLICI ($)", "Leverage Loan ($)", "Total NMTCs ($)",
    "Estimated Investor Equity ($)", "CDE Fee ($)",
    "Construction Start", "Operations Start",
    "Closing Target Date", "Jobs Created", "Jobs Retained", "Affordable Units Built",
    "Square Feet",
]

# The financial columns, for the cross-surface arithmetic check in
# validation/consistency_check. Named here rather than retyped there so a
# column rename cannot silently drop a figure out of the check.
CURRENCY_COLUMNS = [
    "Total Project Cost ($)", "QEI Request ($)", "Total QLICI ($)",
    "Leverage Loan ($)", "Total NMTCs ($)", "Estimated Investor Equity ($)",
    "CDE Fee ($)",
]
