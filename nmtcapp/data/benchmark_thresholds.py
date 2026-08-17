"""
Scoring thresholds for NMTC applications.

Two sections:

SECTION A — CY 2024-2025 scoring thresholds, MIXED PROVENANCE
  Most are read from the CY 2024-2025 NMTC Allocation Application Review Process
  (https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf).
  SOME ARE NOT, and this header used to say they all were.

  It read "CDFI Fund Published Thresholds" and "These are the explicit values
  the CDFI Fund uses to evaluate applications". That was the provenance claim
  standing behind five separate false attributions found in the 1.2.2 sweep,
  and it was false of at least four constants in this very section:

    UNRELATED_ENTITIES_MIN_PCT     the Fund publishes NO percentage here
    TRACK_RECORD_DEPLOYMENT_MIN    the Fund's 90% is a different quantity
    TOP_TIER_AGGREGATE_MIN         no tier above Highly Qualified is published
    TOP_TIER_SECTION_MIN           same
    SPECIAL_TARGETING_BONUS_PCT    not located in the Review Process at all

  Per-constant provenance is now stated at each constant below. A blanket
  "published" header is how an unsourced number acquires a citation it was
  never given: nothing was verified, but everything under the heading read as
  though it had been.

SECTION B — Legacy winner-pattern thresholds (CY2020–2024)
  Used by HistoricalBenchmarks (benchmarks.py) for the 9-metric tier comparison.
  Kept for backward compatibility. These are inferred from award announcements,
  not published by the CDFI Fund.
"""
from __future__ import annotations

# ===========================================================================
# SECTION A — CY 2024-2025 scoring thresholds, MIXED PROVENANCE
# Primary source: CY_2024_25_NMTC_Program_Review_Process.pdf (7pp, retrieved
# and text-extracted 2026-08-16). Each constant below states whether that
# document actually contains it. Where it does not, the constant says so.
# Rulings are recorded in tests/fund_attribution_allowlist.txt as D1-D6.
# ===========================================================================

# --- Community Outcomes thresholds ---
# CY 2024-2025 NMTC Program Review Process, "Targeting Areas of Higher Distress
# (Question 25)", quoted verbatim from the published document:
#
#   "The Applicant indicated that it will commit to providing at least 85% of
#    its QLICIs in specified areas of severe distress and/or areas
#    characterized by multiple indicia of distress. The Applicant indicated
#    that it will commit to providing at least 20% of its QLICIs to 'Deep
#    Distress' areas."
#
# Note what the 85% actually covers: severe distress OR multiple indicia — the
# Question 25 list of twelve, not the severe-distress tier alone. Rendering it
# as a "Severe Distress Threshold" narrowed the Fund's own category, and the
# separate 20% Deep Distress commitment was not reported at all.
SEVERE_DISTRESS_MIN_PCT = 0.85       # >=85% of QLICIs in areas of higher distress
# ASSIGNED ONCE. This name was assigned twice, on consecutive lines, with the
# same value and two different comments. Found by the 1.2.1 mutation harness:
# changing the first assignment to 0.05 moved nothing, because the second
# reassigned 0.20 immediately afterwards, and the constant pin stayed green
# over what looked like a mutated threshold. A duplicate assignment is a live
# hazard even when the two values agree today — the next editor changes one of
# them and the other silently wins.
DEEP_DISTRESS_MIN_PCT = 0.20         # >=20% of QLICIs in "Deep Distress" areas
# NOT LOCATED IN THE REVIEW PROCESS. The document contains no "Special
# Targeting" criterion and none of its four categories — grep for "special
# targeting", "persistent poverty", "territor", "native area", "high migration"
# returns zero hits across all seven pages. The categories are real NMTC
# concepts and may be set out in the NOAA or the Application itself; neither
# has been retrieved, so this is COULD-NOT-ESTABLISH, not disproved.
SPECIAL_TARGETING_BONUS_PCT = 0.10   # 10%+ in a special targeting category triggers bonus

