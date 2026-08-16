"""Distress level concentration analysis for NMTC pipelines."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DEEP DISTRESS IS A STRICT SUBSET OF SEVERE DISTRESS. READ THIS BEFORE
# TOUCHING ANY ARITHMETIC OR ANY LABEL BELOW.
#
# The CDFI Fund's NMTC LIC Eligibility workbook (2016–2020 ACS) publishes the
# two flags in adjacent columns, and each states its own criterion in its own
# header:
#
#   column O  Severe distress = LIC AND (Poverty>30%; MFI<=60%; Unemployment>=1.5)
#   column P  Deep   distress = LIC AND (Poverty>40%; MFI<=40%; Unemployment>=2.5)
#
# Every deep prong implies its severe counterpart — >40% implies >30%, <=40%
# implies <=60%, >=2.5 implies >=1.5 — so deep implies severe by construction.
# VERIFIED EMPIRICALLY against the shipped file rather than inferred from the
# headers, across all 85,395 tracts:
#
#   severe=NO,  deep=NO    64,213
#   severe=YES, deep=NO    13,121
#   severe=YES, deep=YES    8,061
#   severe=NO,  deep=YES         0     <- the cell that would have to be
#                                         non-empty for deep and severe to be
#                                         disjoint. It is empty.
#
# THIS PACKAGE'S BUCKETS ARE DISJOINT; THE FUND'S FLAGS ARE NESTED. Each
# project carries ONE distress_level, so a deep-distress tract lands in the
# "deep" bucket and nowhere else. The bucket named "severe" therefore holds
# tracts that are severe AND NOT deep — which is NOT what a reader of the
# phrase "severely distressed" understands, and not what the Fund's severe
# flag means.
#
# Hence the key names below. The exclusive bucket says "excluding deep" in its
# own name, and the inclusive share — the one that answers the Fund's 85%
# higher-distress bar and the one Appendix B's "Severely Distressed Flag"
# column reports per project — is ``pct_deep_or_severe``.
#
# 1.2.1 shipped ``pct_severe`` for the exclusive bucket while rendering it
# under the label "QEI in Severely Distressed Tracts". On a pipeline whose
# distressed tracts are all deep, that row read 0.0% in Section B while
# Appendix B flagged the same projects "Yes" — one filing, two answers.
# ---------------------------------------------------------------------------
DEEP_IS_SUBSET_OF_SEVERE = True

#: What each rendered label must be computed from. Consulted by the pin in
#: tests/test_121_financial_tables.py so the relation cannot be re-broken
#: silently by a renaming.
DISTRESS_SHARE_SEMANTICS = {
    "pct_deep": "deep distress only — the basis of the Fund's 20% bar",
    "pct_severe_excluding_deep": (
        "severely distressed but NOT also deep — an internal residual, not a "
        "figure any CDFI Fund question asks for"
    ),
    "pct_deep_or_severe": (
        "severely distressed, deep distress included — the basis of the Fund's "
        "85% bar and the share Appendix B's per-project flag reports"
    ),
}


def analyze_distress_concentration(pipeline: "Pipeline") -> dict:
    """Compute distress level breakdown for a pipeline.

    Returns a dict with:
    - ``pct_deep`` – fraction of QEI in deep-distress tracts
    - ``pct_severe_excluding_deep`` – fraction of QEI in tracts that are
      severely distressed but NOT also deep. Named for what it is: deep
      distress is a strict subset of severe distress in the Fund's own
      workbook (see :data:`DEEP_IS_SUBSET_OF_SEVERE`), so this is a residual
      and NOT "the severe share".
    - ``pct_deep_or_severe`` – THE severe share, deep included. This is what
      the Fund's severe-distress flag means and what the 85% higher-distress
      commitment is measured against.
    - ``pct_lic`` – fraction of QEI in standard LIC tracts
    - ``pct_non_lic`` – fraction of QEI in ineligible tracts
    - ``pct_native_area`` – fraction of QEI in NMTC Native Areas
    - ``pct_high_migration_rural`` – fraction of QEI in HMR tracts
    - ``dollars_by_distress`` – absolute QEI dollars in each category
    - ``pct_eligible`` – fraction of QEI in any eligible (LIC) tract
    - ``meets_min_threshold`` – bool, ≥ min_deep_distress competitive threshold
    - ``meets_target_threshold`` – bool, ≥ target_deep_distress threshold
    - ``project_count_by_distress`` – project count per level

    Example::

        result = analyze_distress_concentration(pipeline)
        print(f"Deep/Severe: {result['pct_deep_or_severe']:.0%}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_distress_result()

    total_qei = sum(p.qei_request for p in projects)
    if total_qei == 0:
        return _empty_distress_result()

    buckets = {"deep": 0.0, "severe": 0.0, "lic": 0.0, "ineligible": 0.0, "unknown": 0.0}
    counts = {"deep": 0, "severe": 0, "lic": 0, "ineligible": 0, "unknown": 0}
    native_qei = 0.0
    hmr_qei = 0.0
    us_territory_qei = 0.0
    persistent_poverty_qei = 0.0
    below_market_rate_qei = 0.0
    unrelated_entity_qei = 0.0

    for p in projects:
        level = p.distress_level or "unknown"
        if level not in buckets:
            level = "unknown"
        buckets[level] += p.qei_request
        counts[level] += 1
        if p.is_native_area:
            native_qei += p.qei_request
        if p.is_high_migration_rural:
            hmr_qei += p.qei_request
        if p.is_us_territory:
            us_territory_qei += p.qei_request
        if p.is_persistent_poverty:
            persistent_poverty_qei += p.qei_request
        if p.is_below_market_rate:
            below_market_rate_qei += p.qei_request
        if p.is_unrelated_entity:
            unrelated_entity_qei += p.qei_request

    pct_deep = buckets["deep"] / total_qei
    # The bucket, not the concept. A project whose tract is deep-distress is
    # counted in buckets["deep"] and nowhere else, so this is the severe share
    # LESS the deep share — see DEEP_IS_SUBSET_OF_SEVERE above.
    pct_severe_excluding_deep = buckets["severe"] / total_qei
    pct_deep_or_severe = pct_deep + pct_severe_excluding_deep
    pct_lic = buckets["lic"] / total_qei
    pct_non_lic = (buckets["ineligible"] + buckets["unknown"]) / total_qei
    pct_eligible = pct_deep_or_severe + pct_lic

    min_threshold = TARGET_DISTRESS_THRESHOLDS["min_deep_distress"]
    target_threshold = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]

    return {
        "pct_deep": pct_deep,
        "pct_severe_excluding_deep": pct_severe_excluding_deep,
        "pct_deep_or_severe": pct_deep_or_severe,
        "pct_lic": pct_lic,
        "pct_non_lic": pct_non_lic,
        "pct_native_area": native_qei / total_qei,
        "pct_high_migration_rural": hmr_qei / total_qei,
        "pct_us_territories": us_territory_qei / total_qei,
        "pct_persistent_poverty": persistent_poverty_qei / total_qei,
        "pct_below_market_rate": below_market_rate_qei / total_qei,
        "pct_unrelated_entity": unrelated_entity_qei / total_qei,
        "pct_eligible": pct_eligible,
        "dollars_by_distress": {k: round(v) for k, v in buckets.items()},
        "project_count_by_distress": counts,
        "total_qei": total_qei,
        "meets_min_threshold": pct_deep_or_severe >= min_threshold,
        "meets_target_threshold": pct_deep_or_severe >= target_threshold,
    }


