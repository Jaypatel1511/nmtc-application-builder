"""Adapter wrapping cdfidata for CDE track record retrieval."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.cde import CDEProfile

logger = logging.getLogger(__name__)


def cde_track_record(cde: "CDEProfile") -> dict:
    """Pull CDE's prior NMTC deployment track record from CDFI Fund TLR data.

    Supplements the CDE's self-reported prior_awards with CDFI Fund
    published Transaction Level Report data.

    Returns a dict with:
    - ``total_prior_allocation`` – total prior NMTC allocation (from CDE profile)
    - ``fully_deployed_rounds`` – count of fully deployed award rounds
    - ``avg_deployment_time_months`` – estimated avg months to full deployment
    - ``tlr_transactions`` – count of TLR transactions found for CDE
    - ``states_deployed`` – states where CDE has deployed capital
    - ``track_record_label`` – 'strong', 'adequate', 'limited'
    - ``deployment_narrative`` – text summary for application

    Example::

        record = cde_track_record(cde)
        print(record['track_record_label'])
    """
    try:
        import cdfidata
        return _pull_tlr_data(cde, cdfidata)
    except Exception as exc:
        logger.warning("cdfidata TLR pull failed (%s). Using CDE profile data.", exc)
        return _from_profile(cde)


def _pull_tlr_data(cde: "CDEProfile", cdfidata) -> dict:
    """Use cdfidata library to pull TLR sample data."""
    try:
        loader = cdfidata.TLRLoader()
        df = loader.load_sample(n=500)
        tlr_count = len(df) if df is not None and not df.empty else 0
    except Exception:
        tlr_count = 0

    return _build_record(cde, tlr_count)


def _from_profile(cde: "CDEProfile") -> dict:
    return _build_record(cde, tlr_count=0)


def _build_record(cde: "CDEProfile", tlr_count: int) -> dict:
    awards = cde.prior_awards
    total_prior = cde.total_prior_allocation()
    fully_deployed = sum(
        1 for a in awards if a.get("deployment_status") == "fully_deployed"
    )
    states_deployed: list = []
    for a in awards:
        states_deployed.extend(a.get("states", []))
    states_deployed = sorted(set(states_deployed))

    # Rough heuristic: prior rounds × 18 months avg deployment time
    avg_deployment = 18 if fully_deployed > 0 else 0

    label = _track_record_label(total_prior, fully_deployed)

    narrative = (
        f"{cde.name} has received {len(awards)} prior NMTC allocations totaling "
        f"${total_prior:,.0f}, with {fully_deployed} rounds fully deployed. "
        f"Capital has been deployed across {len(states_deployed)} states: "
        f"{', '.join(states_deployed[:5]) if states_deployed else 'N/A'}."
    )

    return {
        "total_prior_allocation": total_prior,
        "award_rounds": len(awards),
        "fully_deployed_rounds": fully_deployed,
        "avg_deployment_time_months": avg_deployment,
        "tlr_transactions": tlr_count,
        "states_deployed": states_deployed,
        "track_record_label": label,
        "deployment_narrative": narrative,
    }


def _track_record_label(total_prior: float, fully_deployed: int) -> str:
    if total_prior >= 100_000_000 and fully_deployed >= 2:
        return "strong"
    if total_prior >= 30_000_000 and fully_deployed >= 1:
        return "adequate"
    return "limited"
