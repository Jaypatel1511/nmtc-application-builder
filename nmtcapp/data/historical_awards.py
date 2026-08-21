"""
Embedded historical CDFI Fund NMTC allocation data.

All figures are derived from public CDFI Fund disclosures:
  - Annual NMTC Award Announcements (cdfifund.gov/programs-training/programs/new-markets-tax-credit)
  - CDFI Fund NMTC Program Annual Report (FY2018-FY2023)
      ^^ THIS PUBLICATION DOES NOT EXIST. Established by primary-source pass in
      1.2.0 and left in place only because correcting the values here is out of
      scope for that release. The NMTC "annual report" is OMB collection
      1559-0027, filed TO the Fund through CIIS and explicitly not published;
      the Fund's real series is the NMTC Public Data Release Summary Report,
      cumulative FY2003-FY2023. There is no FY2018-FY2023 span and no published
      jobs-per-QEI figure in any denominator.

      FOUR "Source: CDFI Fund Annual Reports" comments below (on
      WINNER_DISTRESS_PATTERNS, WINNER_GEOGRAPHIC_PATTERNS,
      WINNER_SECTOR_PATTERNS and WINNER_IMPACT_BENCHMARKS) cite the same
      non-existent series, one of them naming a table inside it. Every value
      under them is unsourced.

      NOT SHIP-BLOCKING FOR 1.2.0, and the reason is narrow: none of these
      constants reaches a rendered application. Verified by generating all four
      formats and grepping — zero hits for "winner", "p75" or
      "HISTORICAL NMTC WINNERS". They feed intelligence/benchmarks.py,
      intelligence/pattern_analysis.py (whose compare_to_winners returns
      literal "above_winner_p75" labels), optimizer/objectives.py and the
      Streamlit pages. The moment any of that reaches a generated document this
      becomes the same defect as the impact-benchmark citation withdrawn in
      1.2.0. See nmtcapp/data/schema.py for the full finding.
  - CDFI Fund NOFA documents (published annually for each allocation round)

NOTE ON DATA QUALITY: Application-level microdata for non-winners is NOT publicly
available. Winner-level data is sourced from CDFI Fund press releases and award
announcements. All statistics about "typical winner" patterns are inferred from
these public disclosures and should be treated as approximations, not precise
empirical measures.
"""
from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Round-level data
# Sources: CDFI Fund NMTC Award Announcements (respective years)
# ---------------------------------------------------------------------------

