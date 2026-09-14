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

THE ROUND HAS OPENED. THE INSTRUMENT HAS NOT ARRIVED. Those are two facts and
through 1.6.1 this module carried ONE BOOLEAN for both of them.

  * The CY 2026 **NOAA** is **PUBLISHED** -- Federal Register document
    2026-18883, filed 14 Sep 2026 08:45 ET, publication date 15 Sep 2026. It
    makes $5 billion in aggregate allocation authority available and sets an
    application deadline of 5:00 p.m. ET on 10 Nov 2026.
  * The CY 2026 **Allocation Application** and its Application Materials are
    **NOT published**. Confirmed by this package's maintainer on 2026-09-14.

Non-Metropolitan county designations under the CY 2026 NOAA follow OMB
Bulletin 20-01, applied using 2020 census tracts. Recorded here because it is
a CY 2026 fact this module is the right place to hold; it changes no figure in
this package and is not rendered into the note.

WHY ONE BOOLEAN WAS NOT ENOUGH -- THE 1.6.2 DEFECT

``UPCOMING_MATERIALS_PUBLISHED = False`` rendered the sentence "The CY 2026
Allocation Application and NOAA are NOT YET PUBLISHED". That is a
**CONJUNCTION**, and on 15 Sep 2026 one half of it went false while the other
stayed true. A single boolean cannot say so -- it can only be wrong in one
direction or the other, and both wrongs mislead a CDE. So the constant is split
in two, each half carries its own verified date, and the note now distinguishes
the round OPENING from the arrival of the instrument this package ENCODES.

WHAT THIS RELEASE DELIBERATELY DOES NOT CHANGE

``RECHECK_ITEMS`` still names CY 2024-2025 figures and the note still says so.
The NOAA carries the allocation authority, the application deadline and the
certification rule; it does NOT carry Question 25's ladder, Question 22's
Non-Metropolitan bounds, Question 15's product-flexibility ladder or the
Review Process thresholds. Those live in the Application Materials, which do
not exist yet. Re-working the round-specific figures now would be invention
dressed as an update -- the exact failure mode this module was written to stop.
That work is the NEXT release and its trigger is
``tests/test_round_provenance.test_live_cdfi_fund_check``.

``APPLICATION_SHA256`` also stays, and stays correct. It was never the defect;
see ``tests/test_round_provenance`` on why a hash cannot fail on staleness.

WHAT WAS SCHEDULED PAST THE EVENT

``RECHECK_AFTER`` was 2026-11-20 -- **ten days after the application deadline
it existed to protect**. The expiry would have fired for the first time on a
day when the one thing a CDE could still have done was already impossible. The
existing ceiling on the horizon (``test_the_horizon_is_not_pushed_out_of_reach``,
180 days) bounds how LONG the span may be and says nothing about whether the
horizon lands before the thing it watches. Both properties are now gated: see
``next_hard_deadline`` below, which derives the answer from the note's own
constants so the gate cannot learn one date and miss the next.
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

#: ISO dates are the ARITHMETIC form and the US long form is the PROSE form,
#: and the prose form is DERIVED so the two cannot drift. Two hand-maintained
#: spellings of one date is the same retype hazard as two copies of a hash --
#: except a wrong date reads as fine, where a wrong hash at least looks odd.
_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _us_date(iso: str) -> str:
    """``"2026-11-10"`` -> ``"November 10, 2026"``. ONE spelling, derived.

    Example::

        _us_date("2026-11-10")   # 'November 10, 2026'
    """
    year, month, day = (int(part) for part in iso.split("-"))
    return f"{_MONTH_NAMES[month - 1]} {day}, {year}"


#: WHETHER THE UPCOMING ROUND'S NOAA HAS PUBLISHED -- and, SEPARATELY, whether
#: the Allocation Application has. Through 1.6.1 this was one boolean named
#: ``UPCOMING_MATERIALS_PUBLISHED`` covering both, and the pair came apart on
#: 2026-09-15: the NOAA published, the Application did not. A conjunction
#: cannot be half-true in code, so it is two constants now.
#:
#: THESE ARE ASSERTIONS WITH DATES ON THEM, NOT MEASUREMENTS. No offline test
#: can distinguish "the Application has not published" from "nobody has looked
#: since September". ``tests/test_round_provenance.py`` does not pretend
#: otherwise: it makes the claim EXPIRE, so the failure it can produce is the
#: honest one -- staleness of the LOOKING, not of the fact.
UPCOMING_NOAA_PUBLISHED = True

#: The instrument THIS PACKAGE ENCODES. Still absent, and this is the one whose
#: flip to True obliges a rewrite of every round-specific citation.
UPCOMING_APPLICATION_PUBLISHED = False

