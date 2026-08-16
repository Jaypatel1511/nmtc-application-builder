"""Shared disclosure phrasing for pipelines with unverified projects.

Two distinct degraded states flow into export surfaces:

- FULL UNAVAILABLE: ``eligibility_data_status != "ok"`` — the CDFI Fund
  dataset never loaded; no eligibility figure exists at all.
- PARTIAL UNVERIFIED: the dataset loaded, but some projects could not be
  location-verified (``unverified_project_ids`` non-empty). Figures exist
  but cover only the verified subset.

For the partial case every affected metric must carry its qualifier INLINE
("67% (2 of 6 unverified)") in the same cell/line as the number — a separate
disclaimer paragraph can be stripped in editing; an inline qualifier cannot.
"""
from __future__ import annotations


def unverified_ids(pr) -> list:
    """Unverified project IDs from a PipelineAnalysisResult (safe getattr)."""
    return list(getattr(pr, "unverified_project_ids", []) or [])


def is_partial_unverified(pr) -> bool:
    """True when data loaded OK but some projects remain unverified."""
    status_ok = getattr(pr, "eligibility_data_status", "ok") == "ok"
    return status_ok and bool(unverified_ids(pr))


def unverified_qualifier(pr) -> str:
    """Inline qualifier, e.g. ``(2 of 6 unverified)``."""
    n = len(unverified_ids(pr))
    total = getattr(pr, "total_projects", 0)
    return f"({n} of {total} unverified)"


def qualified_pct(value: float, pr, decimals: int = 0) -> str:
    """Percentage with its inline qualifier, e.g. ``67% (2 of 6 unverified)``."""
    return f"{value:.{decimals}%} {unverified_qualifier(pr)}"


def unverified_banner(pr) -> str:
    """Banner text naming the unverified project IDs.

    THIS TEXT USED TO CLAIM THE FIGURES "reflect verified projects only". They
    do not, and that was the more dangerous half of the defect: a wrong figure
    is a defect, but a wrong figure carrying an accurate-sounding disclaimer
    spends the reader's trust to conceal itself.

    What the distress figures actually do (distress_analysis.py:41 and 73-94):
    an unverified project has ``distress_level = None``, so it can never enter
    the numerator — but ``total_qei`` sums EVERY project, so it is always in the
    denominator. Measured: a pipeline whose only verified project was 100% of
    verified QEI and severely distressed reported 48.3%.

    THE ARITHMETIC IS THE HALF THAT STAYS. Two reasons, and the second decides:

      1. It aggregates over the WHOLE pipeline, which is the shape the Fund's
         own commitment takes. CY 2024-2025 Allocation Application, Question
         25(a): "at least 85% of its QLICIs (in terms of aggregate dollar
         amounts)" — aggregate over all of them, not over the subset whose
         geocoding happened to succeed. THE SHAPE, NOT THE BASIS: the Fund's
         denominator is QLICIs and this package's is QEI, and this line used to
         say the two "match", which is the claim FIX-3 removed from the
         rendered document. It is not the reason the denominator is what it is
         — reason 2 is.
      2. A verified-only denominator OVERSTATES, in the direction that flatters
         the applicant. One verified deep-distress project out of twenty would
         file "100% of QEI in deep/severe tracts". Understating is the only
         safe direction to err in a federal filing, and the current number is
         an honest lower bound.

    So the sentence changes to describe the lower bound, rather than the
    arithmetic changing to match a sentence that was wrong.

    The document carries TWO denominators on purpose, which is why this text no
    longer states one rule for all of them: the eligibility RATE uses a
    verified-only denominator and says so on its face (eligibility_check.py:62,
    "Only N% of verified QEI"), while the distress SHARES use the full pipeline.
    Each figure states its own basis; the banner stops pretending they share one.
    """
    ids = unverified_ids(pr)
    total = getattr(pr, "total_projects", 0)
    return (
        f"{len(ids)} of {total} projects could not be location-verified "
        f"(no census tract assigned): {', '.join(ids)}. "
        "Eligibility-dependent figures in this document carry inline "
        f"'{len(ids)} of {total} unverified' qualifiers. Distress and targeting "
        "shares count only location-verified projects in the numerator but all "
        "pipeline QEI in the denominator, so each is a LOWER BOUND — the true "
        "share cannot be known until every location is verified, and may be "
        "materially higher. Do not submit until all project locations are "
        "verified."
    )
