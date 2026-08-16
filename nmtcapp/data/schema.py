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
TARGET_DISTRESS_THRESHOLDS = {
    "min_deep_distress":   0.50,   # house heuristic: internal scoring band
    "target_deep_distress": 0.75,  # house heuristic: internal scoring band
}

# CDFI Fund historically prefers applicants serving ≥3 states.
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

VALID_SECTORS: List[str] = list(TARGET_SECTORS.keys())
VALID_PROJECT_TYPES: List[str] = ["real_estate", "operating_business", "mixed_use"]

# ---------------------------------------------------------------------------
# Readiness scoring weights — must sum to 1.0
# Weights reflect relative importance in CDFI Fund published scoring rubric.
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

# CDFI Fund NMTC program hard constraints
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
