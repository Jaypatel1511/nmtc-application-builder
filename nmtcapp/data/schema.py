"""
Constants, enums, and shared data structures for NMTC application analysis.

Sources:
  - CDFI Fund NMTC Program guidance (https://www.cdfifund.gov/nmtc)
  - Historical NMTC allocation award analysis FY2018–FY2023
  - CDFI Fund NMTC Application scoring criteria (published NOFA)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Distress level codes — values used by nmtc-mapper library
# ---------------------------------------------------------------------------
DISTRESS_LEVELS = {
    "deep":       "Deep Distress (poverty >30% or unemployment >1.5× national avg)",
    "severe":     "Severe Distress (LIC plus additional qualifying distress factors)",
    "lic":        "Low Income Community (AMI ≤80% or poverty ≥20%)",
    "ineligible": "Not NMTC Eligible",
}

# ---------------------------------------------------------------------------
# Competitive thresholds — derived from CDFI Fund published award data
# Applications with ≥75% QEI in deep/severe tracts historically score in
# the top quartile on the "Community Need" criterion.
# ---------------------------------------------------------------------------
TARGET_DISTRESS_THRESHOLDS = {
    "min_deep_distress":   0.50,   # minimum to be competitive
    "target_deep_distress": 0.75,  # target for top-tier applications
    "max_non_lic":          0.10,  # hard ceiling for non-LIC QEI
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
# Impact benchmarks — CDFI Fund historical TLR / annual report data
# ---------------------------------------------------------------------------
IMPACT_BENCHMARKS = {
    "jobs_per_million_qei_low":  5.0,
    "jobs_per_million_qei_avg":  12.0,
    "jobs_per_million_qei_high": 20.0,
    "cost_per_job_low":          50_000,
    "cost_per_job_avg":          80_000,
    "cost_per_job_high":         250_000,
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