#: The CY 2026 NOAA, pinned to its Federal Register identity rather than to a
#: page that can be re-edited underneath a citation.
NOAA_FR_DOCUMENT_NUMBER = "2026-18883"
NOAA_FILED_DATE = "2026-09-14"
NOAA_PUBLICATION_DATE = "2026-09-15"
NOAA_URL = "https://www.federalregister.gov/d/2026-18883"

#: Aggregate allocation authority the CY 2026 NOAA makes available. Carried as
#: the rendered string because the note states it as prose, and it is the one
#: CY 2026 figure the NOAA settles; every OTHER round-specific figure in this
#: package is still CY 2024-2025 and ``RECHECK_ITEMS`` still says so.
NOAA_ALLOCATION_AUTHORITY = "$5 billion"

#: HARD EXTERNAL DATES THE NOTE CARRIES. Set by the CDFI Fund, not computed
#: here, and nothing in this document moves them.
APPLICATION_DEADLINE = "2026-11-10"
APPLICATION_DEADLINE_TEXT = (
    f"5:00 p.m. ET on {_us_date(APPLICATION_DEADLINE)}"
)
AMIS_CDE_CERTIFICATION_DEADLINE = "2026-08-31"
AMIS_CDE_CERTIFICATION_DEADLINE_TEXT = (
    f"11:59 p.m. ET on {_us_date(AMIS_CDE_CERTIFICATION_DEADLINE)}"
)

#: THE DEADLINES A CDE CAN MISS, which is a narrower set than "dates this note
#: names" and the distinction is load-bearing. ``NOAA_PUBLICATION_DATE`` is an
#: AS-OF date: it fixes whose certification counts, and no reader can act on it
#: on the day. A deadline is something you can still be on the wrong side of by
#: failing to act. Only deadlines belong here, because this tuple is what
#: ``next_hard_deadline`` schedules the re-check against.
HARD_EXTERNAL_DEADLINES = (
    (AMIS_CDE_CERTIFICATION_DEADLINE, AMIS_CDE_CERTIFICATION_DEADLINE_TEXT,
     "CY 2026 CDE Certification Application submitted through AMIS"),
    (APPLICATION_DEADLINE, APPLICATION_DEADLINE_TEXT,
     "CY 2026 Allocation Application submitted to the CDFI Fund"),
)


def next_hard_deadline(today=None):
    """The earliest CY 2026 deadline that has NOT yet passed, or ``None``.

    THE RE-CHECK HORIZON MUST LAND BEFORE THIS. 1.6.1 set ``RECHECK_AFTER`` to
    2026-11-20, ten days past the application deadline, and every gate in the
    suite passed: the 180-day ceiling bounds how FAR OUT a horizon goes and
    says nothing about whether it arrives before the event it watches. This is
    the missing half, and it is DERIVED rather than typed so the gate built on
    it learns the next round's date instead of memorising this one's.

    Returns ``(iso, text, what)`` or ``None`` when every deadline has passed --
    which is itself a finding, not a quiet pass: a note whose every deadline is
    behind it describes a closed round and needs rewriting, so the gate in
    ``tests/test_round_provenance.py`` fails closed on ``None``.

    Example::

        next_hard_deadline()   # ('2026-11-10', '5:00 p.m. ET on ...', ...)
    """
    import datetime as _datetime

    if today is None:
        today = _datetime.date.today()
    upcoming = [
        entry for entry in HARD_EXTERNAL_DEADLINES
        if _datetime.date(*(int(p) for p in entry[0].split("-"))) >= today
    ]
    if not upcoming:
        return None
    return min(upcoming, key=lambda entry: entry[0])


#: When the facts above were last verified, ISO-8601. The NOAA is verified
#: against the Federal Register document named above; the ABSENCE of CY 2026
#: Application Materials was confirmed by this package's maintainer on this
#: date. Those are two different kinds of evidence and the note says which is
#: which rather than collapsing both into "verified against cdfifund.gov".
LAST_VERIFIED = "2026-09-14"