# --- Business Strategy thresholds ---
# p.7 Part II.A.4, and accurate: "At least 70% of the Applicant's proposed NMTC
# investments were supported by a track record of similar business types and
# activity types."
TRACK_RECORD_PIPELINE_ALIGNMENT_MIN = 0.70   # 70%+ NMTC pipeline supported by similar prior activity
# D2 — THE COMMENT ON THIS LINE IS WRONG AND THE FIX IS NEXT ROUND. p.7 Part
# II.A.4 states the applicant's "most recent 5-year direct financing track
# record was 90% or more of its projected NMTC deployment in Exhibit A" — a
# track-record-to-projection ratio. "Prior allocation deployed on schedule" is
# a different quantity, and the Fund attaches no percentage to it (p.4 reviews
# whether prior-year Allocatees issued "the minimum requisite QEIs" with no
# figure). Rendered at recommendations.py:326, methodology.md:45,
# 4_About_and_Methodology.py:90.
TRACK_RECORD_DEPLOYMENT_MIN = 0.90           # 90%+ of prior allocation deployed on schedule
# D1 — NOT A PORTFOLIO SHARE. p.6 Part II.A.1: 100% of QLICIs must take one of
# four forms, one of which is "debt with interest rates at least 50%
# below-market". The 50% is the DEPTH OF THE DISCOUNT ON AN INDIVIDUAL LOAN.
# This constant is divided into a QEI-weighted portfolio share at
# win_probability.py:435, which is not a comparison the Fund's sentence
# supports. Fix is next round; changing it moves scored figures.
PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT = 0.50  # 50%+ below-market rate for full product flexibility credit
# D1 — p.6 Part II.A.1: "debt that otherwise satisfies at least five indicia of
# flexible or non-traditional rates and terms". One of the four QUALIFYING
# FORMS an individual QLICI may take, not an application-level alternative to
# the share above. The two are rendered as an OR at the wrong level.
PRODUCT_FLEXIBILITY_MIN_INDICIA = 5          # Or 5+ indicia of flexible terms for full credit

# --- Priority Points thresholds ---
DBC_PRIORITY_YEARS_MIN = 5            # 5+ years DBC focus for full DBC priority points
# p.7 Part II.B.1, and accurate: "at least 70% of its total dollar volume of
# direct financing activities has been provided to DBCs", after "five or more
# years of experience". UPHELD by the 1.2.2 sweep — do not sweep this one.
DBC_VOLUME_PCT_MIN = 0.70             # 70%+ of direct financing volume to DBCs for full credit
# D3 — INVENTED. p.7 Part II.B.2 (Question 23): the Applicant commits "to using
# substantially all of the proceeds of its QEIs" — NO PERCENTAGE, here or in
# the corroborating sentence on p.2. The only three "90%" strings in the whole
# document are 16.90% of awardees being Rural CDEs, 90%-of-maximum non-metro,
# and the p.7 track-record ratio. Treas. Reg. §1.45D-1(c)(5)(i) defines
# "substantially all" as at least 85 percent (75 in year 7), so 90% is not the
# regulation's figure either. THE DENOMINATOR (QEI proceeds) IS CORRECT and
# must NOT be changed — this is the one share this package has right.
UNRELATED_ENTITIES_MIN_PCT = 0.90    # 90%+ QEIs to unrelated entities for full unrelated-entity credit

# --- Non-Metro / Rural commitments ---
NON_METRO_MIN_COMMITMENT_PCT = 0.20        # 20% minimum non-metro commitment
NON_METRO_MAX_COMMITMENT_FACTOR = 0.90     # Must commit larger of min or 90% of max
RURAL_CDE_NON_METRO_THRESHOLD = 0.50       # 50% non-metro to qualify as Rural CDE

