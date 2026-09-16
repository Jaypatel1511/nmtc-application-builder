"""THE NOAA'S TABLE 1 IS CARRIED, AND THE NOTE IS COMPUTED AGAINST IT (1.6.4).

THE DEFECT

Through 1.6.3 ``renderers/_round_provenance`` carried the CY 2026 CDE
certification deadline as **2026-08-31** and rendered, in capitals, in all
four formats, that an organization not certified by then CANNOT APPLY IN CY
2026. The NOAA -- Federal Register document 2026-18883, the document the
package already cited by number -- sets that deadline at **2026-09-22** in
Table 1. The package told an eligible CDE it was excluded, six days before the
window it described as shut actually shut.

The wrong date came from the CDFI Fund's 12 Aug 2026 PRE-ANNOUNCEMENT
(cdfifund.gov/news/738), which said August 31. The NOAA superseded it on
15 Sep 2026. The 1.6.2 and 1.6.3 cycles opened the NOAA three times and each
time read exactly the field they went in for -- that it exists, that it is $5
billion, that applications close 10 Nov. Nobody re-read Table 1.

WHAT THIS MODULE ASSERTS, AND WHY EACH HALF IS NEEDED

  1. ``NOAA_TABLE_1`` matches the instrument. ``tests/noaa_2026_18883_table_1
     .txt`` is lines 33-69 of the Federal Register's raw-text endpoint, byte
     for byte, with the retrieval URL and SHA-256 in its header. This module
     PARSES that excerpt and compares it row by row to the constant. The
     package's copy of the table is checked against the table, not against
     itself; a constant that agrees with a prose sentence derived from that
     same constant is a gate that cannot fail, and this package has shipped
     that shape before (``Q25_QEI_BASIS_CLAUSE``, three copies agreeing by
     luck).

  2. Every date the note renders is in Table 1 or is one of the note's own
     AS-OF dates (publication, filing, verification, generation). A date
     typed into the prose that the table does not carry is exactly how
     August 31 got in.

  3. Every Table 1 row still ahead of "today" is named in the note, with its
     time and its date, in the part of the note that says it is still ahead.
     THIS IS THE DIRECTION THE 1.6.3 SUITE WAS BLIND TO. That suite asserted
     that everything in ``HARD_EXTERNAL_DEADLINES`` reached the note, and
     the tuple held two of Table 1's ten rows, so October 6 (Application
     Registration -- miss it and AMIS will not accept the application at all)
     was not in the note and nothing could say so.

  4. FAILS CLOSED. When no filing deadline is still ahead, the note describes
     a closed round and needs rewriting. ``next_hard_deadline`` already fails
     closed on ``None``; the gate here must too, or a note whose every date is
     behind it passes quietly with an empty "still ahead" list.

  5. The prose MOVES across a deadline boundary. "The only deadline you can
     still miss" was a typed sentence through 1.6.3, true on no day. If the
     rendered note is byte-identical on 21 Sep and 23 Sep 2026, paragraph 2
     is still typed rather than computed, whatever the constants say.

THE GATE IS A PURE FUNCTION OF ``today`` so it can be run at frozen dates.
``test_the_note_agrees_with_table_1_today`` is the live gate;
``test_the_gate_fails_closed_after_the_last_filing_deadline`` is the control
that shows the same function go red. A gate never seen to fail is not
evidence.
"""
from __future__ import annotations

import datetime as _dt
import os
import re

import pytest

from nmtcapp.renderers import _round_provenance as rp

_HERE = os.path.dirname(os.path.abspath(__file__))
_FR_EXCERPT = os.path.join(_HERE, "noaa_2026_18883_table_1.txt")

#: ``Month D, YYYY`` -- the ONE form ``_us_date`` renders and the form every
#: deadline in the note is written in. The gate reads this form. It does not
#: read ``19 Nov 2024`` (paragraph 0's CY 2024-2025 timeline, a closed round's
#: history) and says so rather than implying a wider reach.
_US_DATE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September"
    r"|October|November|December) \d{1,2}, \d{4}\b"
)
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

