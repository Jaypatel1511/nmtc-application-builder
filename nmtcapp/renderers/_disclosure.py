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


#: How many items a truncated list shows before it says there are more.
LIST_PREVIEW_LIMIT = 5


def join_truncated(items, limit: int = LIST_PREVIEW_LIMIT) -> str:
    """Join items, and SAY SO when the list is cut — one statement of both.

    A TRUNCATED LIST UNDER AN UNTRUNCATED COUNT (1.3.1 F1). Four surfaces
    joined ``ids[:5]`` under a sentence that had already said how many there
    were. A CDE with six unverified projects read "6 project(s) ... :" and then
    five IDs, with no ellipsis and nothing saying the list was partial — so the
    sixth read as verified. The generated documents name all six, which means
    the screen and the filing disagreed and the screen is the one a CDE acts
    on before it ever generates a filing.

    The pattern was already in this repository and only one caller used it —
    ``sections/section_a_business``, on the target-states sentence. It is
    stated once here now, and that caller reads it rather than restating it,
    for the reason ``renderers/_frame_geometry`` exists: a rule recomputed at
    each call site is a rule one call site can forget.

    THE SUFFIX IS THE EXISTING ONE, UNCHANGED. " and others" is what Section A
    has rendered since 1.1.x and it is in the four committed baselines; a
    better-informed wording (" and 3 others") would move a generated document
    on a patch release, which this round exists not to do. If it is worth
    changing, it is worth changing as a document change, reviewed as one.

    Example::

        join_truncated(["IL", "OH", "MI"])                 # -> 'IL, OH, MI'
        join_truncated([f"P{i}" for i in range(7)])[-12:]  # -> ' and others'
    """
    items = [str(i) for i in items]
    return ", ".join(items[:limit]) + (" and others" if len(items) > limit else "")


def wrap_disclosure(text: str, *, width: int = 68, indent: str = "  ") -> list:
    """Return a disclosure as wrapped lines — NEVER as a truncated one.

    A DISCLOSURE MAY NOT BE CUT (1.3.1). ``benchmarks.BenchmarkResult.summary``
    printed ``self.methodology_disclosure[:140]`` of a 352-character sentence,
    with no ellipsis. What a reader saw was::

        Benchmarks compare input metrics against patterns observed in CDFI
        Fund NMTC award announcements (CY2020-CY2024). Only winner-level data is

    and what the cut removed was the whole of the disclosure's work:

        ... non-winner distributions are unknown. Scores reflect alignment with
        historical winners, NOT PROBABILITY OF SELECTION. Use as diagnostic
        guidance only — NOT AS A PREDICTION OF FUNDING OUTCOMES.

    So the surface kept the half that reads as a credential and dropped every
    clause saying the score is not a forecast — under a heading that says
    "Methodology:", which is a promise that what follows is the methodology.
    ``optimizer.OptimizationResult.summary`` cut the same class at 120
    characters, losing "Alignment score != win probability".

    Truncating body text is a display decision. Truncating a disclosure changes
    what the document says, and it changes it in the direction that flatters
    the tool. This wraps instead; a terminal that is narrower than ``width``
    reflows, and no clause is lost at any width.

    Example::

        wrap_disclosure("a b c", width=4, indent="")   # -> ['a b', 'c']
    """
    import textwrap

    return textwrap.wrap(
        " ".join(str(text).split()),
        width=max(width, 20),
        initial_indent=indent,
        subsequent_indent=indent,
    ) or [indent.rstrip()]


def qlici_not_supplied_note(pipeline) -> str:
    """Appendix A's disclosure when no QLICI amount was supplied — or ``""``.

    WHY WORD AND PDF NEED A SENTENCE AND NOT A CELL (1.3.0 S3).

    ``tables/pipeline_table``'s "Total QLICI ($)" column reaches only TWO
    surfaces, not four: markdown renders the full 33-column table and Excel
    writes it to the Pipeline Detail sheet, while Word and PDF print the
    six-column ``build_pipeline_summary_table`` in portrait and Word's landscape
    continuation names twelve columns of which QLICI is not one. So the
    defaulted figure was never printed on Word or PDF, and there is no cell
    there to correct — which was worth establishing rather than assuming, since
    the alternative fix (inventing a QLICI column for two surfaces that
    deliberately do not carry one) would have changed the shape of a federal
    attachment to make a test pass.

    What Word and PDF DO carry is a caption directing the reader to the
    workbook for "QLICI structure". A CDE reading only the filed document would
    otherwise learn nothing about a column it never supplied, so the fact goes
    beside that caption. One sentence, one authority, both surfaces.

    Returns an empty string when every project supplied the figure, so the
    caller can append unconditionally.
    """
    missing = [p.project_id for p in pipeline
               if not getattr(p, "qlici_amount_supplied", True)]
    if not missing:
        return ""
    total = sum(1 for _ in pipeline)
    return (
        f"NO QLICI AMOUNT WAS SUPPLIED for {len(missing)} of {total} projects "
        f"({', '.join(missing)}). Each project's QEI request was used in its "
        "place so this pipeline could be analysed, and that figure is NOT the "
        "CDE's QLICI amount: the workbook's Total QLICI column reads "
        "'not supplied [CDE TO COMPLETE]' rather than a number, and the "
        "QLICI <= QEI consistency check is reported as not checkable rather "
        "than passed. Supply a qlici_amount for every project before filing."
    )


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