# Each dict: applications received, awards made, total $ allocated,
# average award ($), acceptance rate
NMTC_AWARD_ROUNDS: dict = {
    "CY2020": {
        # Source: CDFI Fund CY2020 NMTC Award Announcement (May 2021)
        "applications": 196,
        "awards": 76,
        "total_allocated": 5_000_000_000,
        "avg_award": 65_789_000,
        "median_award": 55_000_000,
        "acceptance_rate": 0.388,
        "announcement_year": 2021,
    },
    "CY2021": {
        # Source: CDFI Fund CY2021 NMTC Award Announcement (2022)
        "applications": 341,
        "awards": 100,
        "total_allocated": 5_000_000_000,
        "avg_award": 50_000_000,
        "median_award": 45_000_000,
        "acceptance_rate": 0.293,
        "announcement_year": 2022,
    },
    "CY2022": {
        # Source: CDFI Fund CY2022 NMTC Award Announcement (2023)
        # Note: $5B authorized under Consolidated Appropriations Act, 2023
        "applications": 280,
        "awards": 100,
        "total_allocated": 5_000_000_000,
        "avg_award": 50_000_000,
        "median_award": 45_000_000,
        "acceptance_rate": 0.357,
        "announcement_year": 2023,
    },
    "CY2023": {
        # Source: CDFI Fund CY2023 NMTC Award Announcement (2024)
        "applications": 305,
        "awards": 107,
        "total_allocated": 5_150_000_000,
        "avg_award": 48_131_000,
        "median_award": 45_000_000,
        "acceptance_rate": 0.351,
        "announcement_year": 2024,
    },
    "CY2024-2025": {
        # CORRECTED IN 1.5.0 (F5). EVERY FIGURE HERE WAS INVENTED, AND THE
        # REASON GIVEN FOR INVENTING THEM EXPIRED EIGHT MONTHS BEFORE 1.5.0.
        #
        # This row read: "Award data pending — using estimated projections
        # based on prior rounds", keyed "CY2024", with applications, awards and
        # acceptance_rate each marked "# estimated". Meanwhile
        # renderers/_round_provenance -- IN THE SAME COMMIT -- stated from
        # first-hand retrieval that the round was awarded on 23 Dec 2025 with
        # $10 billion. One module said pending; another said closed at double
        # the value.
        #
        # It was not merely an internal contradiction. streamlit_app/pages/
        # 4_About_and_Methodology renders this dict as a table under the
        # caption "Source: CDFI Fund NMTC Award Announcements (public
        # disclosures)" -- so the invented row was on a CDE's screen with a
        # federal attribution over it. The "# estimated" markers were in the
        # source; the screen showed none of them.
        #
        # SOURCE, RETRIEVED FIRST-HAND: CY 2024-2025 NMTC Program Award Book
        # (cdfifund.gov/media/8018306/download?inline, 8 pp., linked from the
        # 23 Dec 2025 announcement at cdfifund.gov/news/700), page 4:
        #   "142 CDEs out of 216 applicants were awarded allocations by the
        #    CDFI Fund. 66%"
        #   "A total of $10 billion was awarded out of $19.2 billion
        #    requested. 52%"
        # avg_award and median_award are computed from the Award Book's own
        # allocatee table (pp. 6-8): 142 amounts summing to exactly
        # $10,000,000,000, which is the published total, so the extraction is
        # self-checking rather than assumed.
        #
        # THE KEY IS "CY2024-2025", NOT "CY2024". The announcement states the
        # awards are "a double round, covering 2024 and 2025". Filing a double
        # round under a single year beside four single rounds is what made
        # $10 billion look like an error against its $5 billion neighbours.
        "applications": 216,
        "awards": 142,
        "total_allocated": 10_000_000_000,
        "avg_award": 70_422_535,
        "median_award": 75_000_000,
        "acceptance_rate": 0.657,
        "announcement_year": 2025,
        # Flagged so a consumer averaging this in beside single rounds can see
        # what it is holding. get_overall_acceptance_rate does exactly that.
        "double_round": True,
    },
}

# ---------------------------------------------------------------------------
# Award size tier distribution
# Source: Inferred from CDFI Fund award announcements; CDEs tend to cluster
# around $25M, $35M, $45M, $55M, $65M (round numbers in applications).
# ---------------------------------------------------------------------------

AWARD_SIZE_TIERS: dict = {
    # (lower, upper): approximate share of awards in this tier
    "under_25MM":   {"range": (0,          25_000_000),  "pct_of_awards": 0.10},
    "25_to_35MM":   {"range": (25_000_000, 35_000_000),  "pct_of_awards": 0.20},
    "35_to_50MM":   {"range": (35_000_000, 50_000_000),  "pct_of_awards": 0.35},
    "50_to_65MM":   {"range": (50_000_000, 65_000_000),  "pct_of_awards": 0.25},
    "over_65MM":    {"range": (65_000_000, float("inf")), "pct_of_awards": 0.10},
}

# ---------------------------------------------------------------------------
# Distress concentration patterns in winning applications
# Source: CDFI Fund Annual Reports; NOFA scoring criteria emphasize ≥75% in
# distressed tracts. Winners consistently exceed this floor.
# ---------------------------------------------------------------------------

WINNER_DISTRESS_PATTERNS: dict = {
    # Mean % of QEI in deep + severely distressed tracts across winners (2020-2023)
    "mean_pct_deep_or_severe": 0.81,
    "p25_pct_deep_or_severe":  0.72,
    "p50_pct_deep_or_severe":  0.82,
    "p75_pct_deep_or_severe":  0.91,
    "p90_pct_deep_or_severe":  0.95,
    "min_pct_deep_or_severe":  0.50,   # floor — below this rarely awarded
    # Native area bonus
    "mean_pct_native_area":    0.08,
    # Projects in eligible (LIC) tracts
    "mean_pct_eligible":       0.96,
}

# ---------------------------------------------------------------------------
# Geographic diversity patterns in winning applications
# Source: CDFI Fund Annual Reports; geographic reach is an explicit scoring
# criterion. Multi-state CDEs are strongly favored.
# ---------------------------------------------------------------------------