#: One Table 1 row as the GPO typesets it: description, then the date with dot
#: leaders, then the time with dot leaders, then the method. Continuation lines
#: of the description are indented by one space and carry nothing else.
_FR_ROW = re.compile(
    r"^(?P<desc>\S[^\n]*?)\s{2,}"
    r"(?P<date>[A-Z][a-z]+ \d{1,2}, \d{4})\.+\s+"
    r"(?P<time>\d{1,2}:\d{2} [ap]\.m\. ET)\.+\s+"
    r"(?P<method>[^\n]+?)\.?\s*$"
)


def _iso(text: str) -> _dt.date:
    return _dt.date(*(int(p) for p in text.split("-")))


def _parse_fr_table_1() -> list:
    """The rows of Table 1 as the Federal Register prints them.

    Returns ``[(description, "Month D, YYYY", "H:MM x.m. ET", method)]`` with
    each description's hanging-indent continuation lines joined and its
    trailing full stop dropped. Fails closed on an excerpt that yields nothing.
    """
    with open(_FR_EXCERPT, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if not ln.startswith("#")]

    rows = []
    for line in lines:
        match = _FR_ROW.match(line)
        if match:
            rows.append([match["desc"].strip(), match["date"], match["time"],
                         match["method"].strip()])
            continue
        if rows and line.startswith(" ") and line.strip() \
                and not line.strip().startswith("-"):
            rows[-1][0] = rows[-1][0] + " " + line.strip()

    parsed = [(desc.rstrip("."), date, time, method) for desc, date, time, method in rows]
    assert len(parsed) >= 5, (
        f"parsed only {len(parsed)} row(s) out of {_FR_EXCERPT}. The excerpt "
        "is the GPO's fixed-width table; if its layout changed, fix the parser "
        "-- do not let this pass on an empty table."
    )
    return parsed


# ---------------------------------------------------------------------------
# 1. The constant matches the instrument
# ---------------------------------------------------------------------------

def test_table_1_is_carried_verbatim_from_the_federal_register():
    """Row for row, in order: description, date, time, submission method.

    THE DATE IS THE ROW THIS GATE EXISTS FOR, but all four fields are compared
    because a description that drifts from the instrument's is a citation
    that no longer points at what it claims to.
    """
    expected = _parse_fr_table_1()
    carried = [
        (row.description, rp._us_date(row.iso), row.time_text,
         row.submission_method)
        for row in rp.NOAA_TABLE_1
    ]
    assert carried == expected, (
        "NOAA_TABLE_1 does not match Table 1 of Federal Register document "
        f"{rp.NOAA_FR_DOCUMENT_NUMBER} as carried in "
        f"{os.path.basename(_FR_EXCERPT)}.\n\n"
        "  carried by the package:\n    " + "\n    ".join(map(str, carried))
        + "\n  printed by the Federal Register:\n    "
        + "\n    ".join(map(str, expected))
        + "\n\nThe Federal Register is right. Fix the constant, not the "
        "fixture -- unless the NOAA was amended, in which case re-retrieve "
        "the document and replace the excerpt, its SHA-256 and its line range "
        "together."
    )


def test_table_1_dates_are_iso_and_ascending():
    """Table 1 is printed in date order and the constant must be too.

    ``next_hard_deadline`` takes a ``min``, so order is not load-bearing for
    it -- but the prose lists the rows in table order, and a reader expects
    the instrument's order.
    """
    isos = [row.iso for row in rp.NOAA_TABLE_1]
    for iso in isos:
        assert _ISO_DATE.fullmatch(iso), f"{iso!r} is not an ISO date"
        _iso(iso)
    assert isos == sorted(isos), f"NOAA_TABLE_1 is not in date order: {isos}"