# --- Highly Qualified gating thresholds ---
# p.3 Step 2, verbatim: "(i) an aggregate score of at least 40 out of a
# possible total of 50 points in each of the two scored Application sections;
# and (ii) an aggregate base score (excluding priority points) of at least 85
# points." Both UPHELD.
HIGHLY_QUALIFIED_AGGREGATE_MIN = 85    # 85+ aggregate base score to be "Highly Qualified"
HIGHLY_QUALIFIED_SECTION_MIN = 40      # Each section must score 40+ to be "Highly Qualified"
# D4 — HOUSE, NOT PUBLISHED. The Review Process publishes the gate above and
# NOTHING ABOVE IT. "Top Tier" is this package's own label and these two cut
# points are unsourced. recommendations.py:826 already says so in the rendered
# text; methodology.md:99, win-alignment.md:87 and
# 4_About_and_Methodology.py:158 do not, and both docs tables introduce
# themselves as the CDFI Fund's gating process.
TOP_TIER_AGGREGATE_MIN = 95            # 95+ aggregate base score for "Top Tier"
TOP_TIER_SECTION_MIN = 45             # Each section must score 45+ for "Top Tier"

# --- Section maximums (for reference) ---
BUSINESS_STRATEGY_MAX = 50
COMMUNITY_OUTCOMES_MAX = 50
PRIORITY_POINTS_MAX = 10

# --- Historical program data (CY 2024-2025) ---
TOTAL_APPLICANTS_CY2024_25 = 216
TOTAL_REQUEST_CY2024_25_B = 19.2       # $19.2B requested
TOTAL_AVAILABLE_CY2024_25_B = 10.0     # $10B available
RURAL_CDE_AWARDS_PCT = 0.169           # 16.9% of awards historically to Rural CDEs

# --- Sub-score maximums within each section ---
PRODUCT_FLEXIBILITY_MAX = 10
PIPELINE_CREDIBILITY_MAX = 15
TRACK_RECORD_STRENGTH_MAX = 15
TRACK_RECORD_ALIGNMENT_MAX = 10

HIGHER_DISTRESS_MAX = 15
DEEP_DISTRESS_MAX = 10
SPECIAL_TARGETING_MAX = 5
COMMUNITY_OUTCOMES_QUALITY_MAX = 10
COMMUNITY_ACCOUNTABILITY_MAX = 10

DBC_TRACK_RECORD_MAX = 5
UNRELATED_ENTITIES_MAX = 5


# ===========================================================================
# SECTION B — Legacy Winner-Pattern Thresholds (CY2020–2024)
# Used by HistoricalBenchmarks (benchmarks.py). Inferred from award data.
# ===========================================================================

WINNER_PATTERN_THRESHOLDS: dict = {
    "min_deep_distress_pct": {
        "strong": 0.75,
        "competitive": 0.50,
        "weak": 0.25,
    },
    "min_geographic_states": {
        "strong": 7,
        "competitive": 4,
        "weak": 2,
    },
    "min_projects": {
        "strong": 13,
        "competitive": 8,
        "weak": 4,
    },
    "max_geographic_hhi": {
        "strong": 500,
        "competitive": 800,
        "weak": 2_000,
    },
    "min_jobs_per_mm_qei": {
        "strong": 18.0,
        "competitive": 10.0,
        "weak": 6.0,
    },
    "max_single_sector_pct": {
        "strong": 0.25,
        "competitive": 0.35,
        "weak": 0.50,
    },
    "min_sectors_represented": {
        "strong": 5,
        "competitive": 3,
        "weak": 1,
    },
    "min_eligible_pct": {
        "strong": 0.98,
        "competitive": 0.90,
        "weak": 0.75,
    },
    "min_rural_pct": {
        "strong": 0.20,
        "competitive": 0.10,
        "weak": 0.00,
    },
    "min_native_area_pct": {
        "strong": 0.10,
        "competitive": 0.05,
        "weak": 0.00,
    },
}

BENCHMARK_SCORE_POINTS: dict = {
    "strong": 100,
    "competitive": 65,
    "weak": 30,
    "below_weak": 0,
}

BENCHMARK_METRIC_WEIGHTS: dict = {
    "min_deep_distress_pct": 0.25,
    "min_jobs_per_mm_qei": 0.20,
    "min_geographic_states": 0.15,
    "max_geographic_hhi": 0.10,
    "max_single_sector_pct": 0.10,
    "min_sectors_represented": 0.05,
    "min_projects": 0.05,
    "min_eligible_pct": 0.05,
    "min_rural_pct": 0.05,
}