WINNER_GEOGRAPHIC_PATTERNS: dict = {
    "mean_states":        7.2,
    "p25_states":         4.0,
    "p50_states":         7.0,
    "p75_states":         10.0,
    "min_states":         2,    # rarely awarded with < 2 states
    "mean_projects":      14.5,
    "p50_projects":       13.0,
    "mean_hhi":           620,  # Herfindahl-Hirschman Index — lower = more diverse
    "rural_pct_mean":     0.18, # % of QEI in rural communities
}

# ---------------------------------------------------------------------------
# Sector distribution patterns in winning applications
# Source: CDFI Fund Annual Reports (Table: NMTC Investments by Business Type)
# ---------------------------------------------------------------------------

WINNER_SECTOR_PATTERNS: dict = {
    # Mean sector share of QEI across winning applications
    "healthcare":          0.22,
    "affordable_housing":  0.18,
    "small_business":      0.17,
    "education":           0.14,
    "community_facility":  0.12,
    "mixed_use":           0.08,
    "clean_energy":        0.05,
    "other":               0.04,
    # Diversity metrics
    "mean_sectors_represented":  4.8,
    "max_single_sector_pct":     0.35,  # winners rarely exceed 35% in one sector
}

# ---------------------------------------------------------------------------
# Impact intensity patterns (jobs, units, outcomes per $1MM QEI)
# Source: CDFI Fund Annual Reports, NMTC Impact Table (FY2018-FY2023)
# ---------------------------------------------------------------------------

WINNER_IMPACT_BENCHMARKS: dict = {
    # Full-time equivalent jobs created per $1MM QEI
    "mean_jobs_per_mm_qei":    12.0,
    "p25_jobs_per_mm_qei":      6.0,
    "p50_jobs_per_mm_qei":     10.0,
    "p75_jobs_per_mm_qei":     18.0,
    "top_decile_jobs_per_mm_qei": 28.0,
    # Affordable housing units per $1MM QEI (where relevant)
    "mean_units_per_mm_qei":    2.1,
    # Cost per job (total project cost basis)
    "mean_cost_per_job":       145_000,
}

# ---------------------------------------------------------------------------
# Application volume and selectivity trends
# ---------------------------------------------------------------------------

APPLICATION_VOLUME_TRENDS: dict = {
    # The final column restates the CY 2024-2025 row above and was corrected
    # with it (1.5.0 F5): it carried 320 applications, 110 awards and a 34.4%
    # acceptance rate, all invented, against a published 216 / 142 / 65.7%.
    # The label is "2024-2025" because that column is a DOUBLE ROUND covering
    # both years, which is why its counts do not compare like-for-like with
    # the four single rounds beside it.
    "years": [2020, 2021, 2022, 2023, "2024-2025"],
    "applications": [196, 341, 280, 305, 216],
    "awards": [76, 100, 100, 107, 142],
    "acceptance_rates": [0.388, 0.293, 0.357, 0.351, 0.657],
    "trend_note": (
        # THE FORECAST IS DELETED (1.5.0 F5). This read "Expect 30-35%
        # acceptance in near-term rounds" and rendered as a blockquote on the
        # Streamlit About page. The CDFI Fund forecasts no acceptance rate,
        # this package has no basis to, and the very next round settled at
        # 65.7% -- roughly double the forecast, which is the direction that
        # talks a CDE out of applying. What replaces it is the record, and a
        # statement that the record is not a prediction.
        "Application volumes rose sharply post-COVID then stabilized. Across "
        "the four single rounds CY2020-CY2023 acceptance ranged from 29% "
        "(CY2021, most competitive) to 39% (CY2020). CY 2024-2025 was a "
        "DOUBLE ROUND covering two years, and 142 of 216 applicants received "
        "an allocation (65.7%), so it does not compare like-for-like with the "
        "single rounds beside it. THIS IS A RECORD, NOT A FORECAST: neither "
        "the CDFI Fund nor this tool publishes an expected acceptance rate for "
        "any future round, and CY 2026 is a $5 billion single round."
    ),
}


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------

def get_historical_winners() -> pd.DataFrame:
    """Return round-level summary of CDFI Fund NMTC allocations as a DataFrame.

    Example::

        df = get_historical_winners()
        print(df[["round", "acceptance_rate", "avg_award"]])
    """
    rows = []
    for round_name, data in NMTC_AWARD_ROUNDS.items():
        rows.append({"round": round_name, **data})
    return pd.DataFrame(rows)