#: The date this claim goes stale and the suite goes red.
#:
#: THREE WEEKS, AND THE SHORTNESS IS THE POINT. The round is OPEN and the
#: Application Materials can drop on any business day between now and the
#: deadline; a horizon measured in months cannot catch that inside a window
#: that is itself only eight weeks long. At 2026-10-05 the expiry fires with
#: 36 days of runway left before the application deadline -- enough for a CDE
#: to act on what a re-check finds, which is the only reason to look at all.
RECHECK_AFTER = "2026-10-05"

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
        f"$10 billion in allocation authority). THE {UPCOMING_ROUND} ROUND "
        f"HAS OPENED, BUT ITS APPLICATION HAS NOT: the {UPCOMING_ROUND} NOAA "
        f"IS PUBLISHED — Federal Register document {NOAA_FR_DOCUMENT_NUMBER}, "
        f"publication date {_us_date(NOAA_PUBLICATION_DATE)} — and it makes "
        f"{NOAA_ALLOCATION_AUTHORITY} available, half the prior round, with "
        f"applications due {APPLICATION_DEADLINE_TEXT}. The "
        f"{UPCOMING_ROUND} Allocation Application and its Application "
        "Materials are NOT YET PUBLISHED, so the instrument encoded here is "
        f"still the {CITED_ROUND} one.",

        f"USE THIS, AND THEN RE-CHECK IT. The {CITED_ROUND} Application is a "
        "real federal instrument and is the right basis to prepare against "
        f"today; nothing here is unreliable. But it is a PROXY for the "
        f"{UPCOMING_ROUND} instrument, not that instrument, so every "
        f"round-specific figure in this document must be re-verified against "
        f"the {UPCOMING_ROUND} Application Materials on the day the Fund "
        f"releases them — specifically: {'; '.join(RECHECK_ITEMS)}.",

        # THE ROUTE CLOSED (1.6.2). Until this release this paragraph offered
        # a reader two options in the future conditional, on a date that had
        # already passed. Every variable in it is now settled, so it is
        # written as settled.
        f"THE {UPCOMING_ROUND} CDE CERTIFICATION CUTOFFS ARE SETTLED AND ONE "
        "OF THEM HAS ALREADY CLOSED. To be eligible to apply in "
        f"{UPCOMING_ROUND} an organization had EITHER to already be a "
        "certified CDE as of the NOAA's Federal Register publication date, "
        f"{_us_date(NOAA_PUBLICATION_DATE)}, OR to have submitted its CDE "
        "Certification Application through AMIS by "
        f"{AMIS_CDE_CERTIFICATION_DEADLINE_TEXT}. Neither route is still "
        "open. The AMIS window closed on "
        f"{_us_date(AMIS_CDE_CERTIFICATION_DEADLINE)} and it was the only "
        "way to become certified in time, so which organizations meet the "
        f"{_us_date(NOAA_PUBLICATION_DATE)} as-of date is already fixed. An "
        f"organization that did neither CANNOT APPLY IN {UPCOMING_ROUND}. "
        "There is no late filing and no cure; its next opportunity is a "
        "future round.",

        # THE THIRD OBLIGATION (1.5.0 F7). The Fund's section is headed
        # "Important Deadlines for CDE Certification AND Subsidiary CDE
        # Certification", and until 1.5.0 this note read only the first half
        # of it. The second half binds PRIOR ALLOCATEES -- which is this
        # tool's audience, not an edge case -- on the same date, and that
        # date has now passed too.
        "AND IF YOU ARE A PRIOR ALLOCATEE, A THIRD OBLIGATION FELL ON THE "
        "SAME CLOSED DATE: any prior Allocatee that required action by the "
        "CDFI Fund — certifying a Subsidiary entity as a CDE, or adding a "
        "Subsidiary CDE to an Allocation Agreement — in order to meet the "
        "Qualified Equity Investment (QEI) issuance thresholds published in "
        f"the {UPCOMING_ROUND} NOAA had to submit a CDE Certification "
        "Application for its Subsidiary CDE(s) through AMIS by "
        f"{AMIS_CDE_CERTIFICATION_DEADLINE_TEXT}. That date has passed. The "
        "QEI issuance thresholds themselves are in the NOAA, Federal Register "
        f"document {NOAA_FR_DOCUMENT_NUMBER}; this tool neither computes them "
        "nor reproduces them.",

        # THE ONE THAT IS STILL AHEAD (1.6.2). It was absent from this note
        # entirely, while three dates nobody can act on were in it.
        f"THE ONLY {UPCOMING_ROUND} DEADLINE YOU CAN STILL MISS IS THE "
        f"APPLICATION DEADLINE: {APPLICATION_DEADLINE_TEXT}. Every other "
        f"{UPCOMING_ROUND} date named above is already determined. It is set "
        "by the NOAA, it is not a figure this tool computes, and nothing in "
        f"this document moves it. Provenance: the {UPCOMING_ROUND} NOAA is "
        f"Federal Register document {NOAA_FR_DOCUMENT_NUMBER}, filed "
        f"{_us_date(NOAA_FILED_DATE)} and published "
        f"{_us_date(NOAA_PUBLICATION_DATE)}; the absence of {UPCOMING_ROUND} "
        f"Application Materials was confirmed on {_us_date(LAST_VERIFIED)}.",
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
