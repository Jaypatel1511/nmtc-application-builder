"""THE ROUND GATE: the hash pin cannot fail on staleness, so something else must.

THE GATE THAT CANNOT FAIL

``renderers/_question_25`` pins the CY 2024-2025 Application's SHA-256. That pin
is CORRECT -- re-downloaded and re-verified this round, byte count and all 64
hex characters identical. It is also, on its own, the nineteenth recorded
instance in this project of a gate that cannot fail, and the FIRST one caught
before it fired rather than after.

The reason is that it answers the wrong question:

    the hash asks   "is this the document we read?"          -> yes, forever
    nobody asks     "is this the round the CDE FILES?"       -> no, since
                                                                 Dec 2025

When CY 2026 publishes, the hash still matches, the suite is still green, and
every citation in the package is stale. A hash pins an ARTIFACT against
corruption. It says nothing about that artifact's RELEVANCE, and relevance is
the property that decays.

ATTACKING THE OBVIOUS FIX

The candidate design was "a round label and a published-status assertion pinned
beside the hash". Half right. ``_round_provenance`` now carries
``CITED_ROUND``, ``CITED_ROUND_STATUS`` and the published-status booleans,
which makes the staleness a FACT IN THE CODE rather than an omission -- a real
improvement, because a reader of the module now sees it.

But as a GATE it is worthless on its own, and saying so is the point:

    ``UPCOMING_APPLICATION_PUBLISHED = False`` is a sentence somebody typed.
    Nothing flips it. A test asserting the code agrees with itself is the
    tautology ``test_version_sync`` already is (see 1.5.0 S6), and a dated
    assertion nobody re-reads is just another gate that cannot fail.

SO: CAN A TEST DISTINGUISH "CY 2026 HAS NOT PUBLISHED" FROM "NOBODY HAS LOOKED
SINCE AUGUST"?

**Offline, no. Categorically.** Publication is a fact about the world. An
offline test can only read what somebody wrote down, so it can only ever
re-report the writing. No amount of cleverness gets around that, and a gate
that implied otherwise would be worse than none.

What an offline test CAN do is fail on the SECOND condition. That is what this
module does, and it is the honest half:

  ``test_the_round_claim_has_not_expired`` fails when today is past
  ``RECHECK_AFTER``. It detects STALE LOOKING, not stale facts. It cannot tell
  you CY 2026 published yesterday. It CAN tell you nobody has checked in three
  months, which is the failure mode that actually produced this defect -- the
  CY 2024-2025 citation did not go wrong because anyone decided wrongly, it
  went wrong because the world moved and no one was scheduled to look.

  IT DEGRADES TO RITUAL IF BUMPED ROTE, and pretending otherwise would be the
  same self-flattery this suite keeps auditing out. Two things make a rote bump
  less likely and neither makes it impossible: the date lives in the same file
  as the round claim, so the bumper is looking at the claim; and the failure
  message names the two URLs and the specific things to look for, so checking
  properly is cheaper than inventing a reason not to.

  ``test_live_cdfi_fund_check`` is the half that CAN answer the real question:
  it fetches the CDFI Fund program page and asserts CY 2026 materials are still
  absent. It is NOT A GATE -- it is opt-in (``-m network``) and skipped by
  default, because a suite whose greenness depends on a federal website being
  up is a suite that goes red for reasons having nothing to do with this
  repository. A skipped-by-default test cannot fail in CI, and calling it a
  gate would be the vacuity this file exists to name. It is a TOOL, run when
  the expiry fires.

Together: the expiry says WHEN to look, the live check answers WHAT IS TRUE,
and neither pretends to be the other.

IT HAPPENED. 2026-09-14, AND THE SENTENCE ABOVE WAS RIGHT (1.6.2)

The CY 2026 NOAA published -- Federal Register document 2026-18883,
publication date 15 Sep 2026. The hash still matched. The suite was still
green. And the note said "The CY 2026 Allocation Application and NOAA are NOT
YET PUBLISHED", which was now half false.

READ WHAT THIS MODULE GOT RIGHT AND WHAT IT STILL MISSED, because the second
is the useful part:

  RIGHT -- it named the class exactly, in writing, before the event. The
  expiry was the correct instrument and the reasoning above needs no
  correction.

  MISSED -- **it scheduled the check past the event.** ``RECHECK_AFTER`` was
  2026-11-20; the application deadline it protects is 2026-11-10. The expiry
  would have fired for the first time TEN DAYS AFTER the last day a CDE could
  have acted on what it found. A gate that is correct about WHAT to look for
  and wrong about WHEN is not a partial gate, it is a gate that cannot fire in
  time -- the same vacuity in a new costume.

  ``test_the_horizon_is_not_pushed_out_of_reach`` did not catch it and was
  never going to: a 180-day CEILING bounds how far out a horizon goes. It has
  no opinion on whether the horizon lands before the thing it watches. 92 days
  passed it happily.

SO THE THIRD GATE, AND WHY IT IS DERIVED

``test_the_horizon_lands_before_the_deadline_it_watches`` reads
``_round_provenance.next_hard_deadline()`` -- the earliest deadline the NOTE
ITSELF carries that has not yet passed -- and requires ``RECHECK_AFTER`` to
precede it. The date is NOT typed into this file on purpose. A test that
learned "2026-11-10" would pass the next round while pointing at a date from
this one, which is the identical failure one level up.

It fails closed when every deadline has passed: a note whose dates are all
behind it is describing a closed round, and that is a finding rather than a
quiet green.

AND THE CONJUNCTION

``UPCOMING_MATERIALS_PUBLISHED`` was ONE boolean over TWO facts, so the false
sentence could not be half-corrected. It is now
``UPCOMING_NOAA_PUBLISHED`` (True) and ``UPCOMING_APPLICATION_PUBLISHED``
(False), and ``test_the_round_state_is_pinned`` -- the rewrite of what used to
be ``test_upcoming_materials_are_still_unpublished`` -- breaks when EITHER
moves. It is still deliberately weak and still not evidence about the world.

"""
from __future__ import annotations

import datetime as _dt
import os
import re
import sys

import pytest

from nmtcapp.renderers import _round_provenance as rp

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _iso(value: str) -> _dt.date:
    return _dt.date(*(int(part) for part in value.split("-")))


#: The timezone every federal publication date in this module is a date IN.
#:
#: A Federal Register document publishes on its EASTERN date, and the
#: application deadline the note carries is written "5:00 p.m. ET". These are
#: not facts about the machine running pytest, so no gate over them may consult
#: the machine's clock-in-its-own-zone.
_FEDERAL_TZ = "America/New_York"


