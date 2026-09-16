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

  2. Every YEAR the note mentions is a round label, the NOAA's document
     number, or a date -- in any spelling the gate can parse -- that
     normalises to a Table 1 date, one of the note's own AS-OF dates
     (publication, filing, verification, generation) or the cited round's
     timeline. A spelling the gate cannot parse fails closed. A date typed
     into the prose that the table does not carry is exactly how August 31
     got in; as first written this direction read ``Month D, YYYY`` only,
     and ``31 Aug 2026`` walked past it (hostile audit, mutation MI).

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

  5. The prose MOVES across a deadline boundary, AND IN THE RIGHT DIRECTION.
     "The only deadline you can still miss" was a typed sentence through
     1.6.3, true on no day. If the rendered note is byte-identical on 21 Sep
     and 23 Sep 2026, paragraph 2 is still typed rather than computed,
     whatever the constants say. And "differs" alone is not enough: an
     inverted branch differs too.

  6. THE STATUS WORDS AND THE COUNT ARE BOUND TO THE PREDICATE, LIVE (1.6.4
     fix round, R1). As first written this module bound paragraph 4's LISTS
     to the table and nothing else: the hostile audit inverted paragraph 2's
     branch (MA), inverted paragraph 3's (MD), rendered "9 of the 10" above a
     list of ten (MB) and dropped the prior-Allocatee tag (MG), and 90 live
     tests stayed green every time -- only the rendered baselines saw it,
     and a baseline regenerates. Now, on every date the gate runs at:
     paragraph 2 says STILL AHEAD if and only if the certification row is
     ahead; paragraph 3's three-way status agrees with both of its rows;
     paragraph 4's "N of the M" equals the count of rows ahead; every row is
     named exactly once and tagged if and only if Table 1 addresses it to
     prior Allocatees. The predicate is computed here from the row's date;
     the wording is a fixture in this file. A gate that re-implemented the
     paragraph would share its blind spot, so it does not.

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
#: deadline in the note is written in.
_US_DATE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September"
    r"|October|November|December) \d{1,2}, \d{4}\b"
)
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

#: DIRECTION 1 SELECTS ON THE SUBJECT, NOT THE SPELLING (1.6.4 fix round, R5).
#: As first written the gate read ``Month D, YYYY`` only, and said so; the
#: hostile audit's mutation MI -- ``" Also due 31 Aug 2026."`` typed into
#: paragraph 4 -- passed 90 live tests. The subject of a typed date is the
#: YEAR it carries, and every year is one of exactly three things: a round
#: label (``CY 2026``), the Federal Register document number
#: (``2026-18883``), or a date. So every year token in the note is located,
#: each is required to sit inside one of those, and a date is required to
#: NORMALISE to a date the note is allowed to carry. A year in a spelling
#: this gate cannot parse is a failure, not a pass: the gate fails closed on
#: what it does not recognise rather than reading past it.
_MONTHS = {
    name: index for index, name in enumerate(rp._MONTH_NAMES, start=1)
}
_MONTHS.update({name[:3]: index for name, index in list(_MONTHS.items())})
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))
#: (label, pattern, normaliser). Each pattern names ``y``, ``m``, ``d``.
_DATE_SPELLINGS = (
    ("Month D, YYYY",
     re.compile(rf"\b(?P<m>{_MONTH_ALT})\.? (?P<d>\d{{1,2}}), (?P<y>\d{{4}})\b")),
    ("D Month YYYY",
     re.compile(rf"\b(?P<d>\d{{1,2}}) (?P<m>{_MONTH_ALT})\.? (?P<y>\d{{4}})\b")),
    ("YYYY-MM-DD",
     re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})\b")),
    ("M/D/YYYY",
     re.compile(r"\b(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{4})\b")),
)
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_ROUND_LABEL = re.compile(r"\bCY \d{4}(?:-\d{4})?\b")


def _normalise(match) -> str:
    month = match["m"]
    month = _MONTHS[month] if month in _MONTHS else int(month)
    return _dt.date(int(match["y"]), month, int(match["d"])).isoformat()


