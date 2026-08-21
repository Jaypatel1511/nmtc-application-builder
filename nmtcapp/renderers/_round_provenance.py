"""WHICH ROUND this package reads, and why that is not the round a CDE will file.

THE DEFECT (1.5.0 S1)

Every round-specific citation in this package names the **CY 2024-2025** NMTC
Allocation Application, and names it the way you name a live instrument.
``renderers/_question_25`` and ``renderers/_question_22`` both pin its SHA-256
and quote its page numbers; ``data/benchmark_thresholds`` reads its thresholds;
``intelligence/win_probability`` and the Streamlit methodology tables render
them.

CY 2024-2025 IS CLOSED. It opened 19 Nov 2024, its deadline was 29 Jan 2025,
and it was awarded on 23 Dec 2025. Nothing in this package said so.

WHAT THE PACKAGE IS ACTUALLY DOING, STATED PLAINLY

Using the most recent PUBLISHED Application as a proxy for one that does not
exist yet. **That is the correct engineering choice.** There is no other
defensible one: the CY 2026 Application is unpublished, and a tool that
declined to encode any instrument until it appeared would be useless during
exactly the window a CDE needs it. The defect was never the choice. It was that
the choice was never disclosed, so a reader had no way to distinguish "this is
the governing instrument" from "this is the nearest available stand-in".

BOTH DIRECTIONS OF ERROR, AND THE SECOND IS EASIER TO CAUSE

  1. OVERSTATING CURRENCY -- citing a closed round as though it governed. That
     is what shipped through 1.4.0.

  2. OVERSTATING UNCERTAINTY -- writing this disclosure so a reader concludes
     the CY 2024-2025 guidance is unreliable and discounts it.

**The CY 2024-2025 Application is not unreliable.** It is a real federal
instrument, retrieved and hash-verified, and it is the best available basis for
preparing a CY 2026 application. A CDE preparing against it is doing the right
thing. A disclosure that drives a CDE to prepare against NOTHING is worse than
the stale citation it replaces -- it converts a small provenance error into an
unprepared applicant.

So the text below tells a CDE **what to re-check when CY 2026 publishes**, not
that it cannot rely on anything. It is a re-check list, not a warning label.

WHAT IS NOT CLAIMED HERE, AND WHY

That Question 25's structure is round-invariant. A truncated fetch of the CY
2022 Application showed Question **25** as a **Yes/No dropdown** -- the same
number and the same shape, two rounds earlier -- which is suggestive and is NOT
evidence of stability. The criteria list, the 85%-of-QLICIs threshold value
and the 0/5/10/15/20 ladder at 25(b)(i) were **NOT** confirmed for CY 2022. Writing
"this structure has been stable across rounds" on that evidence would be a new
false claim installed while fixing an old one, which is the exact failure this
package keeps producing. Nothing below says it.

THE CY 2026 FACTS, AND WHERE THEY CAME FROM

Retrieved first-hand from ``cdfifund.gov`` on 2026-08-20 (HTTP 200; the page
text is quoted in this round's CHANGELOG entry). The CDFI Fund's news release
of 12 Aug 2026 is the ONLY place the CY 2026 facts live -- the NMTC program
page still displays the CY 2024-2025 timeline and carries no CY 2026 NOAA, no
CY 2026 application link and no certification deadline.
"""
from __future__ import annotations

#: The round whose Application this package encodes.
CITED_ROUND = "CY 2024-2025"

#: Its status. Named as a constant rather than left implicit, because the
#: implicit version is what shipped: a hash pin that answers "is this the
#: document we read?" and is silent on "is this the round the CDE files?".
CITED_ROUND_STATUS = "closed and awarded"

#: The round a CDE reading this today is preparing for.
UPCOMING_ROUND = "CY 2026"

#: Whether the upcoming round's materials have been published.
#:
#: THIS IS AN ASSERTION WITH A DATE ON IT, NOT A MEASUREMENT. No offline test
#: can distinguish "CY 2026 has not published" from "nobody has looked since
#: August". ``tests/test_round_provenance.py`` does not pretend otherwise: it
#: makes this claim EXPIRE, so the failure it can produce is the honest one --
#: staleness of the LOOKING, not of the fact.
UPCOMING_MATERIALS_PUBLISHED = False

#: When the facts above were last verified against cdfifund.gov, ISO-8601.
LAST_VERIFIED = "2026-08-20"

#: The date this claim goes stale and the suite goes red. See the test module
#: for why an expiry is the only offline gate here that can fail at all.
RECHECK_AFTER = "2026-11-20"

#: Sources, so a re-check does not start by hunting for the page.
PROGRAM_PAGE_URL = (
    "https://www.cdfifund.gov/programs-training/programs/new-markets-tax-credit"
)
CY2026_ANNOUNCEMENT_URL = "https://www.cdfifund.gov/news/738"

#: The tab the workbook carries this note on. Named here beside the note so a
#: rename cannot leave the Q25 sheet's cross-reference pointing at nothing.
ROUND_PROVENANCE_SHEET_NAME = "Round Provenance"