def test_every_row_names_an_audience_the_module_defines():
    audiences = {row.audience for row in rp.NOAA_TABLE_1}
    assert audiences <= {rp.AUDIENCE_APPLICANT, rp.AUDIENCE_PRIOR_ALLOCATEE}, (
        f"unknown audience value(s) {audiences - {rp.AUDIENCE_APPLICANT, rp.AUDIENCE_PRIOR_ALLOCATEE}}"
    )
    assert rp.AUDIENCE_APPLICANT in audiences
    assert rp.AUDIENCE_PRIOR_ALLOCATEE in audiences, (
        "no Table 1 row is addressed to prior Allocatees. Section III.A.6(a) "
        "of the NOAA makes the two January 2027 rows ELIGIBILITY conditions on "
        "a CY 2026 applicant that is a prior Allocatee; they are not post-award "
        "obligations and the note must not present them as nobody's."
    )


# ---------------------------------------------------------------------------
# 2. The deadline constants are DERIVED from the table
# ---------------------------------------------------------------------------

def test_the_two_named_deadlines_are_rows_of_the_table():
    """``AMIS_CDE_CERTIFICATION_DEADLINE`` and ``APPLICATION_DEADLINE`` are
    lookups into ``NOAA_TABLE_1``, not second copies of a date."""
    by_desc = {row.description: row for row in rp.NOAA_TABLE_1}
    cert = by_desc[rp.CDE_CERTIFICATION_ROW.description]
    app = by_desc[rp.APPLICATION_DEADLINE_ROW.description]
    assert rp.AMIS_CDE_CERTIFICATION_DEADLINE == cert.iso
    assert rp.APPLICATION_DEADLINE == app.iso
    assert rp.AMIS_CDE_CERTIFICATION_DEADLINE_TEXT == rp.deadline_text(cert)
    assert rp.APPLICATION_DEADLINE_TEXT == rp.deadline_text(app)
    assert "Certification Application" in cert.description
    assert "Allocation Application deadline" in app.description


def test_hard_external_deadlines_is_the_filing_window_of_table_1():
    """Derived by filtering: every row on or before the application deadline.

    THE EXISTING SEMANTICS SURVIVE. ``HARD_EXTERNAL_DEADLINES`` holds the
    deadlines a CDE can still miss BY FAILING TO ACT BEFORE IT FILES, and
    ``next_hard_deadline`` schedules the re-check against it. The two January
    2027 rows are deadlines a prior Allocatee can miss, but not by anything it
    does in this package: after 10 Nov nothing here can help, so they do not
    extend the horizon. The shape ``(iso, text, what)`` is unchanged so
    ``next_hard_deadline`` is unchanged.
    """
    expected = tuple(
        (row.iso, rp.deadline_text(row), row.description)
        for row in rp.NOAA_TABLE_1
        if _iso(row.iso) <= _iso(rp.APPLICATION_DEADLINE)
    )
    assert rp.HARD_EXTERNAL_DEADLINES == expected
    assert len(rp.HARD_EXTERNAL_DEADLINES) >= 8, (
        "Table 1 carries eight rows on or before the application deadline; "
        f"the filter produced {len(rp.HARD_EXTERNAL_DEADLINES)}"
    )
    # And the derivation is what next_hard_deadline reads: after the last
    # filing deadline it is None, exactly as before.
    assert rp.next_hard_deadline(_iso(rp.APPLICATION_DEADLINE)) is not None
    assert rp.next_hard_deadline(
        _iso(rp.APPLICATION_DEADLINE) + _dt.timedelta(days=1)) is None


# ---------------------------------------------------------------------------
# 3. The gate: the note against the table, both directions, fail closed
# ---------------------------------------------------------------------------

def _still_ahead_section(paragraph: str) -> str:
    """The part of the deadlines paragraph that lists what is still ahead.

    The paragraph is written ``... still ahead ... <rows> ... Already passed
    ... <rows>``; a row named only after the ``Already passed`` marker is not
    being presented as something the reader can still act on.
    """
    marker = "Already passed"
    return paragraph.split(marker, 1)[0]


