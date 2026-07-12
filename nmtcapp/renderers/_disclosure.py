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
    """Banner text naming the unverified project IDs."""
    ids = unverified_ids(pr)
    total = getattr(pr, "total_projects", 0)
    return (
        f"{len(ids)} of {total} projects could not be location-verified "
        f"(no census tract assigned): {', '.join(ids)}. "
        "Eligibility-dependent figures in this document carry inline "
        f"'{len(ids)} of {total} unverified' qualifiers and reflect verified "
        "projects only. Do not submit until all project locations are verified."
    )