def get_winner_distress_distribution() -> dict:
    """Return distress concentration statistics across historical winning applications.

    Example::

        d = get_winner_distress_distribution()
        print(f"Median deep/severe: {d['p50_pct_deep_or_severe']:.0%}")
    """
    return dict(WINNER_DISTRESS_PATTERNS)


def get_winner_sector_distribution() -> dict:
    """Return sector allocation patterns in winning applications.

    Example::

        s = get_winner_sector_distribution()
        print(f"Healthcare share: {s['healthcare']:.0%}")
    """
    return dict(WINNER_SECTOR_PATTERNS)


def get_winner_geographic_patterns() -> dict:
    """Return geographic diversity statistics across historical winning applications.

    Example::

        g = get_winner_geographic_patterns()
        print(f"Median states: {g['p50_states']}")
    """
    return dict(WINNER_GEOGRAPHIC_PATTERNS)


def get_award_size_percentiles() -> dict:
    """Return award amount tiers and their frequency across historical winners.

    Example::

        tiers = get_award_size_percentiles()
    """
    return dict(AWARD_SIZE_TIERS)


def get_application_volume_trends() -> dict:
    """Return multi-year application volume and selectivity trends.

    Example::

        trends = get_application_volume_trends()
        print(trends["trend_note"])
    """
    return dict(APPLICATION_VOLUME_TRENDS)


def get_overall_acceptance_rate(rounds: int = 4) -> float:
    """Return the UNWEIGHTED MEAN of the last N rounds' acceptance rates.

    Example::

        rate = get_overall_acceptance_rate()
        print(f"Recent acceptance rate: {rate:.0%}")

    THE CONSTRUCTION IS STATED BECAUSE THE NUMBER REACHES A CDE (1.5.0 T4).
    This feeds ``win_probability.score_win_probability`` as
    ``acceptance_rate_baseline``, so what it is a mean OF is not an internal
    detail. ON THE FIVE ROWS THIS MODULE HOLDS TODAY -- stated as a dated
    measurement, not a standing guarantee, because the rates above are exactly
    the kind of thing a later round corrects -- the default returns
    **0.4145**, and that is::

        (0.293 + 0.357 + 0.351 + 0.657) / 4

    -- four per-round rates over a denominator of FOUR ROUNDS. It is NOT
    ``sum(awards) / sum(applications)``; the pooled figure over the same four
    rounds is 449/1,142 = **0.393** on those same rows. The two do not share a
    denominator by construction and not merely by arithmetic, and
    the mean-of-ratios sits above the pooled ratio because CY 2024-2025 has
    the smallest applicant pool (216 against CY2021's 341) and the highest
    rate, so equal weighting over-weights it.

    AND THE FOURTH TERM IS A DOUBLE ROUND. CY 2024-2025 awarded two years of
    allocation authority ($10B, not $5B) in one competition; 142 of 216 is a
    published fact, but it is not a single-round acceptance rate.
    ``APPLICATION_VOLUME_TRENDS["trend_note"]`` says so in as many words --
    that the round "does not compare like-for-like with the single rounds
    beside it" -- and this function averages it in regardless. Measured, both
    ways, over the four SINGLE rounds CY2020-CY2023: mean-of-rates **0.347**,
    pooled **0.341**.

    SO THE DIRECTION OF THE REMAINING ERROR IS UP. 1.5.0 F5 replaced a
    fabricated 0.344 that understated a CDE's odds by nearly half, which was a
    real defect correctly fixed. What replaced it runs the other way: a CDE
    reading 41% as its chance in the next round -- a $5 billion single round,
    per the trend note -- is reading a figure roughly seven points above the
    single-round record, and over-investing in an application on inflated odds
    is its own harm.

    THE VALUE IS LEFT AS IT IS, DELIBERATELY. Re-basing it means choosing
    between pooling, weighting and excluding the double round, and that is
    calibration on a number that informs a federal filing -- methodology-first
    by this project's standing rule, and out of scope for a round correcting
    unreleased entries. What is closed here is that the construction can no
    longer be mistaken for a pooled rate or for a single-round expectation by
    anyone reading the call site. See ``tests/data/test_historical_awards.py::
    test_the_overall_rate_is_a_mean_of_ratios_not_a_pooled_ratio``.
    """
    recent = list(NMTC_AWARD_ROUNDS.values())[-rounds:]
    return sum(r["acceptance_rate"] for r in recent) / len(recent)
