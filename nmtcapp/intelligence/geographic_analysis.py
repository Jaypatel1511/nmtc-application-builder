"""Geographic diversity metrics for NMTC pipelines."""
from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from nmtcapp.data.schema import MIN_GEOGRAPHIC_DIVERSITY

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# States typically classified as non-metro / rural (simplified)
_RURAL_STATES = {"MS", "WV", "AR", "MT", "WY", "SD", "ND", "VT", "ME", "ID", "NM", "KS"}

# Rough MSA lookup — maps state to approximate MSA count in pipeline
# (In production, this would use proper CBSA codes from census data.)
_STATE_MSA_MAP = {
    "IL": "Chicago-Naperville-Elgin", "TX": "Houston-The Woodlands",
    "NY": "New York-Newark-Jersey City", "CA": "Los Angeles-Long Beach",
    "OH": "Cleveland-Elyria", "GA": "Atlanta-Sandy Springs",
    "FL": "Miami-Fort Lauderdale", "PA": "Philadelphia-Camden",
    "LA": "New Orleans-Metairie", "TN": "Memphis",
    "WI": "Milwaukee-Waukesha", "MO": "St. Louis",
    "NC": "Charlotte-Concord", "AZ": "Phoenix-Mesa",
    "MI": "Detroit-Warren", "IN": "Indianapolis-Carmel",
    "MS": "Jackson", "KS": "Kansas City",
    "MD": "Baltimore-Columbia", "NM": "Albuquerque",
}


def analyze_geographic_diversity(pipeline: "Pipeline") -> dict:
    """Compute geographic diversity metrics for the pipeline.

    Returns a dict with:
    - ``states_count`` – unique state count
    - ``states`` – list of unique state codes
    - ``msa_count`` – estimated unique metro areas
    - ``urban_pct`` – fraction of QEI in urban (metro) markets
    - ``rural_pct`` – fraction of QEI in rural markets
    - ``hhi`` – Herfindahl-Hirschman Index of state concentration (0–10,000)
    - ``state_breakdown`` – per-state QEI dollars, project count, pct
    - ``meets_diversity_minimum`` – bool, ≥ MIN_GEOGRAPHIC_DIVERSITY states
    - ``geographic_concentration_label`` – 'highly_concentrated', 'moderate', 'diverse'

    Example::

        result = analyze_geographic_diversity(pipeline)
        print(f"States served: {result['states_count']}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_geo_result()

    total_qei = sum(p.qei_request for p in projects)
    if total_qei == 0:
        return _empty_geo_result()

    state_qei: dict = {}
    state_count: Counter = Counter()
    urban_qei = 0.0

    for p in projects:
        state = p.state.upper()
        state_qei[state] = state_qei.get(state, 0.0) + p.qei_request
        state_count[state] += 1
        if state not in _RURAL_STATES:
            urban_qei += p.qei_request

    states = sorted(state_qei.keys())
    states_count = len(states)

    # HHI: sum of squared market shares × 10,000
    hhi = sum((v / total_qei) ** 2 for v in state_qei.values()) * 10_000

    state_breakdown = {
        st: {
            "qei_dollars": round(state_qei[st]),
            "project_count": state_count[st],
            "pct_of_total_qei": state_qei[st] / total_qei,
            "msa": _STATE_MSA_MAP.get(st, "Unknown MSA"),
        }
        for st in states
    }

    msa_set = {_STATE_MSA_MAP.get(st, st) for st in states}

    return {
        "states_count": states_count,
        "states": states,
        "msa_count": len(msa_set),
        "msas": sorted(msa_set),
        "urban_pct": urban_qei / total_qei,
        "rural_pct": 1.0 - (urban_qei / total_qei),
        "hhi": round(hhi, 1),
        "state_breakdown": state_breakdown,
        "total_qei": total_qei,
        "meets_diversity_minimum": states_count >= MIN_GEOGRAPHIC_DIVERSITY,
        "geographic_concentration_label": _concentration_label(hhi),
    }


def _concentration_label(hhi: float) -> str:
    if hhi >= 5_000:
        return "highly_concentrated"
    if hhi >= 2_500:
        return "moderate"
    return "diverse"


def _empty_geo_result() -> dict:
    return {
        "states_count": 0,
        "states": [],
        "msa_count": 0,
        "msas": [],
        "urban_pct": 0.0,
        "rural_pct": 0.0,
        "hhi": 0.0,
        "state_breakdown": {},
        "total_qei": 0.0,
        "meets_diversity_minimum": False,
        "geographic_concentration_label": "highly_concentrated",
    }