# ``vs_historical_winners`` / ``_assess_vs_winners`` were REMOVED in 1.2.0.
#
# The function read only the CDE's own pct_deep_or_severe and returned
# "top_quartile" / "competitive" / "below_average" / "uncompetitive" off a
# hardcoded threshold ladder. No distribution of historical applicants was
# ever loaded, and none is published — the CDFI Fund publishes a commitment
# threshold, not a winner percentile curve. Its ladder (0.85/0.75/0.50) also
# disagreed with WINNER_PATTERN_THRESHOLDS (0.75/0.50/0.25) in the same
# package.
#
# It reached the first paragraph a reviewer reads: "placing us in the top
# quartile tier of CDFI Fund applicants historically" (Word/PDF), "ranking in
# the top quartile tier of historical NMTC applications" (Markdown), and
# "Historical Distress Rank: Top Quartile" in Section A's overview table.
#
# Deleted rather than hedged, for the same reason nmtc-mapper dropped
# is_nmtc_native_area: a value that can never be obtained must not exist as a
# field, because a consumer then reads the absence of a positive as meaningful.
# All three renderers defaulted the missing key to 'competitive', which
# manufactured a tier out of no data at all — deleting the field deletes that
# default too.


def _empty_distress_result() -> dict:
    buckets = {"deep": 0, "severe": 0, "lic": 0, "ineligible": 0, "unknown": 0}
    return {
        "pct_deep": 0.0,
        "pct_severe_excluding_deep": 0.0,
        "pct_deep_or_severe": 0.0,
        "pct_lic": 0.0,
        "pct_non_lic": 0.0,
        "pct_native_area": 0.0,
        "pct_high_migration_rural": 0.0,
        "pct_us_territories": 0.0,
        "pct_persistent_poverty": 0.0,
        "pct_below_market_rate": 0.0,
        "pct_unrelated_entity": 0.0,
        "pct_eligible": 0.0,
        "dollars_by_distress": buckets,
        "project_count_by_distress": dict(buckets),
        "total_qei": 0.0,
        "meets_min_threshold": False,
        "meets_target_threshold": False,
    }
