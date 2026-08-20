"""Geographic diversity metrics for NMTC pipelines."""
from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from nmtcapp.data.schema import MIN_GEOGRAPHIC_DIVERSITY

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# _RURAL_STATES IS GONE (1.4.0 R2). It was a twelve-state set — MS WV AR MT WY
# SD ND VT ME ID NM KS — under a comment that called itself "(simplified)", and
# it had three defects, not one:
#
#   1. NO BASIS. The map below it conceded "(In production, this would use
#      proper CBSA codes from census data.)" An acknowledged placeholder,
#      shipping as a live computation on three screens a CDE reads.
#   2. IT WAS A COMPLEMENT, NOT A DETERMINATION, and this was the worst of the
#      three. urban_qei summed every project whose state was NOT in the twelve,
#      and rural_pct was 1 − urban_pct. So Alaska, Nebraska, Iowa, Oklahoma and
#      thirty-four other states were counted METROPOLITAN BY DEFAULT, as was
#      every project the tool had failed to verify. Nothing in the module ever
#      determined that a project was metropolitan; it only ever failed to find
#      it in a list.
#   3. THREE STATES WERE COUNTED BOTH WAYS IN THIS FILE. MS, KS and NM were in
#      the set and in _STATE_MSA_MAP four lines below — as Jackson, Kansas City
#      and Albuquerque.
#
# The replacement is PipelineProject.is_non_metro: the OMB Non-Metropolitan
# County designation for the tract this package geocoded, read per project from
# nmtc-mapper. See _split_by_metro_status below for what happens to a project
# whose status is not determined — which is the part a complement cannot
# express at all.

# _STATE_MSA_MAP IS KEPT, and that is a separate ruling from the one above.
#
# It does not feed the metropolitan determination and never did — it feeds
# ``msa_count``, ``msas`` and the per-state ``msa`` label in state_breakdown.
# Deleting it as collateral to R2 would remove the MSA figure from the CLI
# summary, the Streamlit Geographic tab and the state breakdown, which is a
# user-visible removal that has nothing to do with the defect being fixed.
#
# IT IS STILL WRONG, AND IS RECORDED RATHER THAN REPAIRED. One MSA per state is
# not a CBSA lookup: it collapses every metro in a state to a single name, so
# ``msa_count`` cannot exceed ``states_count`` and equals it for any pipeline
# whose states are all in the map. A twenty-project pipeline across nineteen
# states reports nineteen MSAs regardless of how those projects are actually
# distributed. Fixing it means carrying CBSA codes per tract — a feature, and
# nmtc-mapper does not currently return one. 1.4.x.
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
    - ``non_metro_pct`` – share of QEI in verified Non-Metropolitan Counties
    - ``metro_pct`` – share of QEI in verified Metropolitan Counties
    - ``metro_undetermined_pct`` – share of QEI whose county status is unknown
    - ``metro_status_qei`` – the three buckets in dollars, and their counts
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

    for p in projects:
        state = p.state.upper()
        state_qei[state] = state_qei.get(state, 0.0) + p.qei_request
        state_count[state] += 1

    metro_status = _split_by_metro_status(projects, total_qei)

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
        "non_metro_pct": metro_status["non_metro_pct"],
        "metro_pct": metro_status["metro_pct"],
        "metro_undetermined_pct": metro_status["metro_undetermined_pct"],
        "metro_status_qei": metro_status["metro_status_qei"],
        "hhi": round(hhi, 1),
        "state_breakdown": state_breakdown,
        "total_qei": total_qei,
        "meets_diversity_minimum": states_count >= MIN_GEOGRAPHIC_DIVERSITY,
        "geographic_concentration_label": _concentration_label(hhi),
    }


