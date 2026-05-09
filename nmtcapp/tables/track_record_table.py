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
            "Allocation ($)":     award.get("amount", 0),
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
    df.loc[len(df)] = {
        "Award Year": "TOTALS",
        "Allocation ($)": total,
        "Deployment Status": f"{deployed_count} rounds fully deployed",
        "States Deployed": f"{len({s for a in awards for s in a.get('states', [])})} states",
        "Sectors": "",
        "Notes": f"${total:,.0f} total prior allocation",
    }
    return df