def _note_problems(today: _dt.date) -> list:
    """Every way the note disagrees with Table 1 on ``today``. Empty is green."""
    problems = []
    paragraphs = rp.round_provenance_paragraphs(today=today)
    note = " ".join(paragraphs)

    # Direction 1: nothing rendered that the table (or an as-of date) lacks.
    allowed = {rp._us_date(row.iso) for row in rp.NOAA_TABLE_1} | {
        rp._us_date(rp.NOAA_PUBLICATION_DATE),
        rp._us_date(rp.NOAA_FILED_DATE),
        rp._us_date(rp.LAST_VERIFIED),
        rp._us_date(today.isoformat()),
    }
    for found in _US_DATE.findall(note):
        if found not in allowed:
            problems.append(
                f"the note renders {found!r}, which is not a Table 1 date and "
                "not one of the note's own as-of dates. A typed date."
            )
    for found in _ISO_DATE.findall(note):
        problems.append(
            f"the note renders an ISO date {found!r}; dates reach the prose "
            "only through _us_date"
        )

    # Direction 2: everything still ahead is named as still ahead, with its
    # time and its date; nothing passed is named there.
    deadlines_para = paragraphs[rp.DEADLINES_PARAGRAPH_INDEX]
    ahead_text = _still_ahead_section(deadlines_para)
    for row in rp.NOAA_TABLE_1:
        text = rp.deadline_text(row)
        if _iso(row.iso) >= today:
            if row.description not in ahead_text or text not in ahead_text:
                problems.append(
                    f"Table 1 row {row.description!r} ({text}) is still ahead "
                    f"on {today} and the note does not name it as still ahead"
                )
        elif row.description in ahead_text:
            problems.append(
                f"Table 1 row {row.description!r} ({text}) passed before "
                f"{today} and the note still lists it as ahead"
            )

    # Fail closed.
    if rp.next_hard_deadline(today) is None:
        problems.append(
            f"every filing deadline in Table 1 is behind {today}: the note "
            "describes a CLOSED round and must be rewritten, not rendered"
        )
    return problems


def test_the_note_agrees_with_table_1_today():
    """THE LIVE GATE, on the Eastern date, both directions, fail closed."""
    today = rp._eastern_today()
    problems = _note_problems(today)
    assert not problems, (
        f"on {today} (Eastern) the round-provenance note disagrees with "
        f"Table 1 of the NOAA:\n  " + "\n  ".join(problems)
    )


@pytest.mark.parametrize("iso", [
    "2026-09-16",   # the day 1.6.4 was built: all ten rows ahead
    "2026-09-22",   # the certification deadline day itself: still ahead
    "2026-09-23",   # three rows passed, seven ahead
    "2026-10-07",   # registration passed
    "2026-11-10",   # the application deadline day itself
])
def test_the_note_agrees_with_table_1_on_every_side_of_every_boundary(iso):
    problems = _note_problems(_iso(iso))
    assert not problems, f"on {iso}:\n  " + "\n  ".join(problems)


def test_the_gate_fails_closed_after_the_last_filing_deadline():
    """THE CONTROL. The same function, one day past 10 Nov 2026, goes red.

    The two January 2027 rows are still ahead on that day, so a gate that
    only checked "is everything ahead named?" would pass with two rows named
    and the application deadline behind it. That is the quiet pass this
    exists to refuse.
    """
    day_after = _iso(rp.APPLICATION_DEADLINE) + _dt.timedelta(days=1)
    problems = _note_problems(day_after)
    assert any("CLOSED round" in p for p in problems), (
        f"on {day_after} the gate reported {problems!r} and did not fail "
        "closed. next_hard_deadline() is None on that date; the note "
        "describes a closed round and the gate must say so."
    )


def test_a_typed_date_that_is_not_in_the_table_is_caught(monkeypatch):
    """Direction 1, shown to fire: hand a foreign date to the prose."""
    real = rp.round_provenance_paragraphs

    def with_a_typed_date(today=None):
        paras = list(real(today=today))
        paras[rp.DEADLINES_PARAGRAPH_INDEX] += " Also due August 31, 2026."
        return tuple(paras)

    monkeypatch.setattr(rp, "round_provenance_paragraphs", with_a_typed_date)
    problems = _note_problems(_iso("2026-09-16"))
    assert any("August 31, 2026" in p and "typed" in p for p in problems), problems