def _year_problems(note: str, allowed_iso: set) -> list:
    """Every year the note mentions, accounted for or reported.

    Returns one problem per year token that is not inside a known round
    label, the NOAA's document number, or a date that normalises to a member
    of ``allowed_iso``.
    """
    problems, covered = [], []

    def cover(span, ok, message):
        covered.append(span)
        if not ok:
            problems.append(message)

    for label, pattern in _DATE_SPELLINGS:
        for match in pattern.finditer(note):
            try:
                iso = _normalise(match)
            except (ValueError, KeyError):
                cover(match.span(), False,
                      f"the note renders {match.group(0)!r}, which looks like "
                      f"a {label} date and is not one")
                continue
            if label == "YYYY-MM-DD":
                cover(match.span(), False,
                      f"the note renders an ISO date {match.group(0)!r}; "
                      "dates reach the prose only through _us_date")
            else:
                cover(match.span(), iso in allowed_iso,
                      f"the note renders {match.group(0)!r} ({iso}), which is "
                      "not a Table 1 date, not one of the note's own as-of "
                      "dates and not the cited round's timeline. A typed "
                      "date.")
    for match in _ROUND_LABEL.finditer(note):
        cover(match.span(),
              match.group(0) in (rp.CITED_ROUND, rp.UPCOMING_ROUND),
              f"the note names a round {match.group(0)!r} that is neither "
              f"{rp.CITED_ROUND!r} nor {rp.UPCOMING_ROUND!r}")
    for match in re.finditer(re.escape(rp.NOAA_FR_DOCUMENT_NUMBER), note):
        cover(match.span(), True, "")
    for match in _YEAR.finditer(note):
        start, end = match.span()
        if not any(a <= start and end <= b for a, b in covered):
            context = note[max(0, start - 30):end + 20]
            problems.append(
                f"the note mentions the year {match.group(0)} in a form this "
                f"gate does not recognise as a date, a round label or the "
                f"document number: ...{context}..."
            )
    return problems