#: The CY 2024-2025 Application, pinned. ONE COPY.
#:
#: It was typed into TWO module docstrings -- ``_question_22`` and
#: ``_question_25`` -- as 64 hex characters split across two source lines. Two
#: hand-typed copies of one hash is the retype hazard this package has been
#: bitten by repeatedly (``Q25_QEI_BASIS_CLAUSE`` was three copies agreeing by
#: luck), and it is worse for a hash: nobody proofreads 64 hex characters, so a
#: divergence would look like provenance while pointing at nothing.
APPLICATION_SHA256 = (
    "0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bded8de12834f"
)
APPLICATION_BYTES = 1_525_626
APPLICATION_PAGES = 142
APPLICATION_URL = (
    "https://www.cdfifund.gov/system/files/2024-11/"
    "CY_2024-2025_NMTC_Program_Allocation_Application.pdf"
)

#: What a CDE must re-verify when CY 2026 materials appear. Written as a
#: re-check list on purpose -- see this module's header on the second direction
#: of error.
RECHECK_ITEMS = (
    "the allocation authority and the number of awards available",
    "the CDE certification deadline for eligibility",
    "Question 25's QLICI-denominated commitment levels, its area-type lists "
    "and its ladder",
    "Question 22's QLICI-denominated Non-Metropolitan minimum and maximum",
    "Question 15's product-flexibility ladder",
    "the scoring thresholds in the Review Process",
)


def round_provenance_paragraphs() -> tuple:
    """``round_provenance_note()`` split into paragraphs, same text.

    WHY THIS EXISTS (1.5.0 B1). Markdown, Word and PDF each render the note as
    one flowing string. Excel cannot: a cell has a 409-pt ceiling and the note
    is far longer, so the workbook needs it one paragraph per row. The wrong
    way to get that is a second copy of the text in ``excel_builder`` -- which
    is precisely the shape this module was created to remove, where the round
    caveat existed as three separately-typed sentences that drifted apart.

    So the note is DEFINED here as paragraphs and ``round_provenance_note()``
    is their join. There is still ONE source of truth, and
    ``tests/test_round_provenance.py`` asserts the join is exactly the note, so
    the two views cannot diverge even in principle.

    Example::

        paras = round_provenance_paragraphs()
    """
    return (
        f"WHICH ROUND THIS IS BASED ON. This tool encodes the "
        f"{CITED_ROUND} NMTC Allocation Application, which is the most recent "
        f"PUBLISHED Application and is {CITED_ROUND_STATUS} (it opened "
        "19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with "
        "$10 billion in allocation authority). The "
        f"{UPCOMING_ROUND} Allocation Application and NOAA are NOT YET "
        "PUBLISHED: the CDFI Fund has announced that "
        f"{UPCOMING_ROUND} will make $5 billion available — half the prior "
        "round — and that it will publish the round's Application Materials "
        "when the round opens.",

        f"USE THIS, AND THEN RE-CHECK IT. The {CITED_ROUND} Application is a "
        "real federal instrument and is the right basis to prepare against "
        f"today; nothing here is unreliable. But it is a PROXY for the "
        f"{UPCOMING_ROUND} instrument, not that instrument, so every "
        f"round-specific figure in this document must be re-verified against "
        f"the {UPCOMING_ROUND} materials once the Fund releases them — "
        f"specifically: {'; '.join(RECHECK_ITEMS)}.",

        "SEPARATELY, AND SOONER: to be eligible to apply in "
        f"{UPCOMING_ROUND}, an organization must either already be a certified "
        "CDE as of the NOAA's Federal Register publication date, or have "
        "submitted its CDE Certification Application through AMIS by "
        "11:59 p.m. ET on August 31, 2026. That deadline is not a figure this "
        "tool computes and it does not move with anything in this document.",

        # THE THIRD OBLIGATION (1.5.0 F7). The Fund's section is headed
        # "Important Deadlines for CDE Certification AND Subsidiary CDE
        # Certification", and until this release this note read only the
        # first half of it. The second half binds PRIOR ALLOCATEES -- which
        # is this tool's audience, not an edge case -- on the same date.
        "AND IF YOU ARE A PRIOR ALLOCATEE, A THIRD OBLIGATION FALLS ON THE "
        "SAME DATE: any prior Allocatee that requires action by the CDFI Fund "
        "— certifying a Subsidiary entity as a CDE, or adding a Subsidiary CDE "
        "to an Allocation Agreement — in order to meet the Qualified Equity "
        f"Investment (QEI) issuance thresholds published in the "
        f"{UPCOMING_ROUND} NOAA must submit a CDE Certification Application "
        "for its Subsidiary CDE(s) through AMIS by 11:59 p.m. ET on "
        "August 31, 2026. Full eligibility information, including the QEI "
        "issuance thresholds themselves, comes with the NOAA when it "
        f"publishes. Verified against cdfifund.gov on {LAST_VERIFIED}.",
    )


def round_provenance_note() -> str:
    """The round-provenance disclosure, in the package's own voice.

    ONE STRING, READ EVERYWHERE. The round caveat was previously three
    separately-typed sentences -- ``_methodology.noaa_note()``,
    ``sections/base``'s placeholder and the tail of
    ``_question_25.q25_basis_note()`` -- each saying a different fraction of it
    and each able to drift from the others. That is the shape that produced the
    1.2.0 defect where a sentence was deleted from one file and stayed live in
    a second.

    The text is defined as paragraphs in ``round_provenance_paragraphs()`` and
    joined here; Excel renders the paragraphs and the other three formats
    render this join. Same words, two shapes, no second copy.

    Example::

        note = round_provenance_note()
    """
    return " ".join(round_provenance_paragraphs())
