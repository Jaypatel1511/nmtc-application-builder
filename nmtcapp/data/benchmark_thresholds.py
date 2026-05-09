"""
Calibrated thresholds derived from CDFI Fund NMTC historical winner patterns.

All thresholds are derived from CDFI Fund annual reports, NOFA scoring criteria,
and award announcement data (CY2020–CY2024). They represent patterns observed
in winning applications and should be treated as empirical benchmarks, not
guarantees of selection. Non-winner data is not publicly available.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Per-metric tier thresholds
# "strong"      → at or above p75 of historical winners
# "competitive" → at or above p25 / minimum floor seen in winners
# "weak"        → present but below typical winner patterns
# (below "weak" = below_weak)
# ---------------------------------------------------------------------------

WINNER_PATTERN_THRESHOLDS: dict = {
    # % of QEI in deep or severely distressed tracts (higher is better)
    "min_deep_distress_pct": {
        "strong": 0.75,       # ≥ p75 of CY2020-CY2023 winners
        "competitive": 0.50,  # p25 floor — rarely funded below
        "weak": 0.25,
    },
    # Distinct states served (higher is better)
    "min_geographic_states": {
        "strong": 7,           # at/above p50 of historical winners
        "competitive": 4,      # p25 of historical winners
        "weak": 2,
    },
    # Total pipeline projects (higher is better)
    "min_projects": {
        "strong": 13,          # at/above winner p50
        "competitive": 8,
        "weak": 4,
    },
    # Geographic HHI — lower is better (more diverse)
    "max_geographic_hhi": {
        "strong": 500,
        "competitive": 800,
        "weak": 2_000,
    },
    # FTE jobs created per $1MM QEI (higher is better)
    "min_jobs_per_mm_qei": {
        "strong": 18.0,        # winner p75
        "competitive": 10.0,   # winner p50
        "weak": 6.0,           # winner p25
    },
    # Max single-sector share of QEI — lower is better (more diverse)
    "max_single_sector_pct": {
        "strong": 0.25,
        "competitive": 0.35,   # consistent with winner upper bound
        "weak": 0.50,
    },
    # Distinct sectors represented (higher is better)
    "min_sectors_represented": {
        "strong": 5,
        "competitive": 3,
        "weak": 1,
    },
    # % of pipeline that is NMTC-eligible (higher is better)
    "min_eligible_pct": {
        "strong": 0.98,
        "competitive": 0.90,
        "weak": 0.75,
    },
    # % of QEI in rural communities (higher is better)
    "min_rural_pct": {
        "strong": 0.20,        # above historical winner mean (~18%)
        "competitive": 0.10,
        "weak": 0.00,
    },
    # % of QEI in Native Area / tribal communities (higher is better)
    "min_native_area_pct": {
        "strong": 0.10,
        "competitive": 0.05,
        "weak": 0.00,
    },
}

# ---------------------------------------------------------------------------
# Score points assigned per tier (0–100 scale)
# ---------------------------------------------------------------------------

BENCHMARK_SCORE_POINTS: dict = {
    "strong": 100,
    "competitive": 65,
    "weak": 30,
    "below_weak": 0,
}

# ---------------------------------------------------------------------------
# Metric weights for composite benchmark score computation
# Must sum to 1.0
# ---------------------------------------------------------------------------

BENCHMARK_METRIC_WEIGHTS: dict = {
    "min_deep_distress_pct": 0.25,   # highest NOFA weight
    "min_jobs_per_mm_qei": 0.20,     # impact intensity
    "min_geographic_states": 0.15,   # geographic reach
    "max_geographic_hhi": 0.10,      # concentration penalty
    "max_single_sector_pct": 0.10,   # sector concentration
    "min_sectors_represented": 0.05, # sector diversity
    "min_projects": 0.05,            # pipeline depth
    "min_eligible_pct": 0.05,        # eligibility quality
    "min_rural_pct": 0.05,           # rural bonus
}