def _eastern_date(instant=None) -> _dt.date:
    """The date in ``America/New_York`` at ``instant`` (default: now).

    WHY ET AND NOT LOCAL, AND NOT UTC EITHER (1.6.2 R2)

    ``test_no_federal_event_is_stated_as_having_happened_before_it_has`` used
    ``_dt.date.today()`` -- the RUNNER's local date -- and that made the gate's
    verdict a property of the machine. Measured, on 2026-09-15 00:53 UTC, with
    ``NOAA_PUBLICATION_DATE = 2026-09-15``:

        maintainer's Mac (UTC-5, 19:53)   local date 2026-09-14   -> RED
        this bridge VM   (UTC,    00:53)  local date 2026-09-15   -> GREEN
        GitHub Actions   (UTC)            local date 2026-09-15   -> GREEN

    Three machines, one repository, one moment, two answers. The RED one was
    right about the world -- it was 20:53 EDT and the NOAA had not published --
    and CI would have shipped past it.

    UTC IS NOT THE FIX, IT IS THE SAME BUG WITH A NICER NAME. It agrees with ET
    for nineteen hours a day and disagrees for five, and the five are exactly
    the evening hours in which somebody finishes a release. A publication date
    is not a UTC date; it is the date the document bears, which the Federal
    Register assigns in Eastern Time. So the comparison is done in the zone the
    fact lives in, and then every machine returns the same verdict.

    ``instant`` must be TIMEZONE-AWARE when given. A naive datetime is exactly
    the ambiguity this function exists to remove, so it is refused rather than
    guessed at.

    Example::

        _eastern_date(_dt.datetime(2026, 9, 15, 0, 53, tzinfo=_dt.timezone.utc))
        # date(2026, 9, 14)  -- 20:53 the previous evening, in ET
    """
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    if instant is None:
        instant = _dt.datetime.now(_dt.timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError(
            f"_eastern_date() needs a timezone-AWARE instant; got {instant!r}. "
            "A naive datetime is the ambiguity this function exists to remove."
        )
    try:
        zone = ZoneInfo(_FEDERAL_TZ)
    except ZoneInfoNotFoundError as exc:            # pragma: no cover
        raise AssertionError(
            f"the {_FEDERAL_TZ} timezone is not available on this machine "
            f"({exc}), so no gate here can compare a federal date correctly.\n\n"
            "THIS DELIBERATELY DOES NOT FALL BACK TO LOCAL TIME. A silent "
            "fallback is the defect this helper replaced: it would make the "
            "verdict machine-dependent again and nothing would say so. "
            "Install the `tzdata` package."
        ) from exc
    return instant.astimezone(zone).date()


#: Phrases in the rendered note that assert a federal event HAS HAPPENED.
#: Read off the note rather than off ``UPCOMING_NOAA_PUBLISHED``, because no
#: branch in ``round_provenance_paragraphs`` consults that constant -- a gate
#: on the boolean alone would watch a variable the sentence never reads.
_PRESENT_PERFECT_FEDERAL_CLAIMS = ("ROUND HAS OPENED", "NOAA IS PUBLISHED")


def _federal_events_stated_as_done(note: str) -> list:
    """Which "already happened" claims the rendered note actually makes.

    Factored out of the gate below so the gate's VERDICT can be evaluated at
    frozen instants without a clock. ``test_the_future_event_gate_is_the_same_
    on_every_machine`` needs exactly that: the defect it pins is about WHICH
    DATE gets compared, and a property you can only observe through
    ``datetime.now()`` cannot be tested on both sides of a boundary.
    """
    return sorted(
        phrase for phrase in _PRESENT_PERFECT_FEDERAL_CLAIMS if phrase in note
    )


def _claims_an_unhappened_event(note: str, published: _dt.date,
                                today: _dt.date) -> list:
    """The gate's property, as a pure function of the three things it reads.

    Returns the offending phrases, or ``[]`` when the note is honest.
    """
    stated = _federal_events_stated_as_done(note)
    return stated if (stated and published > today) else []


#: Every format the application renders to. The gate below asserts the round
#: provenance reaches ALL of them, and the tuple is written out rather than
#: imported so that a format being dropped from the renderer cannot silently
#: shrink what this gate checks.
_ALL_FORMATS = ("markdown", "word", "excel", "pdf")

#: Phrases that must survive into every rendered artifact. Each one is a
#: DISTINCT fact a reader loses if it is missing, not a restatement:
#:   - which round this encodes, and that it is over
#:   - that the CY 2026 round has OPENED while its Application has not arrived
#:     (one sentence used to carry both halves and went half-false on
#:     2026-09-15; these are two entries now for the same reason the source
#:     constant is two booleans)
#:   - the deadline a CDE can still miss, which was absent entirely through
#:     1.6.1 while three dates nobody could act on were present
#:   - the AMIS certification deadline, which is external, hard and closed
#:   - the third obligation, which binds prior Allocatees (F7)
#:
#: EXCEL IS THE FORMAT THAT MATTERS MOST HERE. It is the one circulated
#: internally and pasted from, so a false sentence does the most damage there
#: and survives longest.
_PROVENANCE_FACTS = (
    ("closed and awarded", "which round this encodes, and that it is closed"),
    ("ROUND HAS OPENED, BUT ITS APPLICATION HAS NOT",
     "that the round is open while the instrument this tool encodes is not"),
    ("NOAA IS PUBLISHED", "that the CY 2026 NOAA exists and governs the round"),
    ("Materials are NOT YET PUBLISHED",
     "that the Application a CDE will file still has no materials"),
    # THE TWO DATES ARE DERIVED, NOT TYPED (1.6.4). This tuple carried
    # "August 31, 2026" as a literal, and the literal was the defect: it was
    # the pre-announcement's date, the NOAA's Table 1 says 22 Sep, and a gate
    # that types the date it checks for can only confirm the typo it shares
    # with the source. tests/test_noaa_table_1 checks the constants against
    # the Federal Register's own text; this gate checks that they RENDER.
    (rp.APPLICATION_DEADLINE_TEXT,
     "the application deadline, in full, on every surface"),
    (rp.AMIS_CDE_CERTIFICATION_DEADLINE_TEXT,
     "the AMIS CDE certification deadline, in full, on every surface -- "
     "whether it is still ahead or has passed"),
    ("Subsidiary CDE", "the prior-Allocatee Subsidiary CDE obligation"),
)


def _render_all_formats(tmp_path) -> dict:
    """Render the sample application to every format; return {fmt: text}."""
    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    paths = app.generate(str(tmp_path), formats=list(_ALL_FORMATS))

    # FAILS CLOSED. A format that does not render is a format this gate would
    # otherwise pass by not looking at.
    assert set(paths) == set(_ALL_FORMATS), (
        f"rendered {sorted(paths)}, expected {sorted(_ALL_FORMATS)} — a format "
        "that silently does not render is a format this gate is not checking"
    )

    out = {}
    for fmt, path in paths.items():
        if fmt == "markdown":
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        elif fmt == "word":
            from docx import Document
            doc = Document(path)
            parts = [para.text for para in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.extend(cell.text for cell in row.cells)
            text = "\n".join(parts)
        elif fmt == "excel":
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            parts = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    parts.extend(str(v) for v in row if v is not None)
            text = "\n".join(parts)
        else:
            from pypdf import PdfReader
            text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)

        assert text.strip(), f"{fmt} extracted as empty text"
        # PDF and Word wrap; compare on collapsed whitespace so a line break
        # inside a phrase is not read as the phrase being absent.
        out[fmt] = re.sub(r"\s+", " ", text)
    return out


def test_the_round_provenance_reaches_all_four_formats(tmp_path):
    """The disclosure must render in EVERY format, not three of four.

    THIS GATE IS THE DELIVERABLE, NOT THE EXCEL BLOCK IT CHECKS (1.5.0 B1).

    Through 1.5.0 the note reached markdown, Word and PDF. The workbook
    carried none of it -- and carried the citation anyway, in the present
    tense and in the Fund's voice, at row 4 of the 'Q25 Basis Note' sheet:
    "Question 25 of the CY 2024-2025 NMTC Allocation Application (printed
    pp. 38-41) sets both commitments." A CDE who opened only the workbook got
    a federal citation with no notice that the round had closed on
    29 Jan 2025, that CY 2026 was unpublished, or that a hard external
    certification deadline fell on 31 Aug 2026.

    Excel is the format most likely to be circulated internally and pasted
    from, so it was the worst of the four to leave silent. It was silent
    because the gates counted formats that HAD the note rather than formats
    that MUST. Adding the block without adding this test would fix the site
    and leave the class -- which is the shape this project has recorded
    repeatedly, and the reason the assertion below is parameterised over
    _ALL_FORMATS rather than naming the workbook.
    """
    rendered = _render_all_formats(tmp_path)

    missing = [
        (fmt, phrase, why)
        for fmt, text in rendered.items()
        for phrase, why in _PROVENANCE_FACTS
        if phrase not in text
    ]
    assert not missing, (
        "round provenance is missing from rendered output:\n\n"
        + "\n".join(
            f"  {fmt:<9} lacks {phrase!r} — the reader loses {why}"
            for fmt, phrase, why in missing
        )
        + "\n\nEvery format that cites a round must say which round it is and "
        "that it is closed. Render the note from "
        "_round_provenance.round_provenance_paragraphs(); do not retype it."
    )


def test_the_paragraph_view_is_exactly_the_note():
    """The two shapes of the note cannot drift, because one builds the other.

    Excel needs the note one paragraph per row (a merged cell has a 409-pt
    ceiling and the note is longer). The wrong way to get that is a second
    copy in excel_builder -- the exact shape that produced the 1.2.0 defect
    where a sentence was corrected in one file and left live in another. So
    the paragraphs are the definition and the note is their join, and this
    asserts it stays that way.
    """
    joined = " ".join(rp.round_provenance_paragraphs())
    assert joined == rp.round_provenance_note(), (
        "round_provenance_note() is no longer the join of "
        "round_provenance_paragraphs(). Excel renders the paragraphs and the "
        "other three formats render the note, so they have just diverged: one "
        "artifact now says something the others do not."
    )


# ---------------------------------------------------------------------------
# The offline half
# ---------------------------------------------------------------------------

def test_the_round_claim_has_not_expired():
    """FAILS ON TIME. The only offline failure available here, and it is real.

    This does not check whether CY 2026 published. It checks whether anybody
    has looked recently, which is a different and weaker claim -- and it is the
    one that failed. See this module's header.
    """
    today = _dt.date.today()
    recheck = _iso(rp.RECHECK_AFTER)
    assert today <= recheck, (
        f"the {rp.UPCOMING_ROUND} round claim expired on {rp.RECHECK_AFTER} "
        f"(today is {today.isoformat()}). Nobody has verified it since "
        f"{rp.LAST_VERIFIED}.\n\n"
        "THIS IS NOT A FAILING BUILD, IT IS A SCHEDULED RE-CHECK. Do it now:\n\n"
        f"  1. {rp.PROGRAM_PAGE_URL}\n"
        "     -- have the CY 2026 ALLOCATION APPLICATION MATERIALS appeared? "
        "That is the question now. The NOAA published on "
        f"{rp.NOAA_PUBLICATION_DATE} (Federal Register "
        f"{rp.NOAA_FR_DOCUMENT_NUMBER}); the Application had not as of "
        f"{rp.LAST_VERIFIED}.\n"
        f"  2. {rp.CY2026_ANNOUNCEMENT_URL}\n"
        "     -- is there a newer release than the 12 Aug 2026 one?\n"
        f"  3. {rp.NOAA_URL}\n"
        "     -- the NOAA itself, for the authority, the deadline and the "
        "certification rule.\n\n"
        "Then EITHER set UPCOMING_APPLICATION_PUBLISHED = True and open the "
        "re-verification work in _round_provenance.RECHECK_ITEMS, OR bump "
        "LAST_VERIFIED and RECHECK_AFTER.\n\n"
        "RECHECK_AFTER MUST STILL LAND BEFORE "
        f"{(rp.next_hard_deadline() or ('—', '', ''))[0]}, the next deadline "
        "this note carries — a horizon past it is a re-check nobody can act "
        "on, which is what 1.6.1 shipped.\n\n"
        "Bumping the dates WITHOUT opening those two pages turns this into a "
        "gate that cannot fail, which is the exact thing it was built to "
        "replace. `pytest -m network tests/test_round_provenance.py` does the "
        "check for you."
    )


def test_the_recheck_horizon_is_after_the_verification():
    """A horizon before its own verification date is already expired."""
    assert _iso(rp.RECHECK_AFTER) > _iso(rp.LAST_VERIFIED), (
        f"RECHECK_AFTER ({rp.RECHECK_AFTER}) is not after LAST_VERIFIED "
        f"({rp.LAST_VERIFIED})."
    )


def test_the_horizon_is_not_pushed_out_of_reach():
    """A far-enough horizon is an abstention wearing a gate's clothes.

    MAX_HORIZON_DAYS is the difference between "re-check quarterly" and "this
    will fire after I have stopped working on it". Without a ceiling, the
    cheapest response to a red expiry is +5 years, and the gate is gone with
    nobody having decided to remove it.
    """
    span = (_iso(rp.RECHECK_AFTER) - _iso(rp.LAST_VERIFIED)).days
    assert span <= 180, (
        f"the re-check horizon is {span} days. An NMTC round opens, runs and "
        "closes inside that window, so a horizon this long cannot catch the "
        "transition it exists for. Keep it to a quarter or so; if the round "
        "genuinely has not moved, re-verifying costs two page loads."
    )



def test_the_horizon_lands_before_the_deadline_it_watches():
    """THE GATE 1.6.1 DID NOT HAVE. A ceiling is not a landing point.

    ``RECHECK_AFTER`` was 2026-11-20 and the application deadline it exists to
    protect is 2026-11-10. Every gate in this module passed. The expiry would
    have fired for the first time ten days after the last day anyone could
    have acted on it -- correct about WHAT to check, ten days wrong about
    WHEN, and therefore useless.

    ``test_the_horizon_is_not_pushed_out_of_reach`` could not catch this and
    was never meant to: 92 days is comfortably inside its 180-day ceiling. A
    ceiling bounds how far out a horizon goes. It has no opinion on whether
    the horizon arrives before the event.

    THE DATE IS NOT WRITTEN IN THIS FILE, DELIBERATELY. It comes from
    ``_round_provenance.next_hard_deadline()``, which reads the note's own
    constants. A test that learned "2026-11-10" would go on passing into
    CY 2027 while guarding a date from CY 2026 -- the same failure one level
    up, which is the shape this whole module exists to refuse.

    FAILS CLOSED ON None. When every deadline the note carries has passed, the
    note describes a closed round. That is a finding, not a quiet green.
    """
    upcoming = rp.next_hard_deadline()
    assert upcoming is not None, (
        "every hard deadline in _round_provenance.HARD_EXTERNAL_DEADLINES is "
        f"in the past (today is {_dt.date.today().isoformat()}). This note "
        f"now describes a CLOSED {rp.UPCOMING_ROUND} round: the application "
        "deadline has gone by and the package is still citing the round as "
        "upcoming.\n\n"
        "This is not a date to bump. Re-check the Fund, then rewrite the note "
        "for whatever round is now next."
    )
    iso, text, what = upcoming
    assert _iso(rp.RECHECK_AFTER) < _iso(iso), (
        f"RECHECK_AFTER is {rp.RECHECK_AFTER}, which is NOT before {iso} — "
        f"the next hard deadline this note carries ({what}, {text}).\n\n"
        "A re-check scheduled after the deadline it protects cannot change "
        "anything by the time it fires. That is exactly what 1.6.1 shipped: "
        "RECHECK_AFTER 2026-11-20 against a 2026-11-10 deadline, with the "
        "whole suite green.\n\n"
        "Move RECHECK_AFTER inside the window. The round is live; weeks, not "
        "months."
    )


def test_every_hard_deadline_the_constants_carry_reaches_the_note():
    """A deadline in the constants and not in the note is a deadline nobody sees.

    This is the anti-dodge half of the gate above. ``next_hard_deadline()``
    schedules against ``HARD_EXTERNAL_DEADLINES``, so the cheapest way to make
    a red horizon go green is to quietly drop an entry from that tuple. This
    binds the tuple to the rendered text: anything the gate schedules against
    must be something a CDE can actually read.
    """
    assert rp.HARD_EXTERNAL_DEADLINES, (
        "HARD_EXTERNAL_DEADLINES is EMPTY. Everything below this line passes "
        "on nothing: `missing` is [] over an empty tuple and the assertion "
        "holds vacuously.\n\n"
        "This is the anti-dodge gate, so emptying the tuple is precisely the "
        "dodge it exists to catch, and without this line it is the ONE dodge "
        "it could not see. A note that carries no hard external deadline at "
        "all is not a passing state; it is a note with nothing to schedule "
        "the re-check against."
    )
    note = rp.round_provenance_note()
    missing = [
        f"{what}: {text!r}"
        for _iso_date, text, what in rp.HARD_EXTERNAL_DEADLINES
        if text not in note
    ]
    assert not missing, (
        "HARD_EXTERNAL_DEADLINES carries deadlines the note never states:\n  "
        + "\n  ".join(missing)
        + "\n\nThe re-check horizon is scheduled against this tuple. A "
        "deadline that is in the tuple and not in the note is one the gate "
        "watches and the reader never sees."
    )


def test_no_federal_event_is_stated_as_having_happened_before_it_has():
    """B3 (1.6.2). The note stated a FUTURE federal event in the past tense.

    WHAT SHIPPED ON THE BRANCH. Paragraph 0 read "THE CY 2026 ROUND HAS
    OPENED" and "the CY 2026 NOAA IS PUBLISHED" -- both in the present perfect
    -- while naming a publication date of 15 Sep 2026 and stamping the
    document ``LAST_VERIFIED = 2026-09-14``. On 14 Sep 2026 the package
    asserted, in all four formats, that a thing scheduled for tomorrow had
    already happened.

    THE CALENDAR CLEARED IT AND THE CALENDAR IS NOT A GATE. By 15 Sep 2026 the
    three sentences are true and can never be false again for THIS round. That
    is exactly why this test is here: the defect was not the sentences, it was
    that nothing in the suite compared a stated federal event against its own
    date, so the next round will reproduce it the first time somebody writes
    the note between the Federal Register FILING and its PUBLICATION -- which
    is the natural moment to write it, because that is when the document
    becomes readable.

    THE DATE IS NOT WRITTEN IN THIS FILE. It is read from
    ``NOAA_PUBLICATION_DATE`` and compared against the clock, so the gate
    learns the next round's date instead of memorising this one's.

    READ OFF THE RENDERED NOTE, NOT OFF THE BOOLEAN. ``round_provenance_
    paragraphs`` states the round has opened in plain prose; no branch in it
    reads ``UPCOMING_NOAA_PUBLISHED``, so a gate on the constant alone would
    watch a variable the sentence does not consult.

    THE OTHER DIRECTION IS DELIBERATELY NOT ASSERTED HERE. "The date has
    passed and the package still says the NOAA has not published" is
    understatement, not a false federal claim, and
    ``test_the_round_state_is_pinned`` already fails when either constant
    moves. One property per gate.

    AND ``LAST_VERIFIED`` IS NOT COMPARED TO IT EITHER, ON PURPOSE. It is
    2026-09-14, a day BEFORE the publication date -- and that is legitimate: a
    Federal Register document is on public inspection from its FILING, which
    the note itself states as 14 Sep 2026. Gating verification against
    publication would red-flag the correct practice of reading the filed
    document.

    "TODAY" IS THE EASTERN DATE, NOT THE RUNNER'S (1.6.2 R2)

    This gate shipped comparing against ``_dt.date.today()``, and that made
    its verdict a property of the machine rather than of the world. On
    2026-09-15 00:53 UTC it was RED on the maintainer's Mac (local 2026-09-14)
    and GREEN in CI and on the bridge VM (local/UTC 2026-09-15). The RED one
    was correct -- 20:53 EDT, the NOAA not yet published -- and the gate that
    was going to decide the release was the green one.

    A Federal Register publication date is an EASTERN TIME fact: the document
    bears the ET date the Register assigns it. So the comparison is made in
    ``America/New_York`` via ``_eastern_date`` and every machine now returns
    the same answer. Switching to UTC would have hidden the disagreement
    without removing it -- UTC and ET differ for five hours of every day, and
    those five hours are the evening in which releases get cut.

    ``_claims_an_unhappened_event`` holds the property as a pure function so
    that ``test_the_future_event_gate_is_the_same_on_every_machine`` can
    exercise it at frozen instants either side of ET midnight, including the
    instant at which UTC and ET disagree. A rule about which clock to read
    cannot be checked by reading the clock.
    """
    today = _eastern_date()
    published = _iso(rp.NOAA_PUBLICATION_DATE)
    note = rp.round_provenance_note()

    stated_as_done = _federal_events_stated_as_done(note)
    assert not (stated_as_done and published > today), (
        f"the note states {stated_as_done} -- the present perfect, a thing "
        f"that has ALREADY happened -- while NOAA_PUBLICATION_DATE is "
        f"{rp.NOAA_PUBLICATION_DATE} and today in {_FEDERAL_TZ} is "
        f"{today.isoformat()}. The event is {(published - today).days} day(s) "
        f"in the FUTURE.\n\n"
        "A CDE reading this document today is told a federal round has opened "
        "when it has not. Either the date is wrong, or the sentence is early "
        "and must be written in the future tense until the date arrives. A "
        "document filed for public inspection is not yet published; the note "
        "already carries both dates and can say which one it means.\n\n"
        f"THE DATE COMPARED IS THE EASTERN ONE, NOT THIS MACHINE'S. If your "
        f"local clock already reads {_dt.date.today().isoformat()}, that is "
        "not a reason to dismiss this: the Federal Register publishes on its "
        "ET date and this gate answers the same on every machine on purpose. "
        "It goes green by itself when the ET date arrives."
    )


#: Frozen instants either side of ET midnight on the NOAA publication date,
#: with the ET date each one falls on. 2026-09-15 is EDT (UTC-4), so ET
#: midnight is 04:00 UTC and the two rows around it are the whole point:
#: 03:59 UTC is ALREADY 15 Sep in UTC and STILL 14 Sep in Eastern Time. That
#: is the disagreement that produced the defect -- the maintainer's machine
#: said the 14th and CI said the 15th at the same instant.
_ET_BOUNDARY_CASES = (
    ("2026-09-15T03:59:00+00:00", _dt.date(2026, 9, 14), "UTC and ET DISAGREE"),
    ("2026-09-15T04:00:00+00:00", _dt.date(2026, 9, 15), "ET midnight exactly"),
    ("2026-09-15T04:01:00+00:00", _dt.date(2026, 9, 15), "one minute after"),
    ("2026-09-14T23:59:00+00:00", _dt.date(2026, 9, 14), "same date both zones"),
    ("2026-09-16T12:00:00+00:00", _dt.date(2026, 9, 16), "well past, both zones"),
)

#: Runner timezones to prove the verdict against. Chosen to straddle: one east
#: of ET, one far east enough to be a whole calendar day ahead, one west, and
#: UTC itself, which is what CI runs and what made this invisible.
_RUNNER_TIMEZONES = ("UTC", "America/Los_Angeles", "Asia/Tokyo",
                     "Pacific/Kiritimati", "America/New_York")


def test_the_future_event_gate_is_the_same_on_every_machine():
    """THE DEFECT WAS WHICH CLOCK, SO THE TEST CANNOT BE ALLOWED TO READ ONE.

    ``test_no_federal_event_is_stated_as_having_happened_before_it_has``
    compared ``NOAA_PUBLICATION_DATE`` against ``_dt.date.today()``. At
    2026-09-15 00:53 UTC that was 2026-09-14 on the maintainer's machine and
    2026-09-15 in CI: the gate went red where it should and green where the
    release was going to be cut from. Not a flake -- a gate whose answer
    depended on the runner.

    This asserts the fix as a PROPERTY rather than as an outcome: at a fixed
    instant, ``_eastern_date`` and therefore the gate's verdict must not move
    when the runner's ``TZ`` moves. ``time.tzset()`` makes the runner's zone
    an input instead of an assumption, so the claim is demonstrated rather
    than reasoned about.

    THE LAST BLOCK IS THE CONTROL, AND IT IS THE LOAD-BEARING ONE. It shows
    the OLD approach really does give different answers at these same
    instants. Without it, this test would pass just as happily against an
    implementation that had never been broken, and would be evidence of
    nothing.

    POSIX ONLY. ``time.tzset()`` does not exist on Windows. CI is
    ubuntu-latest and the maintainer is on macOS, so this runs everywhere it
    is run; on Windows it skips rather than pretending to have checked.
    """
    import time

    if not hasattr(time, "tzset"):                  # pragma: no cover
        pytest.skip("time.tzset() is POSIX-only; cannot vary TZ in-process")

    published = _iso(rp.NOAA_PUBLICATION_DATE)
    honest_note = "nothing has happened yet"
    claiming_note = "THE CY 2026 ROUND HAS OPENED and the NOAA IS PUBLISHED"

    original_tz = os.environ.get("TZ")
    observed = {}
    try:
        for zone_name in _RUNNER_TIMEZONES:
            os.environ["TZ"] = zone_name
            time.tzset()
            for iso_instant, expected_et, why in _ET_BOUNDARY_CASES:
                instant = _dt.datetime.fromisoformat(iso_instant)
                actual_et = _eastern_date(instant)
                assert actual_et == expected_et, (
                    f"with TZ={zone_name}, _eastern_date({iso_instant}) "
                    f"returned {actual_et}, not {expected_et} ({why}). The "
                    "Eastern date at an instant is a fact about that instant; "
                    "if the runner's zone can change it, the gate built on it "
                    "is machine-dependent again."
                )
                verdict = tuple(_claims_an_unhappened_event(
                    claiming_note, published, actual_et))
                observed.setdefault(iso_instant, {})[zone_name] = verdict

                assert not _claims_an_unhappened_event(
                    honest_note, published, actual_et), (
                    "a note claiming nothing cannot be claiming something "
                    "unhappened, whatever the date or the runner's zone"
                )
    finally:
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()

    disagreed = {
        instant: verdicts for instant, verdicts in observed.items()
        if len(set(verdicts.values())) != 1
    }
    assert not disagreed, (
        "the gate returned different verdicts for the same instant under "
        f"different runner timezones: {disagreed}. That is the 1.6.2 defect "
        "exactly."
    )

    # The verdicts themselves, so this is not merely "consistent" — a gate
    # that answered "no problem" everywhere would also be consistent.
    expected_verdicts = {
        "2026-09-15T03:59:00+00:00": ("NOAA IS PUBLISHED", "ROUND HAS OPENED"),
        "2026-09-15T04:00:00+00:00": (),
        "2026-09-15T04:01:00+00:00": (),
        "2026-09-14T23:59:00+00:00": ("NOAA IS PUBLISHED", "ROUND HAS OPENED"),
        "2026-09-16T12:00:00+00:00": (),
    }
    actual_verdicts = {
        instant: next(iter(set(verdicts.values())))
        for instant, verdicts in observed.items()
    }
    assert actual_verdicts == expected_verdicts, (
        f"the gate fires at the wrong instants.\n  expected "
        f"{expected_verdicts}\n  actual   {actual_verdicts}\n\n"
        "It must be RED while the ET date is before "
        f"{rp.NOAA_PUBLICATION_DATE} and GREEN from ET midnight on that date "
        "onwards — including at 03:59 UTC, which is still the previous "
        "evening in Eastern Time and is the case the whole fix is for."
    )

    # THE CONTROL. The rejected implementation, run over the same table: the
    # runner's own date at these instants DOES depend on TZ. This is what the
    # gate used to read.
    local_dates = {}
    try:
        for zone_name in _RUNNER_TIMEZONES:
            os.environ["TZ"] = zone_name
            time.tzset()
            for iso_instant, _expected_et, _why in _ET_BOUNDARY_CASES:
                instant = _dt.datetime.fromisoformat(iso_instant)
                local_dates.setdefault(iso_instant, set()).add(
                    instant.astimezone().date()
                )
    finally:
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()

    assert any(len(dates) > 1 for dates in local_dates.values()), (
        "the runner's LOCAL date came out the same under every timezone in "
        f"{list(_RUNNER_TIMEZONES)}, which means TZ is not actually taking "
        "effect in this process and the comparison above proved nothing. "
        "Establish that before trusting this file: an inert control is worse "
        "than no control."
    )


def test_the_gate_reads_the_eastern_date_and_not_the_local_one():
    """THE HOLE IN THE TEST ABOVE, FOUND BY MUTATION AND CLOSED HERE.

    ``test_the_future_event_gate_is_the_same_on_every_machine`` exercises
    ``_eastern_date`` and ``_claims_an_unhappened_event``. It does NOT exercise
    the gate's CALL SITE -- so reverting one line,
    ``today = _eastern_date()`` back to ``today = _dt.date.today()``, leaves it
    green. Measured: with that revert in place the TZ test still passed. A
    helper nobody is required to call is not a fix.

    So this drives the gate itself, with the two clocks forced APART and in
    OPPOSITE directions, and reads which one it obeyed:

        eastern date  = the day AFTER publication  -> the note is honest
        local date    = the day BEFORE publication -> the note is premature

    A gate reading ET passes. A gate reading ``date.today()`` fails. Then the
    two are swapped and the expected outcomes swap with them, so neither
    result can be got by a gate that is simply always-green or always-red.

    NO REAL CLOCK IS CONSULTED, which is the point: a test of which clock is
    read cannot itself depend on what time it is.
    """
    import types

    module = sys.modules[__name__]
    published = _iso(rp.NOAA_PUBLICATION_DATE)
    day_before = published - _dt.timedelta(days=1)
    day_after = published + _dt.timedelta(days=1)

    def _local_clock_frozen_at(frozen):
        """A stand-in for this module's ``_dt`` whose ``date.today()`` lies.

        ``datetime.date`` is a C type and will not take a monkeypatched
        ``today``, so the module's handle on the datetime module is swapped
        instead. Everything except ``date.today`` is the real thing, and the
        subclass keeps ``_iso``'s ``_dt.date(y, m, d)`` and every comparison
        working unchanged.
        """
        class _FrozenDate(_dt.date):
            @classmethod
            def today(cls):
                return frozen

        shim = types.SimpleNamespace(
            date=_FrozenDate,
            datetime=_dt.datetime,
            timezone=_dt.timezone,
            timedelta=_dt.timedelta,
        )
        return shim

    gate = test_no_federal_event_is_stated_as_having_happened_before_it_has

    # Sanity: the note under test really does make the claims, otherwise both
    # halves below pass vacuously and this test checks nothing.
    assert _federal_events_stated_as_done(rp.round_provenance_note()), (
        "the rendered note makes NO 'has happened' claim, so this test "
        "cannot distinguish the two clocks: every outcome below would be "
        "green for the same uninteresting reason. The note is expected to "
        f"contain one of {list(_PRESENT_PERFECT_FEDERAL_CLAIMS)}."
    )

    real_eastern, real_dt = module._eastern_date, module._dt
    try:
        # ET says the event has happened; the local clock says it has not.
        module._eastern_date = lambda instant=None: day_after
        module._dt = _local_clock_frozen_at(day_before)
        gate()   # must NOT raise: a gate reading ET is satisfied

        # Now the other way round.
        module._eastern_date = lambda instant=None: day_before
        module._dt = _local_clock_frozen_at(day_after)
        with pytest.raises(AssertionError):
            gate()
    finally:
        module._eastern_date, module._dt = real_eastern, real_dt

    # The failure the first half would have produced, spelled out, because a
    # bare "must NOT raise" says nothing about WHY it did if it does.
    assert module._eastern_date is real_eastern
    assert module._dt is real_dt


def test_the_deadline_lookup_is_eastern_time_too():
    """``next_hard_deadline()`` answers a FEDERAL question; same rule (1.6.2 R2).

    Found by sweeping the module for the shape the gate above was fixed for.
    ``next_hard_deadline`` decided whether a deadline had passed with
    ``date.today()`` -- the caller's local date -- and the deadline it decides
    about is written into the note as **5:00 p.m. ET on November 10, 2026**.

    THE FAILURE IS A DAY EARLY, WHICH IS THE EXPENSIVE DIRECTION. At
    2026-11-11 04:59 UTC it is 23:59 EST on the 10th: the ET deadline has
    passed, but for the preceding five hours of that UTC day a CDE could still
    file and a caller east of ET was already being told the round was closed.
    ``test_the_horizon_lands_before_the_deadline_it_watches`` fails closed on
    ``None``, so it would have reported a CLOSED CY 2026 round up to a day
    early, on the one day anybody is looking.

    Two properties, neither of which depends on what day it is when this runs:
    the boundary is placed in ET, and the answer does not move with ``TZ``.
    """
    import time

    tokyo_side = _dt.datetime(2026, 11, 11, 4, 59, tzinfo=_dt.timezone.utc)
    assert _eastern_date(tokyo_side) == _dt.date(2026, 11, 10), (
        "2026-11-11 04:59 UTC is 23:59 EST on 10 Nov 2026 (November is EST, "
        "UTC-5). If this is not the 10th, the boundary arithmetic below is "
        "not testing what it claims to."
    )

    still_open = rp.next_hard_deadline(_eastern_date(tokyo_side))
    assert still_open is not None and still_open[0] == "2026-11-10", (
        f"at 23:59 ET on the deadline date next_hard_deadline() returned "
        f"{still_open!r}. The deadline is 5:00 p.m. ET on that date; the day "
        "itself must not be treated as already gone."
    )

    # THE REJECTED IMPLEMENTATION, at the same instant. This is the control:
    # without it the assertion above would pass against code that had never
    # been wrong.
    utc_local_date = tokyo_side.date()
    assert utc_local_date == _dt.date(2026, 11, 11)
    assert rp.next_hard_deadline(utc_local_date) is None, (
        "the local-date reading of this instant is expected to report every "
        "deadline passed — that is the defect being fixed. If it no longer "
        "does, this control has gone inert and proves nothing."
    )

    if not hasattr(time, "tzset"):                  # pragma: no cover
        pytest.skip("time.tzset() is POSIX-only; cannot vary TZ in-process")

    original_tz = os.environ.get("TZ")
    answers = {}
    try:
        for zone_name in _RUNNER_TIMEZONES:
            os.environ["TZ"] = zone_name
            time.tzset()
            answers[zone_name] = rp._eastern_today()
    finally:
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()

    assert len(set(answers.values())) == 1, (
        f"_eastern_today() moved with the runner's timezone: {answers}. It is "
        "supposed to be a fact about Eastern Time and about nothing else."
    )

    # AND THE DEFAULT PATH ACTUALLY CALLS IT. Everything above exercises
    # _eastern_today directly or passes `today=` explicitly, so reverting the
    # one line `today = _eastern_today()` back to `date.today()` left all of it
    # green -- measured, as mutation E of this round. A helper nobody is
    # required to call is not a fix, which is the same hole found in
    # test_the_future_event_gate_is_the_same_on_every_machine.
    #
    # So _eastern_today is replaced with a stub and the NO-ARGUMENT call is
    # required to have obeyed it. The two stub dates straddle the application
    # deadline, so a default still reading the real clock (2026, months before
    # it) cannot produce the second answer by accident.
    real_eastern_today = rp._eastern_today
    try:
        rp._eastern_today = lambda: _dt.date(2026, 11, 10)
        on_the_day = rp.next_hard_deadline()
        rp._eastern_today = lambda: _dt.date(2026, 11, 11)
        day_after = rp.next_hard_deadline()
    finally:
        rp._eastern_today = real_eastern_today

    assert on_the_day is not None and on_the_day[0] == "2026-11-10", (
        f"with the Eastern date stubbed to the deadline date itself, "
        f"next_hard_deadline() returned {on_the_day!r}."
    )
    assert day_after is None, (
        f"next_hard_deadline() returned {day_after!r} with the Eastern date "
        "stubbed to the day AFTER the last deadline, so it did not consult "
        "_eastern_today() at all -- it is reading some other clock. That is "
        "the defect this test exists for, and it is invisible to every "
        "assertion above."
    )


def test_the_application_hash_is_pinned_in_exactly_one_place():
    """ONE COPY of 64 hex characters.

    The hash was typed into two module docstrings, split across two source
    lines each. Nobody proofreads 64 hex characters, so a divergence would
    read as provenance while pointing at nothing -- and this package has
    already shipped three hand-typed copies of one sentence that agreed only
    by luck (``Q25_QEI_BASIS_CLAUSE``).
    """
    sha = rp.APPLICATION_SHA256
    assert len(sha) == 64 and re.fullmatch(r"[0-9a-f]{64}", sha), (
        f"APPLICATION_SHA256 is not 64 lowercase hex characters: {sha!r}"
    )

    # Search the package for the hash with any whitespace/newlines removed,
    # which is how the two docstring copies were written.
    offenders = []
    for dirpath, _dirs, names in os.walk(os.path.join(_REPO_ROOT, "nmtcapp")):
        for name in sorted(names):
            if not name.endswith(".py") or name == "_round_provenance.py":
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                squashed = re.sub(r"\s+", "", handle.read())
            if sha in squashed:
                offenders.append(os.path.relpath(path, _REPO_ROOT))

    assert not offenders, (
        f"the CY 2024-2025 Application hash is typed again in {offenders}. It "
        "lives in nmtcapp/renderers/_round_provenance.APPLICATION_SHA256 and "
        "must be READ from there, not retyped -- import it, or reference the "
        "constant by name in prose."
    )


def test_the_disclosure_states_both_directions():
    """The note must not read as a warning label.

    A disclosure scoped only around understatement produces a correct fact
    leading somewhere wrong: a CDE told the guidance is stale, and not told it
    is nonetheless the right thing to prepare against, prepares against
    nothing. That outcome is WORSE than the stale citation this replaces, so
    both halves are asserted rather than only the cautionary one.

    ONE RATIONALE IN HERE WENT FALSE, AND THE TEST KEPT ASSERTING IT (1.6.2).
    Through 1.6.1 the "August 31, 2026" entry below was justified as "the only
    CY 2026 date a CDE can miss TODAY". That stopped being true when the AMIS
    window closed on 31 Aug 2026. The date a CDE can miss today is the
    APPLICATION DEADLINE, 10 Nov 2026 -- and it was in no part of the note.

    AND THEN THE DATE ITSELF WENT FALSE (1.6.4). The AMIS window did not close
    on 31 Aug 2026. That was the pre-announcement's date; Table 1 of the NOAA
    says 22 Sep 2026, and this test asserted the literal "August 31, 2026"
    against a note that rendered the same literal from the same wrong
    constant. The dates below are now read from the constants -- this gate
    checks that they RENDER, and tests/test_noaa_table_1 checks that the
    constants match the Federal Register's own text.

    A test whose stated reasoning argues for something untrue is worse than a
    missing test: it is the next person's premise. Both the assertion and the
    reasoning are corrected here, together, because correcting only the
    assertion leaves the false sentence sitting in the file for the next
    reader to build on.
    """
    note = rp.round_provenance_note()

    for phrase, why in (
        ("Materials are NOT YET PUBLISHED",
         "must say the CY 2026 APPLICATION materials do not exist -- and must "
         "say it of the Application specifically, since the NOAA now does"),
        ("NOAA IS PUBLISHED",
         "must say the CY 2026 round has opened; a note that still reads as "
         "'nothing has happened yet' sends a CDE to the wrong conclusion in "
         "the other direction"),
        ("most recent PUBLISHED Application",
         "must say what the cited round IS, not only what it is not"),
        ("re-verified", "must tell the CDE what to do, not just what is wrong"),
        ("nothing here is unreliable",
         "must say the cited instrument is still the right basis -- this is "
         "the overstating-uncertainty half, and it is the one a "
         "caution-shaped rewrite drops first"),
        (rp.APPLICATION_DEADLINE_TEXT,
         "must carry the application deadline"),
        (rp.AMIS_CDE_CERTIFICATION_DEADLINE_TEXT,
         "must carry the AMIS certification deadline on BOTH sides of it: "
         "while it is ahead, because it is the route into this round; after, "
         "because a CDE that missed it needs to know it is out of this round "
         "rather than discovering it in November"),
        ("CANNOT APPLY",
         "must say plainly what missing both certification routes means. "
         "'May not be eligible' is a softening that costs a reader the "
         "decision"),
    ):
        assert phrase in note, (
            f"round_provenance_note() no longer contains {phrase!r}: it {why}."
        )

    assert "CY 2026" in note and rp.CITED_ROUND in note


def test_the_note_names_every_recheck_item():
    """The re-check list is what makes this actionable rather than ominous."""
    note = rp.round_provenance_note()
    missing = [item for item in rp.RECHECK_ITEMS if item not in note]
    assert not missing, (
        f"round_provenance_note() drops {missing} from the re-check list. A "
        "CDE cannot act on an item the note does not name."
    )


def test_the_round_state_is_pinned():
    """Pins the premise the rest of the package is written against.

    THE REWRITE OF ``test_upcoming_materials_are_still_unpublished`` (1.6.2).
    Not a deletion and not a rename for tidiness: the old name asserted
    something that is now FALSE. The CY 2026 materials are not "still
    unpublished" -- the NOAA published on 2026-09-15. Only the Application has
    not. A test whose name states a false fact is a claim in the suite, and it
    is read more often than its body.

    DELIBERATELY WEAK, AND LABELLED AS SUCH. This asserts the module agrees
    with itself. It is NOT evidence about the world; see the module header on
    why no offline test can be.

    ITS VALUE IS THAT IT BREAKS ON EITHER MOVE. One boolean over two facts is
    what let the false conjunction ship: there was no state the code could be
    in that said "one of these changed". There is now, and flipping either
    constant is a deliberate act that lands the author here with the specific
    work attached.
    """
    assert rp.UPCOMING_NOAA_PUBLISHED is True, (
        "UPCOMING_NOAA_PUBLISHED is False, so the CY 2026 NOAA has been "
        "un-published -- which does not happen -- or this constant was "
        "reverted.\n\n"
        f"The NOAA is Federal Register document {rp.NOAA_FR_DOCUMENT_NUMBER}, "
        f"publication date {rp.NOAA_PUBLICATION_DATE}. The allocation "
        f"authority ({rp.NOAA_ALLOCATION_AUTHORITY}), the application "
        f"deadline ({rp.APPLICATION_DEADLINE}) and the CDE certification rule "
        "all come from it, and the note states them."
    )
    assert rp.UPCOMING_APPLICATION_PUBLISHED is False, (
        "UPCOMING_APPLICATION_PUBLISHED is True, so the CY 2026 ALLOCATION "
        "APPLICATION has been published and this package still encodes "
        f"{rp.CITED_ROUND}.\n\n"
        "THIS IS THE FLIP THAT OBLIGES THE CITATION REWRITE. Work the list in "
        "_round_provenance.RECHECK_ITEMS against the new documents -- "
        "Question 25's ladder, Question 22's Non-Metropolitan bounds, "
        "Question 15's product-flexibility ladder, the Review Process "
        "thresholds -- then update the citations, APPLICATION_SHA256, "
        "APPLICATION_URL and this test together."
    )


# ---------------------------------------------------------------------------
# The network half -- a TOOL, not a gate
# ---------------------------------------------------------------------------

@pytest.mark.network
def test_live_cdfi_fund_check():
    """Ask cdfifund.gov the question no offline test can answer.

    Run it when the expiry fires::

        pytest -m network tests/test_round_provenance.py

    SKIPPED BY DEFAULT, and that is a real limitation rather than a
    configuration detail: a skipped test cannot fail in CI, so this is not a
    gate. Making CI depend on a federal website being reachable would produce
    red builds that say nothing about this repository, and a flaky gate is one
    people learn to ignore -- which is a worse outcome than an opt-in tool
    people run deliberately.

    THAT REASONING IS NOT WHAT FAILED IN 1.6.1 AND IS UNCHANGED. What failed
    was the SCHEDULE that sends someone here (see the module header). This
    test was the only one in the module that could ever have told the truth,
    and on 2026-09-14 it would have: it asserted the CY 2024-2025 timeline was
    still on the page and CY 2026 was not named, and the CY 2026 NOAA had
    published. It was RIGHT TO GO RED. That is the instrument working, and it
    is re-pointed here rather than quietly relaxed.

    RE-POINTED AT THE NEXT TRANSITION. The NOAA is behind us, so CY 2026 being
    named is now the EXPECTED state, not the alarm. The alarm is the
    ALLOCATION APPLICATION MATERIALS appearing -- that is the event that
    obliges the citation rewrite in ``RECHECK_ITEMS`` and the flip of
    ``UPCOMING_APPLICATION_PUBLISHED``.
    """
    import urllib.request

    request = urllib.request.Request(
        rp.PROGRAM_PAGE_URL, headers={"User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8", "replace")
    except Exception as exc:                      # pragma: no cover - network
        pytest.skip(f"cdfifund.gov unreachable ({exc}); no conclusion drawn")

    assert len(body) > 5_000, "program page returned too little to read"

    names_new_round = bool(re.search(r"CY\s*2026", body))

    # THE TRIGGER. Not "is CY 2026 mentioned" -- it is, the NOAA published --
    # but "is the INSTRUMENT THIS PACKAGE ENCODES available for CY 2026". An
    # Application PDF, an application-materials link, or the Q&A that ships
    # with them.
    application_materials = bool(
        re.search(r"CY[\s_-]*2026[^<]{0,120}Allocation Application", body, re.I)
        or re.search(r"2026[-_]\s*NMTC[_-]", body)
        or re.search(r"Allocation Application[^<]{0,40}"
                     r"(Materials|Q\s*&\s*A|Instructions)", body, re.I)
    )

    assert names_new_round, (
        "cdfifund.gov's NMTC program page does not name "
        f"{rp.UPCOMING_ROUND} at all.\n\n"
        f"The {rp.UPCOMING_ROUND} NOAA published on "
        f"{rp.NOAA_PUBLICATION_DATE} (Federal Register "
        f"{rp.NOAA_FR_DOCUMENT_NUMBER}), so by now the program page should. "
        "Two possibilities and they need different responses:\n"
        "  - the page lags the Federal Register, which is normal and is not a "
        "reason to change anything here; confirm against the NOAA itself at "
        f"{rp.NOAA_URL}\n"
        "  - the CY 2026 facts in _round_provenance are wrong, in which case "
        "the note is asserting a round that did not open."
    )

    assert not application_materials, (
        f"THE {rp.UPCOMING_ROUND} ALLOCATION APPLICATION MATERIALS HAVE "
        "APPEARED on cdfifund.gov.\n\n"
        "This is the transition this tool exists to catch, and it is the "
        "trigger for the next release of this package. Do, in order:\n\n"
        "  1. Retrieve the Application; record its SHA-256, byte count and "
        "page count.\n"
        "  2. Work every item in _round_provenance.RECHECK_ITEMS against it "
        "-- Question 25's ladder and area-type lists, Question 22's "
        "Non-Metropolitan bounds, Question 15's product-flexibility ladder, "
        "the Review Process thresholds, the award count.\n"
        "  3. Update APPLICATION_SHA256, APPLICATION_BYTES, APPLICATION_PAGES "
        "and APPLICATION_URL, set UPCOMING_APPLICATION_PUBLISHED = True, and "
        "update CITED_ROUND / CITED_ROUND_STATUS.\n"
        "  4. Rewrite the note: it currently tells a CDE the materials do not "
        "exist.\n\n"
        f"The application deadline is {rp.APPLICATION_DEADLINE_TEXT}. Whatever "
        "is left of that window is the time a CDE has to act on this."
    )
