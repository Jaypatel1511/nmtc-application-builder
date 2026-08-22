"""
Constants, enums, and shared data structures for NMTC application analysis.

Sources:
  - CDFI Fund NMTC Program guidance (https://www.cdfifund.gov/nmtc)
  - CDFI Fund NMTC Allocation Application Review Process, CY 2024-2025

NOT a source, and removed in 1.2.0: "Historical NMTC allocation award analysis
FY2018-FY2023". There is no such publication and no such span. See the note on
IMPACT_BENCHMARKS below.

Constants in this file whose provenance is a comment rather than a verified
extraction are marked "HOUSE BAND". Auditing each one against a primary source
is queued work; what 1.2.0 fixes is that none of them is presented to a CDE as
a federal figure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Distress level codes — values used by nmtc-mapper library
#
# THE "deep" ENTRY STATED THE SEVERE CRITERION (1.2.1 B-1). It read
# "poverty >30% or unemployment >1.5× national avg", which is column O of the
# CDFI Fund's eligibility workbook — the SEVERE flag. Deep distress is column
# P and is a strictly tighter test. Nothing in this package renders this dict,
# so no filing carried the wrong definition, but it is exported as
# ``nmtcapp.data.DISTRESS_LEVELS`` and a caller printing it would have.
#
# Both criteria are now quoted from the workbook's own column headers, which
# is the same wording renderers/_methodology puts in the filing. The two are
# NESTED, not disjoint: every deep-distress tract is also severely distressed
# (see intelligence/distress_analysis.DEEP_IS_SUBSET_OF_SEVERE).
# ---------------------------------------------------------------------------
DISTRESS_LEVELS = {
    "deep":       ("Deep Distress — LIC AND (Poverty>40%; MFI<=40%; "
                   "Unemployment>=2.5). A subset of Severe Distress."),
    "severe":     ("Severe Distress — LIC AND (Poverty>30%; MFI<=60%; "
                   "Unemployment>=1.5). Includes every Deep Distress tract."),
    "lic":        "Low Income Community (AMI ≤80% or poverty ≥20%)",
    "ineligible": "Not NMTC Eligible",
}

# ---------------------------------------------------------------------------
# HOUSE HEURISTICS — NOT CDFI Fund figures. Do not attribute them to the Fund
# and do not print them in a submitted document under the Fund's name.
#
# These two values are internal scoring bands used by readiness_score.py and
# eligibility_check.py to grade a pipeline against itself. They do not appear
# in any CDFI Fund publication. The Fund's published threshold on distress
# targeting is SEVERE_DISTRESS_MIN_PCT (0.85) in
# nmtcapp/data/benchmark_thresholds.py, sourced to the CY 2024-2025 NMTC
# Allocation Application Review Process — use that one for anything a CDE
# submits, and cite the round it belongs to.
#
# (A prior release printed 50%/75% in Section B labelled "CDFI Fund
# Competitive Minimum" and "CDFI Fund Target", understating the published
# 85% bar by ten points under the Fund's name. Hence this header.)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# BOTH KEYS BELOW ARE MISNAMED, AND THE NAME IS RECORDED RATHER THAN FIXED
# (1.5.4 T5).
#
# WHAT THEY MEASURE: ``pct_deep_or_severe`` -- the share of QEI in tracts that
# are deep OR severely distressed, the two tiers COLLAPSED INTO ONE BAND. Every
# read site compares them against that key and none of them looks at
# ``pct_deep``:
#
#   validation/readiness_score._distress_score      pct_deep_or_severe
#   intelligence/distress_analysis                  meets_min/target_threshold
#   validation/eligibility_check                    deep+severe QEI share
#   sections/section_a_business, pipeline_analyzer  render target_deep_distress
#
# WHAT THEIR NAMES SAY: deep distress. The CDFI Fund scores deep and severe as
# TWO SEPARATE sub-scores with DISTINCT bars -- benchmark_thresholds
# .SEVERE_DISTRESS_MIN_PCT (0.85) and .DEEP_DISTRESS_MIN_PCT (0.20) -- and
# intelligence/win_probability keeps them separate. Only this composite
# collapses them, under a key naming the half it is not measuring.
#
# WHAT THAT PRODUCES, MEASURED on an all-severe / no-deep pipeline:
#
#     readiness   distress_concentration  100.0/100, not docked
#     engine      Deep Distress Commitment  0/10, named as a gating reason
#
# THOSE TWO STATEMENTS ARE BOTH TRUE AND THEY ARE NOT IN CONFLICT. They are
# about different quantities that share a word: the share in deep-OR-severe
# tracts, and the share in deep tracts alone. Nothing needs reconciling between
# them. What is false is this key's NAME, which tells the next reader the band
# measures deep distress -- the "files agree with each other but not with the
# truth" class, and it misleads every future reader of the constant.
#
# NOT RENAMED HERE. This dict is exported as
# ``nmtcapp.data.TARGET_DISTRESS_THRESHOLDS``, its keys are read by four
# modules and asserted BY NAME in tests/validation/
# test_readiness_narrative_withdrawn.py, so renaming a key is a breaking change
# and 1.5.4 is a patch. Queued for 2.0.0 alongside ``overall_score``,
# ``grade`` and ``GRADE_THRESHOLDS``.
#
# THE GATE THAT MAKES THIS SAFE TO DEFER: tests/test_distress_band_semantics.py
# holds ``pct_deep_or_severe`` fixed while moving ``pct_deep`` underneath it and
# fails if the band responds -- so the documented semantics above and the
# measured quantity cannot diverge without the suite going red. Proved by
# mutating _distress_score to read ``pct_deep``: five of seven fail.
# ---------------------------------------------------------------------------
TARGET_DISTRESS_THRESHOLDS = {
    # house heuristic, internal scoring band. MEASURED ON pct_deep_or_severe.
    "min_deep_distress":   0.50,
    # house heuristic, internal scoring band. MEASURED ON pct_deep_or_severe.
    "target_deep_distress": 0.75,
}

# HOUSE. This comment read "CDFI Fund historically prefers applicants serving
# >=3 states." for nine releases. THAT IS AN UNSOURCED CLAIM ABOUT A FEDERAL
# AGENCY, and it sat in no attribution registry: zero hits in
# tests/scoring_attribution.txt and zero in tests/fund_attribution_allowlist.txt.
# The CY 2024-2025 Review Process scores no state count, and the Allocation
# Application asks for a service area, not a minimum number of states.
#
# AND IT IS NOT INERT, WHICH IS WHY IT MATTERS. tests/pinned_constants.txt
# waived this constant on the grounds that it "Feeds meets_diversity_minimum, a
# boolean. Neither the boolean nor the 3 renders in any artifact." Both halves
# are wrong. It is the DENOMINATOR of validation/readiness_score._geo_score
# (``states / MIN_GEOGRAPHIC_DIVERSITY * 50``), which is the
# geographic_diversity component -- 15% of the readiness grade printed at the
# top of every artifact. And MIN_GEOGRAPHIC_DIVERSITY + 2 renders verbatim as
# "Target >=5 states" in the recommendation block. Measured 1.5.0 on a
# single-state pipeline: sub-score 16.7, recommendation rendered.
#
# THE VALUE IS UNCHANGED HERE ON PURPOSE. Re-basing it is calibration against
# the Fund's newly published Allocatee data, which is methodology-first work
# and is NOT this release. What changes is that it no longer claims to be the
# Fund's preference, and it is no longer waived on a false premise.
MIN_GEOGRAPHIC_DIVERSITY: int = 3

# ---------------------------------------------------------------------------
# Sector targets — CDFI Fund priority areas (current NOFA guidance)
# ---------------------------------------------------------------------------
TARGET_SECTORS = {
    "healthcare":         {"description": "FQHCs, hospitals, behavioral health", "priority": "high"},
    "affordable_housing": {"description": "Affordable rental, supportive housing", "priority": "high"},
    "education":          {"description": "Charter schools, CDCs, community colleges", "priority": "high"},
    "small_business":     {"description": "Manufacturing, retail, services in LICs", "priority": "medium"},
    "mixed_use":          {"description": "Mixed-use RE with community benefit", "priority": "medium"},
    "community_facility": {"description": "Libraries, rec centers, food access", "priority": "medium"},
    "clean_energy":       {"description": "Solar, wind, efficiency in LICs", "priority": "medium"},
    "other":              {"description": "Other NMTC-eligible uses", "priority": "low"},
}

# THE PRIORITY TIERS, DERIVED (FIX-2 G-5 sweep, third instance). Four places
# stated them independently and one had already drifted:
#
#   intelligence/sector_analysis._HIGH_PRIORITY_SECTORS  hand-typed, agreed
#   visualization/maps._HIGH_PRIORITY / _MED_PRIORITY    hand-typed, WRONG —
#       _MED_PRIORITY held {small_business, mixed_use} and omitted
#       community_facility and clean_energy, which this dict classes medium.
#       The sector-mix chart therefore coloured those two bars with the
#       low-priority grey under a legend reading "Medium Priority (Small
#       Business/Mixed Use)", while the Streamlit page rendering the same
#       pipeline printed "Priority: Medium" for them in the table beside it —
#       one screen, two classifications.
#   streamlit_app/utils.VALID_SECTORS                    retyped under the
#       comment "(from schema)". It was not from schema.
#
# Same shape as the required-CDE-fields triplication, and the same fix: one
# statement, everything else derived.
SECTORS_BY_PRIORITY = {
    tier: frozenset(k for k, v in TARGET_SECTORS.items() if v["priority"] == tier)
    for tier in ("high", "medium", "low")
}

VALID_SECTORS: List[str] = list(TARGET_SECTORS.keys())
VALID_PROJECT_TYPES: List[str] = ["real_estate", "operating_business", "mixed_use"]

# ---------------------------------------------------------------------------
# Readiness scoring weights — must sum to 1.0
#
# HOUSE. THE IDENTICAL DEFECT 1.2.0 REMOVED FROM MIN_GEOGRAPHIC_DIVERSITY, ONE
# DICT AWAY, STILL STANDING (1.5.2 T2). This comment read:
#
#     "Weights reflect relative importance in CDFI Fund published scoring
#      rubric."
#
# THAT IS FALSE, and this package's own registry already says so. The row for
# this constant in tests/pinned_constants.txt rules it an "unsourced house
# heuristic" and states that "the CDFI Fund publishes no such weighting";
# renderers/_methodology.readiness_weights_note() renders the same negative to
# a CDE on four surfaces; and the Streamlit About page's Limitation 7 says the
# Fund publishes no such score, no such weighting and no grade. THERE IS NO
# CDFI FUND PUBLISHED SCORING RUBRIC BEHIND THESE SIX NUMBERS. There is no
# published rubric of any kind that weights an application this way. The CY
# 2024-2025 Review Process scores two sections at 50 points each; it does not
# score eligibility rate, distress concentration, geographic diversity, impact
# metrics, validation pass rate or completeness, and it assigns none of them a
# weight.
#
# WHY IT MATTERED THOUGH IT RENDERS NOWHERE. A comment is not a surface, and no
# CDE ever read this line. It is worse than a rendered defect for a different
# reason: it is a claim a future round re-cites having assumed somebody checked
# it. That is precisely the hazard the IMPACT_BENCHMARKS block below was
# written to prevent, and it is what happened to MIN_GEOGRAPHIC_DIVERSITY --
# nine releases of "CDFI Fund historically prefers >=3 states" sitting above a
# constant that is the denominator of a scored component.
#
# THE MACHINERY DID NOT CATCH IT, AND NOW IT DOES. tests/
# test_fund_attribution_source.py scans string literals through the AST, so a
# comment is not a node and can never match; and its _BAR detector requires a
# figure, which this sentence does not contain. Two independent reasons it was
# invisible. tests/test_fund_attribution_source.py::
# test_no_house_constant_is_attributed_to_the_fund_in_its_own_comment closes
# the class by reading the registry: a constant ruled HOUSE may not carry an
# undisclaimed Fund attribution in the comment block that defines it.
# ---------------------------------------------------------------------------
READINESS_SCORING_WEIGHTS = {
    "eligibility_quality":   0.25,  # % of pipeline in LIC tracts
    "distress_concentration": 0.25,  # % of QEI in deep/severe distress
    "geographic_diversity":  0.15,  # states and MSA breadth
    "impact_metrics":        0.20,  # jobs/units vs historical benchmarks
    "validation_pass_rate":  0.10,  # % of validation checks passing
    "completeness":          0.05,  # required fields populated
}

# ---------------------------------------------------------------------------
# Impact screening bands — HOUSE BANDS. NOT a CDFI Fund benchmark.
#
# A primary-source pass in 1.2.0 established that the citation these numbers
# used to carry named a publication that does not exist. Recorded here so it
# cannot be re-cited by someone who assumes the earlier comment was checked:
#
#   1. THE CITED PUBLICATION DOES NOT EXIST. There is no "CDFI Fund NMTC
#      Program Annual Report" series. The NMTC "annual report" is OMB
#      collection 1559-0027 — the Awardee/Allocatee Annual Report (Institution
#      Level Report + Transaction Level Report) that allocatees FILE TO the
#      Fund through CIIS, and whose OMB supporting statement says the
#      confidential and proprietary information it collects will not be
#      published. The Fund's actual publication series is the NMTC Public Data
#      Release ... Summary Report, which is cumulative FY2003-FY2023 — not a
#      set of annual reports, and not an FY2018-FY2023 span.
#
#   2. NO JOBS-PER-DOLLAR FIGURE IS PUBLISHED, IN ANY DENOMINATOR. The Fund
#      reports job counts and dollar counts separately and never divides them.
#      The only official per-dollar figure in the record is the 2013 Urban
#      Institute evaluation's tax-credits-per-permanent-job range, from a
#      149-project pre-2010 subsample: different numerator, different
#      denominator, inverted direction, different era.
#
#   3. NO DISTRIBUTION IS PUBLISHED, so calling 20.0 a "top quartile" asserted
#      a population percentile nothing supports — the same
#      threshold-is-not-a-percentile error that removed _assess_vs_winners,
#      sector_analysis's twin, and impact_aggregator._benchmark_label.
#
#   4. THE SPAN IS IMPOSSIBLE. Actual job figures stop at FY2020 activity;
#      FY2021-FY2023 in the current release are projections. There were no
#      FY2018-FY2023 actuals to average.
#
# DO NOT "FIX" THIS BY RE-CITING. Two derivations land near 12.0 and both are
# traps — the plausible ones count transient construction FTEs, which is not
# what a reader of "12 FTE per $1MM" assumes, and the Urban Institute range
# converts to roughly half of 12.0 with 12.0 sitting on its best-case endpoint.
# All of them are DERIVED, not published. Substituting one relocates the error.
#
# What these three numbers ARE: this tool's own screening bands, used by
# validation/readiness_score._impact_score — its only reader — to place a
# pipeline on a 0-100 impact component of a score that already declares itself
# an unsourced house heuristic on the face of every rendered methodology note.
# Relabelling makes the two consistent. Deleting the constant would mean
# redesigning a scored component, which is next release's work.
#
# cost_per_job_low/avg/high were removed in 1.2.0: zero consumers repo-wide.
# ---------------------------------------------------------------------------
IMPACT_BENCHMARKS = {
    "jobs_per_million_qei_low":  5.0,
    "jobs_per_million_qei_avg":  12.0,
    "jobs_per_million_qei_high": 20.0,
}

# Required fields for a project to be considered complete
REQUIRED_PROJECT_FIELDS: List[str] = [
    "project_id", "project_name", "qalicb_name",
    "address", "city", "state",
    "sector", "project_type",
    "total_project_cost", "qei_request", "qlici_amount",
    "expected_jobs_created",
]

# NMTC program constraints — TWO STATUTORY, FOUR HOUSE. NOT a CDFI Fund dict.
#
# THE SECOND INSTANCE OF T2'S CLASS, FOUND BY THE SWEEP RATHER THAN KNOWN
# (1.5.2). This comment read "CDFI Fund NMTC program hard constraints", and
# that header is false about every key under it, in two different directions:
#
#   credit_rate, compliance_period_years   STATUTE, NOT THE AGENCY. Both are
#       IRC §45D(a)(2) -- 5% for each of the first three credit allowance
#       dates and 6% for each of the remaining four, over a 7-year compliance
#       period. The CDFI Fund administers the allocation; it does not set the
#       credit rate, and Congress did. The registry rows for both cite the
#       statute, not the Fund.
#
#   standard_credit_price, cde_fee_rate_typical   HOUSE MARKET ASSUMPTIONS,
#       and the registry rules them in the Fund's own negative: "The CDFI Fund
#       sets no credit price" and "The CDFI Fund sets no fee rate". Both
#       render into the generated documents, where the line beside them
#       already reads "market assumption, not a CDFI Fund parameter" -- so the
#       rendered surface was right and the source comment above it was wrong.
#
#   leverage_ratio_typical, min_qei_per_project   house values, waived in the
#       registry as consumed by nothing.
#
# "Hard constraints" was the second false word: four of the six are typical
# market figures this model assumes, and nothing constrains them.
NMTC_PROGRAM_CONSTRAINTS = {
    "min_qei_per_project":       1_000_000,   # $1MM floor
    "credit_rate":               0.39,        # 39% of QEI over 7 years
    "compliance_period_years":   7,
    "leverage_ratio_typical":    0.80,
    "cde_fee_rate_typical":      0.025,       # 2.5% of QEI
    "standard_credit_price":     0.83,        # $/NMTC credit dollar
}

GRADE_THRESHOLDS = {
    "A": 85.0,
    "B": 70.0,
    "C": 55.0,
    "D": 40.0,
}


# ---------------------------------------------------------------------------
# Shared result objects used across validation and analysis modules
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of a single validation check.

    Example::

        result = ValidationResult(
            check_name="eligibility_check",
            passed=True,
            issues=[],
            warnings=["2 projects lack census tract data"],
        )
    """
    check_name: str
    passed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable one-paragraph summary."""
        status = "PASS" if self.passed else "FAIL"
        lines = [f"[{status}] {self.check_name}"]
        for issue in self.issues:
            lines.append(f"  ERROR: {issue}")
        for warning in self.warnings:
            lines.append(f"  WARN:  {warning}")
        if not self.issues and not self.warnings:
            lines.append("  All checks passed.")
        return "\n".join(lines)
