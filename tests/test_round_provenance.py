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

import pytest

from nmtcapp.renderers import _round_provenance as rp

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _iso(value: str) -> _dt.date:
    return _dt.date(*(int(part) for part in value.split("-")))


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
    ("November 10, 2026",
     "the application deadline — the only CY 2026 date a CDE can still miss"),
    ("August 31, 2026", "the AMIS CDE certification deadline, now closed"),
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
        ("November 10, 2026",
         "must carry the application deadline, which is the only CY 2026 date "
         "a CDE can still miss"),
        ("August 31, 2026",
         "must carry the AMIS certification deadline -- NOT because it can "
         "still be met, it cannot, but because a CDE that missed it needs to "
         "know it is out of this round rather than discovering it in November"),
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