# ---------------------------------------------------------------------------
# 4. The prose is COMPUTED, not typed
# ---------------------------------------------------------------------------

def test_the_note_moves_across_the_certification_deadline():
    """21 Sep and 23 Sep 2026 must render differently, and in paragraph 2.

    If they do not, the certification paragraph is a typed sentence that is
    true on one side of 22 Sep and false on the other -- which is 1.6.3's
    defect with the date corrected.
    """
    before = rp.round_provenance_paragraphs(today=_iso("2026-09-21"))
    after = rp.round_provenance_paragraphs(today=_iso("2026-09-23"))
    assert before != after
    cert = rp.CERTIFICATION_PARAGRAPH_INDEX
    # THE GENERATION DATE IS MASKED FIRST. The note stamps "As of <today>"
    # into the paragraph, so the two renders differ by that stamp alone even
    # when nothing else moved -- measured as mutation M5 of 1.6.4: with
    # _is_ahead forced to True, the unmasked comparison stayed green. The
    # question is whether the STATUS moved, not whether the date did.
    masked_before = before[cert].replace(rp._us_date("2026-09-21"), "<TODAY>")
    masked_after = after[cert].replace(rp._us_date("2026-09-23"), "<TODAY>")
    assert masked_before != masked_after, (
        "paragraph 2 is identical either side of the certification deadline "
        "once the generation date is masked; its status is still typed"
    )
    cert_text = rp.AMIS_CDE_CERTIFICATION_DEADLINE_TEXT
    assert cert_text in before[cert] and cert_text in after[cert], (
        "the certification deadline must be stated on both sides of it -- a "
        "CDE that missed it needs to know it is out of this round"
    )
    assert "CANNOT APPLY" in before[cert] and "CANNOT APPLY" in after[cert]


def test_each_row_is_ahead_on_its_day_and_passed_the_day_after():
    """Day-level semantics, the same as ``next_hard_deadline``: the deadline
    day itself is still ahead; the day after, it has passed."""
    for row in rp.NOAA_TABLE_1:
        on_the_day = _iso(row.iso)
        day_after = on_the_day + _dt.timedelta(days=1)
        if rp.next_hard_deadline(day_after) is None:
            continue    # the closed-round branch; covered by the control above
        ahead = _still_ahead_section(
            rp.round_provenance_paragraphs(today=on_the_day)[rp.DEADLINES_PARAGRAPH_INDEX])
        gone = _still_ahead_section(
            rp.round_provenance_paragraphs(today=day_after)[rp.DEADLINES_PARAGRAPH_INDEX])
        assert row.description in ahead, (row.description, on_the_day)
        assert row.description not in gone, (row.description, day_after)


def test_the_default_today_is_the_eastern_date():
    """``round_provenance_paragraphs()`` with no argument must consult
    ``_eastern_today()``. Mutation E of 1.6.2: a helper nobody is required
    to call is not a fix."""
    real = rp._eastern_today
    try:
        rp._eastern_today = lambda: _iso("2026-09-21")
        before = rp.round_provenance_paragraphs()
        rp._eastern_today = lambda: _iso("2026-09-23")
        after = rp.round_provenance_paragraphs()
    finally:
        rp._eastern_today = real
    masked = [
        " ".join(paras).replace(rp._us_date(iso), "<TODAY>")
        for paras, iso in ((before, "2026-09-21"), (after, "2026-09-23"))
    ]
    assert masked[0] != masked[1], (
        "round_provenance_paragraphs() rendered identically (generation date "
        "masked) with _eastern_today() stubbed to either side of the "
        "certification deadline, so the default path is reading some other "
        "clock -- or the status is typed"
    )


def test_the_note_and_its_paragraphs_take_the_same_today():
    today = _iso("2026-10-01")
    assert rp.round_provenance_note(today=today) == " ".join(
        rp.round_provenance_paragraphs(today=today))
