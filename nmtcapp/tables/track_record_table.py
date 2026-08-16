"""Section C/E CDE track record deployment history table."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nmtcapp.core.cde import CDEProfile

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    "fully_deployed":    "Fully Deployed",
    "partially_deployed":"Partially Deployed",
    "in_deployment":     "In Deployment",
    "pending":           "Pending Deployment",
}


def build_track_record_table(cde: "CDEProfile") -> pd.DataFrame:
    """Build the CDE deployment history table from CDEProfile.prior_awards.

    Formats prior award data into the CDFI Fund Section C/E track record table.

    Example::

        df = build_track_record_table(cde)
    """
    awards = cde.prior_awards
    if not awards:
        return pd.DataFrame(columns=[
            "Award Year", "Allocation ($)", "Deployment Status",
            "States Deployed", "Sectors", "Notes",
        ])

    rows = []
    for award in sorted(awards, key=lambda a: a.get("year", 0)):
        rows.append({
            "Award Year":         award.get("year", "N/A"),
            # NOT `award.get("amount", 0)` (1.2.1 B-2 sweep). A prior award
            # whose amount the CDE left out rendered "$0" — a statement that
            # the round was worth nothing, in the table the Fund reads to
            # assess deployment history. None reaches _cell_format, which
            # prints the same em dash Appendix A uses for an absent figure.
            "Allocation ($)":     award.get("amount"),
            "Deployment Status":  _STATUS_LABELS.get(
                award.get("deployment_status", ""), award.get("deployment_status", "")
            ),
            "States Deployed":    ", ".join(award.get("states", [])),
            "Sectors":            ", ".join(award.get("sectors", [])),
            "Notes":              award.get("notes", ""),
        })

    df = pd.DataFrame(rows)
    # Totals row
    total = cde.total_prior_allocation()
    deployed_count = sum(
        1 for a in awards if a.get("deployment_status") == "fully_deployed"
    )
    # SAY WHEN THE TOTAL IS NOT A TOTAL (1.2.1 B-2 sweep). total_prior_allocation
    # sums `a.get("amount", 0)`, so an award the CDE recorded without an amount
    # contributes nothing and the footer still read "$X total prior allocation"
    # as though every round were counted. The sum cannot be repaired — the
    # missing figure does not exist — so the note stops asserting completeness.
    missing_amounts = sum(1 for a in awards if a.get("amount") is None)
    note = f"${total:,.0f} total prior allocation"
    if missing_amounts:
        note += (
            f" across {len(awards) - missing_amounts} of {len(awards)} awards — "
            f"{missing_amounts} award(s) record no amount and are NOT in this "
            "total. [CDE TO COMPLETE]"
        )
    df.loc[len(df)] = {
        "Award Year": "TOTALS",
        "Allocation ($)": total,
        "Deployment Status": f"{deployed_count} rounds fully deployed",
        "States Deployed": f"{len({s for a in awards for s in a.get('states', [])})} states",
        "Sectors": "",
        "Notes": note,
    }
    return df