#: THE STATUS VOCABULARY OF PARAGRAPHS 2 AND 3, SPELLED HERE ON PURPOSE (1.6.4
#: fix round, R1). The gate binds these WORDS to the PREDICATE -- "is the row
#: still ahead of today?" -- computed here from the row's ISO date, not read
#: back from ``_is_ahead``. Reading the words from the module would let the
#: module change both sides at once; re-implementing the paragraph would share
#: its blind spot. So the gate holds the predicate and a fixture holds the
#: wording: a wording change reddens here and is a deliberate act, and an
#: inverted branch reddens here on the live date. Mutation MA of the hostile
#: audit -- ``if _is_ahead`` -> ``if not _is_ahead`` in
#: ``_certification_paragraph`` -- passed 90 live tests before this existed.
_CERT_AHEAD_WORDS = "the AMIS route is STILL AHEAD"
_CERT_CLOSED_WORDS = "the AMIS route has CLOSED"
#: Keyed on (Subsidiary CDE certification row ahead?, amendment row ahead?).
_PRIOR_STATUS_WORDS = {
    (True, True): "both of those dates are still ahead",
    (False, True): ("the Subsidiary CDE certification date has passed and the "
                    "amendment date is still ahead"),
    (False, False): "both of those dates have passed",
}
#: Paragraph 4's count sentence. Mutation MB -- ``len(ahead) - 1`` -- rendered
#: "9 of the 10 ... are still ahead" above a list of ten and passed every live
#: gate, because the lists were checked and the count never was.
_COUNT_SENTENCE = re.compile(
    r"\b(?P<ahead>\d+) of the (?P<total>\d+) deadlines in Table 1 "
    r"(?P<verb>is|are) still ahead\b"
)
#: The audience tag ``_row_item`` appends to a prior-Allocatee row.
_PRIOR_TAG = "[prior Allocatees]"

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
    extend the horizon. The shape ``(iso, text, what)`` is unchanged.

    ``next_hard_deadline`` IS NOT UNCHANGED, and this docstring said it was
    (1.6.4 fix round, R3). Through 1.6.3 the tuple held two rows and the
    function answered 10 Nov on every day from 1 Sep; with eight rows it
    answers 22 Sep, then 6 Oct, then 3 Nov, then 6 Nov -- a different answer
    on 52 of the 56 days from 16 Sep to 10 Nov 2026, measured. That
    divergence is the fix. What IS unchanged is the ``None`` case: the day
    after 10 Nov, both versions return ``None``, and that is what the last
    two assertions below hold.
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

    # Direction 1: nothing rendered that the table (or an as-of date, or the
    # cited round's own timeline) lacks -- selected by YEAR, in any spelling,
    # failing closed on a spelling the gate cannot read.
    allowed_iso = {row.iso for row in rp.NOAA_TABLE_1} | {
        rp.NOAA_PUBLICATION_DATE,
        rp.NOAA_FILED_DATE,
        rp.LAST_VERIFIED,
        today.isoformat(),
    } | set(rp.CITED_ROUND_TIMELINE.values())
    problems.extend(_year_problems(note, allowed_iso))

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

    # Direction 3: paragraph 2's status words agree with the predicate, as of
    # today. The ahead-wording appears when the certification row is ahead and
    # cannot appear when it is not, and the converse.
    when = rp._us_date(today.isoformat())
    cert_para = paragraphs[rp.CERTIFICATION_PARAGRAPH_INDEX]
    cert_ahead = _iso(rp.CDE_CERTIFICATION_ROW.iso) >= today
    expected, forbidden = (
        (_CERT_AHEAD_WORDS, _CERT_CLOSED_WORDS) if cert_ahead
        else (_CERT_CLOSED_WORDS, _CERT_AHEAD_WORDS)
    )
    if f"As of {when} {expected}" not in cert_para:
        problems.append(
            f"paragraph 2 does not say 'As of {when} {expected}', and the CDE "
            f"certification row ({rp.CDE_CERTIFICATION_ROW.iso}) "
            f"{'is' if cert_ahead else 'is not'} ahead of {today}"
        )
    if forbidden in cert_para:
        problems.append(
            f"paragraph 2 says {forbidden!r} while the CDE certification row "
            f"({rp.CDE_CERTIFICATION_ROW.iso}) "
            f"{'is' if cert_ahead else 'is not'} ahead of {today}"
        )

    # Direction 4: paragraph 3's status words agree with BOTH predicates.
    prior_para = paragraphs[rp.PRIOR_ALLOCATEE_PARAGRAPH_INDEX]
    sub_ahead = _iso(rp.SUBSIDIARY_CDE_CERTIFICATION_ROW.iso) >= today
    add_ahead = _iso(rp.ADD_SUBSIDIARY_CDES_ROW.iso) >= today
    if (sub_ahead, add_ahead) not in _PRIOR_STATUS_WORDS:
        problems.append(
            "Table 1 puts the amendment-request row before the Subsidiary CDE "
            "certification row; paragraph 3 has no wording for that state"
        )
    else:
        expected = _PRIOR_STATUS_WORDS[(sub_ahead, add_ahead)]
        if f"As of {when} {expected}" not in prior_para:
            problems.append(
                f"paragraph 3 does not say 'As of {when} {expected}' "
                f"(Subsidiary CDE certification ahead: {sub_ahead}; amendment "
                f"ahead: {add_ahead}; today {today})"
            )
        for words in _PRIOR_STATUS_WORDS.values():
            if words != expected and words in prior_para:
                problems.append(
                    f"paragraph 3 says {words!r} on {today}, when the state "
                    f"is (certification ahead: {sub_ahead}, amendment ahead: "
                    f"{add_ahead})"
                )

    # Direction 5: paragraph 4's COUNT equals the number of rows still ahead.
    ahead_rows = [row for row in rp.NOAA_TABLE_1 if _iso(row.iso) >= today]
    count = _COUNT_SENTENCE.search(deadlines_para)
    if ahead_rows and count is None:
        problems.append(
            f"paragraph 4 carries no 'N of the M deadlines in Table 1 are "
            f"still ahead' sentence on {today}, with {len(ahead_rows)} ahead"
        )
    elif count is not None:
        stated = (int(count["ahead"]), int(count["total"]))
        actual = (len(ahead_rows), len(rp.NOAA_TABLE_1))
        if stated != actual:
            problems.append(
                f"paragraph 4 says {stated[0]} of the {stated[1]} deadlines "
                f"are still ahead on {today}; Table 1 says {actual[0]} of "
                f"{actual[1]}"
            )
        verb = "is" if len(ahead_rows) == 1 else "are"
        if count["verb"] != verb:
            problems.append(
                f"paragraph 4 says '{count['ahead']} ... {count['verb']} still "
                f"ahead'; with {len(ahead_rows)} ahead the verb is {verb!r}"
            )

    # Direction 6: every row is named exactly once in paragraph 4 (a row in
    # both lists is a contradiction) and carries the prior-Allocatee tag if
    # and only if Table 1 addresses it to prior Allocatees. Mutation MG
    # dropped the tag and passed every live gate.
    for row in rp.NOAA_TABLE_1:
        seen = deadlines_para.count(row.description)
        if seen != 1:
            problems.append(
                f"Table 1 row {row.description!r} is named {seen} times in "
                f"paragraph 4 on {today}; it must be named exactly once"
            )
            continue
        tail = deadlines_para[
            deadlines_para.index(row.description) + len(row.description):]
        cut = min(pos for pos in (tail.find("; "), tail.find("Already passed"),
                                  len(tail)) if pos >= 0)
        item = tail[:cut]
        to_prior = row.audience == rp.AUDIENCE_PRIOR_ALLOCATEE
        if (_PRIOR_TAG in item) != to_prior:
            problems.append(
                f"Table 1 row {row.description!r} is addressed to "
                f"{row.audience!r} and its item "
                f"{'lacks' if to_prior else 'carries'} the {_PRIOR_TAG!r} tag"
            )

    # Fail closed. AND THE SEAM THIS LEAVES, DUE BEFORE 2026-11-11 (hostile
    # audit F5, carried): from 11 Nov 2026 to 14 Jan 2027 paragraph 4 will
    # say "2 of the 10 deadlines in Table 1 are still ahead" -- the two
    # January prior-Allocatee rows -- while next_hard_deadline() is None and
    # this line reports a closed round. Both are true on those days and they
    # do not agree on what the reader should do. Not wrong today; the note
    # must be rewritten for that window before it arrives, and this gate is
    # what will say so on the morning of the 11th.
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