def _split_by_metro_status(projects: list, total_qei: float) -> dict:
    """Split pipeline QEI three ways by OMB Non-Metropolitan County status.

    THE THIRD BUCKET IS THE POINT (1.4.0 R2). The metric this replaces was a
    two-way split that summed to 1.0 because it was arithmetic, not
    measurement: ``rural_pct = 1 − urban_pct``, where "urban" meant "in a state
    absent from a hard-coded list of twelve". Nothing was ever determined to be
    metropolitan, so a project the tool could not verify — and a project in any
    of the thirty-eight unlisted states — landed in the metropolitan bucket
    silently and made that bucket look measured.

    So the honest replacement is three-way, and it is not reducible to two:

    ==================================  ============================
    ``project.is_non_metro``            bucket
    ==================================  ============================
    ``True``                            non-metropolitan
    ``False``                           metropolitan
    ``None``                            **not determined**
    ==================================  ============================

    ``None`` IS NOT ``False``. A tract whose metro status nmtc-mapper could not
    resolve is not a metropolitan tract; it is an unknown one, and the dollars
    in it belong to neither answer.

    "THE PROJECT NEVER GEOCODED" NEEDS NO SEPARATE ARM, and stating why is
    better than adding a redundant one. ``nmtc_mapper_adapter`` leaves every
    eligibility field ``None`` on all three of its indeterminate branches — a
    geocode failure, a typed mapper error, and a tract absent from the CDFI
    Fund's 85,395-row table — so an ungeocoded project reaches this function
    with ``is_non_metro is None`` and falls into the third bucket by the rule
    above. Testing ``geocode_success`` as well would add an arm that can only
    agree, and would then disagree wrongly in the one case where they diverge:
    a pre-enriched pipeline (``Pipeline.sample()``, every fixture) carries a
    populated ``is_non_metro`` with ``geocode_success`` still ``None``, and
    that determination stands.

    The three shares sum to 1.0 for any pipeline with QEI. Callers must render
    all three or say what they dropped: a donut that silently omits the
    undetermined slice is the same defect as a numerator that silently excludes
    it, drawn instead of computed.

    Example::

        split = _split_by_metro_status(projects, total_qei)
        split["non_metro_pct"] + split["metro_pct"] \
            + split["metro_undetermined_pct"]   # -> 1.0
    """
    buckets = {"non_metro": 0.0, "metro": 0.0, "undetermined": 0.0}
    counts = {"non_metro": 0, "metro": 0, "undetermined": 0}

    for project in projects:
        status = getattr(project, "is_non_metro", None)
        if status is True:
            key = "non_metro"
        elif status is False:
            key = "metro"
        else:
            key = "undetermined"
        buckets[key] += project.qei_request
        counts[key] += 1

    if counts["undetermined"]:
        logger.info(
            "%d of %d projects (%.0f%% of QEI) have no Non-Metropolitan County "
            "determination — reported as a third bucket, not as metropolitan",
            counts["undetermined"], len(projects),
            100.0 * buckets["undetermined"] / total_qei,
        )

    return {
        "non_metro_pct": buckets["non_metro"] / total_qei,
        "metro_pct": buckets["metro"] / total_qei,
        "metro_undetermined_pct": buckets["undetermined"] / total_qei,
        "metro_status_qei": {
            "non_metro": round(buckets["non_metro"]),
            "metro": round(buckets["metro"]),
            "undetermined": round(buckets["undetermined"]),
            "non_metro_projects": counts["non_metro"],
            "metro_projects": counts["metro"],
            "undetermined_projects": counts["undetermined"],
        },
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
        # An empty pipeline determines nothing about anything, so all three
        # shares are 0.0 and they do NOT sum to 1.0 here. That is deliberate:
        # the alternative — metro_undetermined_pct = 1.0 — would assert that
        # some quantity of dollars is of unknown status, and there are no
        # dollars. Callers rendering the split must handle a zero-QEI pipeline
        # by saying so, not by drawing a full ring of "not determined".
        "non_metro_pct": 0.0,
        "metro_pct": 0.0,
        "metro_undetermined_pct": 0.0,
        "metro_status_qei": {
            "non_metro": 0.0, "metro": 0.0, "undetermined": 0.0,
            "non_metro_projects": 0, "metro_projects": 0,
            "undetermined_projects": 0,
        },
        "hhi": 0.0,
        "state_breakdown": {},
        "total_qei": 0.0,
        "meets_diversity_minimum": False,
        "geographic_concentration_label": "highly_concentrated",
    }
