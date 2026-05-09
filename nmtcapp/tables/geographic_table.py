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

    rows = []
    for state, data in sorted(state_data.items()):
        rows.append({
            "State": state,
            "Project Count": data["Project Count"],
            "QEI ($)": data["QEI ($)"],
            "QEI (% of Total)": data["QEI ($)"] / total_qei if total_qei else 0.0,
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
        "QEI (% of Total)": 1.0,
        "Deep/Severe Projects": df["Deep/Severe Projects"].sum(),
        "Native Area Projects": df["Native Area Projects"].sum(),
        "HMR Projects": df["HMR Projects"].sum(),
        "OZ Projects": df["OZ Projects"].sum(),
    }
    return df