@pytest.mark.parametrize("typed", [
    " Also due 31 Aug 2026.",          # mutation MI of the hostile audit
    " Also due 31 August 2026.",
    " Also due Aug 31, 2026.",
    " Also due 8/31/2026.",
    " Also due 2026-08-31.",
    " Also due August 31st, 2026.",    # a spelling the gate does NOT parse
    " Also due in 2026.",              # a bare year, likewise
])
def test_a_typed_date_in_any_spelling_is_caught(monkeypatch, typed):
    """Direction 1, shown to fire on the SUBJECT: five spellings of the
    1.6.3 date normalise and are refused; two the gate cannot parse are
    refused for that reason. Mutation MI passed 90 live tests when the gate
    read ``Month D, YYYY`` only."""
    _with_paragraph_edited(monkeypatch, rp.DEADLINES_PARAGRAPH_INDEX,
                           lambda p: p + typed)
    problems = _note_problems(_iso("2026-09-16"))
    assert any(
        "2026-08-31" in p or "does not recognise" in p or "ISO date" in p
        for p in problems
    ), problems


def _with_paragraph_edited(monkeypatch, index, edit):
    """Patch ``round_provenance_paragraphs`` so paragraph ``index`` is passed
    through ``edit`` -- the text-level form of a renderer mutation, so each
    direction of ``_note_problems`` is seen to fire inside the suite."""
    real = rp.round_provenance_paragraphs

    def edited(today=None):
        paras = list(real(today=today))
        paras[index] = edit(paras[index])
        return tuple(paras)

    monkeypatch.setattr(rp, "round_provenance_paragraphs", edited)


def test_an_inverted_certification_status_is_caught(monkeypatch):
    """Direction 3, shown to fire: mutation MA at the text level. On 16 Sep
    the AMIS route is ahead; a paragraph saying CLOSED must be red."""
    _with_paragraph_edited(
        monkeypatch, rp.CERTIFICATION_PARAGRAPH_INDEX,
        lambda p: p.replace(_CERT_AHEAD_WORDS, _CERT_CLOSED_WORDS))
    problems = _note_problems(_iso("2026-09-16"))
    assert any("paragraph 2" in p and "CLOSED" in p for p in problems), problems
    # And the other way on the other side: on 23 Sep it has closed.
    _with_paragraph_edited(
        monkeypatch, rp.CERTIFICATION_PARAGRAPH_INDEX,
        lambda p: p.replace(_CERT_CLOSED_WORDS, _CERT_AHEAD_WORDS))
    problems = _note_problems(_iso("2026-09-23"))
    assert any("paragraph 2" in p and "STILL AHEAD" in p for p in problems), problems


