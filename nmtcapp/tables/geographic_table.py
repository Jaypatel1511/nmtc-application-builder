"""Geographic targeting and distribution table."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def build_geographic_table(pipeline: "Pipeline") -> pd.DataFrame:
    """Build geographic distribution table by state with QEI and project counts.

    Example::

        df = build_geographic_table(pipeline)
    """
    projects = list(pipeline)
    if not projects:
        return pd.DataFrame()

    total_qei = sum(p.qei_request for p in projects)

    state_data: dict = {}
    for p in projects:
        s = p.state
        if s not in state_data:
            state_data[s] = {
                "Project Count": 0, "QEI ($)": 0.0,
                "Deep/Severe Projects": 0,
                "Native Area Projects": 0,
                "HMR Projects": 0,
                "OZ Projects": 0,
            }
        state_data[s]["Project Count"] += 1
        state_data[s]["QEI ($)"] += p.qei_request
        if p.distress_level in ("deep", "severe"):
            state_data[s]["Deep/Severe Projects"] += 1
        if p.is_native_area:
            state_data[s]["Native Area Projects"] += 1
        if p.is_high_migration_rural:
            state_data[s]["HMR Projects"] += 1
        if p.is_opportunity_zone:
            state_data[s]["OZ Projects"] += 1

    # "QEI (% of Total)" IS FORMATTED HERE, AS A STRING, ON PURPOSE.
    #
    # It used to hold the raw fraction (0.3284...) under a header that says
    # "%", and every renderer got it wrong in a different way:
    #
    #   Excel     the column matched no entry in _build_geographic_sheet's
    #             format lists, fell through to the auto-detect branch, and
    #             took FMT_NUMBER ("#,##0") -- so a state holding 32.8% of
    #             pipeline QEI displayed as "0", and the whole column read
    #             0 0 0 0 0 0 1 in the workbook the Word and PDF documents
    #             cross-reference by name as the authoritative attachment.
    #   Word/PDF  _fmt_cell sends a float <= 1000 to f"{val:.2f}" -> "0.33",
    #             which reads as a third of one percent.
    #   Markdown  dumped the raw float, "0.328".
    #
    # A CDE files Appendix C with those figures. Formatting once here fixes
    # all four at a single point: _fmt_cell passes str through unchanged,
    # _df_to_md stringifies, and the Excel writer's final else-branch writes
    # str(val).
    #
    # The alternative was to add the column to excel_builder's pct_cols and
    # fix Word, PDF and markdown separately. Rejected: it is four edits
    # instead of one, and this sheet's format config is already stale --
    # _build_geographic_sheet passes currency_cols/number_cols naming columns
    # that do not exist in this table ("Total QEI ($)", "Deep Distress
    # Count", ...), so a correct pct_cols would sit beside a wrong
    # currency_cols and fix one column while leaving its neighbours
    # misconfigured. Repairing that config is a separate change.
    #
    # KNOWN COST, stated rather than implied: the Excel cell is now text, so
    # it no longer sorts or sums as a number and loses the numeric
    # right-alignment. That is the price of one change point, and it is worth
    # paying against a column that currently reads zero. If this sheet's
    # format config is repaired later, move this back to a float and give it
    # a real pct_cols entry.
    def _pct(qei: float) -> str:
        return f"{(qei / total_qei if total_qei else 0.0):.1%}"

    rows = []
    for state, data in sorted(state_data.items()):
        rows.append({
            "State": state,
            "Project Count": data["Project Count"],
            "QEI ($)": data["QEI ($)"],
            "QEI (% of Total)": _pct(data["QEI ($)"]),
            "Deep/Severe Projects": data["Deep/Severe Projects"],
            "Native Area Projects": data["Native Area Projects"],
            "HMR Projects": data["HMR Projects"],
            "OZ Projects": data["OZ Projects"],
        })

    df = pd.DataFrame(rows)
    # Add totals row
    df.loc[len(df)] = {
        "State": "TOTAL",
        "Project Count": df["Project Count"].sum(),
        "QEI ($)": df["QEI ($)"].sum(),
        # The parts are shares of this same total, so the total is 100% by
        # construction. (A pipeline with projects always has total_qei > 0:
        # PipelineProject.__post_init__ rejects qei_request <= 0, and an empty
        # pipeline returns above before reaching this row.)
        "QEI (% of Total)": "100.0%",
        "Deep/Severe Projects": df["Deep/Severe Projects"].sum(),
        "Native Area Projects": df["Native Area Projects"].sum(),
        "HMR Projects": df["HMR Projects"].sum(),
        "OZ Projects": df["OZ Projects"].sum(),
    }
    return df
