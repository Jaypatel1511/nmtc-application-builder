"""
Scoring thresholds for NMTC applications.

Two sections:

SECTION A — CDFI Fund Published Thresholds (CY 2024-2025)
  Derived from the CY 2024-2025 NMTC Allocation Application Review Process
  (https://www.cdfifund.gov/system/files/2025-12/CY_2024_25_NMTC_Program_Review_Process.pdf).
  These are the explicit values the CDFI Fund uses to evaluate applications in
  the two scored sections (Business Strategy and Community Outcomes) and to
  gate applicants into the "Highly Qualified" pool.

SECTION B — Legacy winner-pattern thresholds (CY2020–2024)
  Used by HistoricalBenchmarks (benchmarks.py) for the 9-metric tier comparison.
  Kept for backward compatibility. These are inferred from award announcements,
  not published by the CDFI Fund.
"""
from __future__ import annotations

# ===========================================================================
# SECTION A — CDFI Fund CY 2024-2025 Published Thresholds
# Source: CY_2024_25_NMTC_Program_Review_Process.pdf
# ===========================================================================

# --- Community Outcomes thresholds ---
SEVERE_DISTRESS_MIN_PCT = 0.85       # 85%+ in severe distress / multi-indicia for full credit
DEEP_DISTRESS_MIN_PCT = 0.20         # 20%+ in Deep Distress areas for full credit
SPECIAL_TARGETING_BONUS_PCT = 0.10   # 10%+ in a special targeting category triggers bonus

# --- Business Strategy thresholds ---
TRACK_RECORD_PIPELINE_ALIGNMENT_MIN = 0.70   # 70%+ NMTC pipeline supported by similar prior activity
TRACK_RECORD_DEPLOYMENT_MIN = 0.90           # 90%+ of prior allocation deployed on schedule
PRODUCT_FLEXIBILITY_BELOW_MARKET_PCT = 0.50  # 50%+ below-market rate for full product flexibility credit
PRODUCT_FLEXIBILITY_MIN_INDICIA = 5          # Or 5+ indicia of flexible terms for full credit

# --- Priority Points thresholds ---
DBC_PRIORITY_YEARS_MIN = 5            # 5+ years DBC focus for full DBC priority points
DBC_VOLUME_PCT_MIN = 0.70             # 70%+ of direct financing volume to DBCs for full credit
UNRELATED_ENTITIES_MIN_PCT = 0.90    # 90%+ QEIs to unrelated entities for full unrelated-entity credit

# --- Non-Metro / Rural commitments ---
NON_METRO_MIN_COMMITMENT_PCT = 0.20        # 20% minimum non-metro commitment
NON_METRO_MAX_COMMITMENT_FACTOR = 0.90     # Must commit larger of min or 90% of max
RURAL_CDE_NON_METRO_THRESHOLD = 0.50       # 50% non-metro to qualify as Rural CDE

# --- Highly Qualified gating thresholds ---
HIGHLY_QUALIFIED_AGGREGATE_MIN = 85    # 85+ aggregate base score to be "Highly Qualified"
HIGHLY_QUALIFIED_SECTION_MIN = 40      # Each section must score 40+ to be "Highly Qualified"
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