def test_an_inverted_prior_allocatee_status_is_caught(monkeypatch):
    """Direction 4, shown to fire: mutation MD at the text level."""
    both_ahead = _PRIOR_STATUS_WORDS[(True, True)]
    one_passed = _PRIOR_STATUS_WORDS[(False, True)]
    _with_paragraph_edited(
        monkeypatch, rp.PRIOR_ALLOCATEE_PARAGRAPH_INDEX,
        lambda p: p.replace(both_ahead, one_passed))
    problems = _note_problems(_iso("2026-09-16"))
    assert any("paragraph 3" in p for p in problems), problems


def test_a_wrong_count_is_caught(monkeypatch):
    """Direction 5, shown to fire: mutation MB at the text level -- the
    count one short above a list that is not."""
    def one_short(p):
        match = _COUNT_SENTENCE.search(p)
        assert match, p
        return p.replace(match.group(0),
                         match.group(0).replace(match["ahead"],
                                                str(int(match["ahead"]) - 1), 1), 1)

    _with_paragraph_edited(monkeypatch, rp.DEADLINES_PARAGRAPH_INDEX, one_short)
    problems = _note_problems(_iso("2026-09-16"))
    assert any("paragraph 4 says" in p and "Table 1 says 10 of 10" in p
               for p in problems), problems


def test_a_missing_audience_tag_is_caught(monkeypatch):
    """Direction 6, shown to fire: mutation MG at the text level."""
    _with_paragraph_edited(
        monkeypatch, rp.DEADLINES_PARAGRAPH_INDEX,
        lambda p: p.replace(" " + _PRIOR_TAG, ""))
    problems = _note_problems(_iso("2026-09-16"))
    tagged = [p for p in problems if "lacks" in p and _PRIOR_TAG in p]
    assert len(tagged) == sum(
        1 for row in rp.NOAA_TABLE_1
        if row.audience == rp.AUDIENCE_PRIOR_ALLOCATEE), problems


def test_a_row_named_in_both_lists_is_caught(monkeypatch):
    """Direction 6, the other half: a row that appears as still ahead AND as
    already passed is a contradiction, not two facts."""
    row = rp.APPLICATION_REGISTRATION_ROW
    _with_paragraph_edited(
        monkeypatch, rp.DEADLINES_PARAGRAPH_INDEX,
        lambda p: p.replace("Already passed: none.",
                            f"Already passed: {rp._row_item(row)}."))
    problems = _note_problems(_iso("2026-09-16"))
    assert any("named 2 times" in p for p in problems), problems


# ---------------------------------------------------------------------------
# 4. The prose is COMPUTED, not typed
# ---------------------------------------------------------------------------

def test_the_note_moves_across_the_certification_deadline():
    """21 Sep and 23 Sep 2026 must render differently, in paragraph 2, AND
    IN THE RIGHT DIRECTION: ahead before, closed after.

    If they do not differ, the certification paragraph is a typed sentence
    that is true on one side of 22 Sep and false on the other -- which is
    1.6.3's defect with the date corrected. And "they differ" alone was not
    enough: an INVERTED branch differs too, and the hostile audit's mutation
    MA (``if _is_ahead`` -> ``if not _is_ahead``) rendered "the AMIS route
    has CLOSED" on 16 Sep and passed this test as first written.
    """
    before = rp.round_provenance_paragraphs(today=_iso("2026-09-21"))
    after = rp.round_provenance_paragraphs(today=_iso("2026-09-23"))
    assert before != after
    cert = rp.CERTIFICATION_PARAGRAPH_INDEX
    assert _CERT_AHEAD_WORDS in before[cert] and \
        _CERT_CLOSED_WORDS not in before[cert], (
        "on 21 Sep 2026, the day before the certification deadline, "
        f"paragraph 2 must say {_CERT_AHEAD_WORDS!r} and not "
        f"{_CERT_CLOSED_WORDS!r}:\n{before[cert]}"
    )
    assert _CERT_CLOSED_WORDS in after[cert] and \
        _CERT_AHEAD_WORDS not in after[cert], (
        "on 23 Sep 2026, the day after the certification deadline, "
        f"paragraph 2 must say {_CERT_CLOSED_WORDS!r} and not "
        f"{_CERT_AHEAD_WORDS!r}:\n{after[cert]}"
    )
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
