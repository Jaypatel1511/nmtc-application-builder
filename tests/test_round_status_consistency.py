"""ROUND-STATUS CLAIMS MUST AGREE WITH ``_round_provenance``'S CONSTANTS.

THE DEFECT THIS EXISTS FOR (1.6.2 → 1.6.3)

1.6.2 was the release that corrected this package's round provenance. It
rewrote ``renderers/_round_provenance`` to say, in prose and in two new
constants, that the CY 2026 NOAA **is published** (Federal Register document
2026-18883, publication date 15 Sep 2026) while the CY 2026 Allocation
Application **is not**.

It left the opposite sentence live in a DIFFERENT module. The last sentence of
``renderers/_question_25.Q25_BASIS_TEXT`` still read::

    (The CY 2026 NOAA is not yet published.)

and that sentence reaches the reader FIRST in every one of the four formats,
measured against the published 1.6.2 wheel:

    format    the stale sentence          its own correction
    PDF       page 8 of 27                page 26 of 27
    Excel     'Q25 Basis Note'!A9         'Round Provenance'!A4
    Word      table 7 of 17, row 8        paragraph 149 of 149
    Markdown  line 130 of 445             line 443 of 445

Eighteen pages, three sheets or 313 lines of a CDE reading, in that order,
"there is no CY 2026 round open yet" and then, much later, "the round is open
and closes in 56 days". And ``'Round Provenance'!A2`` claimed jurisdiction over
exactly the sheet that contradicted it: "This applies to every round-specific
citation in this workbook, including the 'Q25 Basis Note' sheet."

Every gate in the suite was green. ``tests/test_round_provenance.py`` reads the
note ``_round_provenance`` renders and nothing else, so a round-status sentence
in another module was outside every scanner in the package. That is the
enumeration failure this portfolio keeps reproducing: a fact with COPIES, one
copy updated, the others left behind and nothing looking.

WHAT THIS MODULE BINDS

``UPCOMING_NOAA_PUBLISHED`` and ``UPCOMING_APPLICATION_PUBLISHED`` are a fact
with copies. Every sentence anywhere in the RENDERED OUTPUT or in the PACKAGE
SOURCE that carries both a publication-status word and a round word is pulled
out of the corpus, and has to be classified in ``ROUND_STATUS_CLAIMS`` below —
by its exact text, not by matching an approved spelling — and then has to agree
with the constant it is about.

NOTE WHAT THE CONSTANTS ARE. They are assertions somebody typed with a date on
them, not measurements, and NO branch of ``round_provenance_paragraphs()``
reads either one: the note states the round's status in plain prose. So this
gate proves the package AGREES WITH ITSELF. It cannot prove the package is
right about the world. That is a different gate and it already exists:
``tests/test_round_provenance.test_the_round_claim_has_not_expired`` makes the
claim EXPIRE (``RECHECK_AFTER``, currently 2026-10-05), which is the honest
failure — staleness of the LOOKING, not of the fact.

THE TWO STAGES

STAGE 1, COMPLETENESS, is the stage that catches the NEXT one. A selected
segment that is not a key of ``ROUND_STATUS_CLAIMS`` FAILS, quoting itself and
asking to be classified. An unclassified sentence is the whole defect: 1.6.2's
author did not decide wrongly about ``_question_25``, they never saw it.

    THIS IS DELIBERATELY NOT A LIST OF APPROVED SPELLINGS. "Anything matching
    one of these patterns passes" is the gate shape this portfolio has shipped
    eight times, most recently in 1.6.2's own
    ``test_the_floor_field_is_tri_state_not_a_bool``. It passes every sentence
    nobody thought of, which is the only kind that has ever caused a defect
    here. The registry is keyed on EXACT SEGMENTS, so a reworded sentence is a
    new key and goes red until a human reads it.

STAGE 2, CORRECTNESS, asserts each classified claim's polarity against the
constant it is about. ``("NOAA", False)`` fails while
``UPCOMING_NOAA_PUBLISHED`` is ``True``.

WHAT THIS GATE CANNOT SEE — read this before trusting it

  * IT READS SENTENCES. A round-status claim expressed as a table cell with no
    verb, as a bare date, as a number, or as a heading is invisible to it. The
    ``Round Provenance`` sheet's DATES are not checked here; only prose about
    them is.

  * IT READS STRING LITERALS AND DOCSTRINGS, NOT COMMENTS. The source side of
    the corpus is collected with ``ast``, so it sees what the package can
    PRINT. A ``#`` comment cannot reach a reader and is out of scope on
    purpose — but note that ``renderers/_word_helpers.py:113-115`` carries a
    comment quoting a superseded rendered value, including the words "the CY
    2026 NOAA is not yet published", as a record of a truncation defect. It
    renders nowhere. If comments are ever brought into this corpus, that
    record has to be reworded first.

  * THE BASELINES ARE A FRESH RENDER, NOT A SNAPSHOT — but of ONE FIXTURE.
    ``tests/test_rendered_output_baseline.py`` renders all four formats from
    its own fixed fixture on every run and fails on any changed line, so the
    four ``.txt`` files this module reads cannot silently drift from what the
    renderers produce. They are still one fixture: a sentence that renders
    only on a branch that fixture does not take is not in this corpus.

  * ``_round_provenance.py`` IS EXCLUDED FROM THE SOURCE SCAN. It is the
    authority; scanning it would only assert it agrees with itself. Its text
    still reaches this gate — through all four rendered baselines, which is
    where it matters.

  * IT PROVES INTERNAL AGREEMENT, NOT TRUTH. See above.

MUTATIONS THIS GATE HAS BEEN SEEN TO FAIL UNDER — a gate never seen to fail is
not evidence, so each is recorded with the command and the red count it
produced. They are in the 1.6.3 commit message.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

import nmtcapp
from nmtcapp.renderers import _round_provenance as rp

# ---------------------------------------------------------------------------
# THE CORPUS
# ---------------------------------------------------------------------------

#: The four rendered projections, beside this file. Fails closed if absent.
BASELINE_DIR = os.path.join(os.path.dirname(__file__), "rendered_baseline")
BASELINE_FORMATS = ("markdown", "word", "excel", "pdf")

#: The package source, located through the IMPORTED package rather than as
#: ``../nmtcapp`` — so this reads the code actually under test whether the
#: suite runs from the repo, from an unpacked sdist, or against an install.
SOURCE_ROOT = os.path.dirname(os.path.abspath(nmtcapp.__file__))

#: THE AUTHORITY, EXCLUDED. Scanning the module that DEFINES the constants
#: would only assert it agrees with itself. Its prose is still gated — it
#: reaches this corpus through all four rendered baselines.
SOURCE_EXCLUDED = ("_round_provenance.py",)

# ---------------------------------------------------------------------------
# SELECTION
#
# Both token sets must hit for a segment to be selected. The round tokens are
# derived from ``UPCOMING_ROUND`` rather than typed, so the selector learns the
# next round's name instead of memorising this one's.
# ---------------------------------------------------------------------------

_STATUS_TOKEN = re.compile(r"\b(?:published|publishes|publication)\b", re.IGNORECASE)

_ROUND_WORDS = (rp.UPCOMING_ROUND, "NOAA", "Allocation Application",
                "Application Materials")
_ROUND_TOKEN = re.compile("|".join(re.escape(word) for word in _ROUND_WORDS))

#: The subjects a claim can be about, and the constant each is bound to.
SUBJECT_CONSTANTS = {
    "NOAA": "UPCOMING_NOAA_PUBLISHED",
    "APPLICATION": "UPCOMING_APPLICATION_PUBLISHED",
}

# ---------------------------------------------------------------------------
# SEGMENTATION
#
# THE CORPUS IS HARD-WRAPPED. markdown and pdf break sentences across lines, so
# a scan of raw lines misses every sentence that does not fit on one — which is
# most of the round-provenance note. Whitespace is therefore collapsed.
#
# BUT COLLAPSING EVERYTHING WELDS UNRELATED RECORDS TOGETHER. Measured on this
# corpus: a flat collapse merged an Excel cell, a Word paragraph and a PDF page
# header into single pseudo-sentences, and selected 42 segments of which 14
# were welding artifacts — a registry whose keys break whenever an unrelated
# cell moves, which is the recorded reason gates here get bypassed.
#
# So each projection's OWN record separators are honoured as block boundaries
# first, whitespace is collapsed WITHIN a block, and blocks are then split into
# sentences. Same corpus, 32 selected occurrences, no artifacts.
# ---------------------------------------------------------------------------

#: Page furniture and projection markers. Kept as blocks of their own rather
#: than dropped — nothing in the corpus is invisible to this scan.
_STANDALONE = re.compile(
    r"^\s*(?:@@(?:PAGE|SHEET)\b.*|Page \d+|.*\|\s+CONFIDENTIAL)\s*$"
)
#: ``Sheet Name!A9|str|fmt=General|<the cell's text>``
_EXCEL_RECORD = re.compile(r"^[^|\n]+![A-Z]{1,3}\d+\|[^|]*\|fmt=[^|]*\|")
#: ``P|Style|<text>``, ``T6|R7|<cell>|<cell>``, ``HDR|<text>``, ``FTR|<text>``
_WORD_RECORD = re.compile(r"^(?:P\|[^|]*\||HDR\||FTR\||T\d+\|R\d+\|)")
#: markdown structure: blank line, heading, list item, table row
_MARKDOWN_BREAK = re.compile(r"^(?:\s*$|#{1,6} |\s*[-*] |\s*\d+\. |\|)")

#: Split after terminal punctuation, KEEPING any closing bracket or quote with
#: the sentence it belongs to. Longest lookbehind first; Python lookbehinds are
#: fixed-width, hence three alternatives rather than a quantifier.
_SENTENCE_BREAK = re.compile(
    r'(?<=[.!?]["\')\]]["\')\]])\s+'
    r'|(?<=[.!?]["\')\]])\s+'
    r'|(?<=[.!?])\s+'
)

#: Abbreviations whose full stop does not end a sentence. Every one of these is
#: present in this corpus: "5:00 p.m. ET on November 10, 2026", "U.S. Island
#: Areas", "printed pp. 38-41".
_ABBREVIATIONS = (
    "p.m.", "a.m.", "U.S.", "pp.", "e.g.", "i.e.", "No.", "Inc.", "vs.",
    "cf.", "approx.", "Fig.", "St.", "Mr.", "Ms.", "Dr.",
)


def _blocks(text: str):
    """Yield the text's own records: cells, paragraphs, pages, md blocks."""
    current = []
    for line in text.split("\n"):
        if _STANDALONE.match(line):
            if current:
                yield " ".join(current)
            yield line
            current = []
            continue
        record = _EXCEL_RECORD.match(line) or _WORD_RECORD.match(line)
        if record:
            if current:
                yield " ".join(current)
            current = [line[record.end():]]
            continue
        if _MARKDOWN_BREAK.match(line):
            if current:
                yield " ".join(current)
            current = [line] if line.strip() else []
            continue
        current.append(line)
    if current:
        yield " ".join(current)


def segments(text: str) -> list:
    """``text`` as whitespace-normalised sentences."""
    out = []
    for block in _blocks(text):
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        merged = []
        for part in _SENTENCE_BREAK.split(block):
            if merged and any(merged[-1].endswith(a) for a in _ABBREVIATIONS):
                merged[-1] = merged[-1] + " " + part
            else:
                merged.append(part)
        out.extend(part.strip() for part in merged if part.strip())
    return out


def _python_literals(path: str) -> list:
    """Every string literal and docstring in ``path``, implicit joins joined.

    ``ast`` rather than a regex over the raw file: implicit concatenation is
    how every long piece of rendered prose in this package is written, and the
    parser joins it exactly the way the interpreter does. An f-string's
    interpolations become ``{}`` — this gate reads the sentence's WORDS, and a
    value it cannot evaluate is not one of them.
    """
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    found = []

    def walk(node):
        if isinstance(node, ast.JoinedStr):
            found.append("".join(
                value.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
                else "{}"
                for value in node.values
            ))
            return
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.append(node.value)
            return
        for child in ast.iter_child_nodes(node):
            walk(child)

    walk(ast.parse(source, filename=path))
    return found


def source_files() -> list:
    """Every ``nmtcapp`` module the scan reads, sorted."""
    paths = []
    for dirpath, dirnames, filenames in os.walk(SOURCE_ROOT):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".py") and name not in SOURCE_EXCLUDED:
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


def corpus() -> list:
    """``[(label, text)]`` — the four baselines, then every source literal."""
    items = []
    for fmt in BASELINE_FORMATS:
        path = os.path.join(BASELINE_DIR, fmt + ".txt")
        assert os.path.exists(path), (
            f"no rendered baseline for {fmt} at {path}. This gate reads the "
            "rendered output through those four files; without them it would "
            "pass having examined no rendered text at all."
        )
        with open(path, encoding="utf-8") as fh:
            items.append((f"rendered_baseline/{fmt}.txt", fh.read()))
    for path in source_files():
        label = os.path.relpath(path, os.path.dirname(SOURCE_ROOT))
        for text in _python_literals(path):
            items.append((label, text))
    return items


def selected() -> list:
    """``[(label, segment)]`` — every segment with a status AND a round token.

    ``finditer``, not ``search``: a segment carrying the tokens more than once
    is the normal case here and the scan must not stop at the first.
    """
    hits = []
    for label, text in corpus():
        for segment in segments(text):
            status = list(_STATUS_TOKEN.finditer(segment))
            round_ = list(_ROUND_TOKEN.finditer(segment))
            if status and round_:
                hits.append((label, segment))
    return hits


@pytest.fixture(scope="module")
def scan() -> list:
    return selected()


# ---------------------------------------------------------------------------
# THE REGISTRY
#
# Keyed on the EXACT normalised segment. Each value is the tuple of claims that
# segment makes: ``(subject, asserts_published)`` pairs, where subject is
# "NOAA" or "APPLICATION". ``()`` means the segment asserts nothing about
# either constant and requires a written reason in NON_CLAIM_REASONS below.
#
# A segment can make BOTH claims -- the note's provenance sentence states the
# NOAA's publication date and the Application's absence in one breath -- so the
# value is a tuple rather than a single pair.
#
# THE COMMENTS ABOVE EACH KEY ARE THE CORPUS MEMBERS IT WAS FOUND IN, recorded
# so a reviewer can see at a glance which surfaces a sentence reaches. They are
# not read by any assertion; test_every_registry_key_is_found_in_the_corpus
# re-derives the live answer.
# ---------------------------------------------------------------------------

ROUND_STATUS_CLAIMS = {
    # nmtcapp/renderers/_question_25.py
    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    "(Those area lists are the CY 2024-2025 Application's; the CY 2026 Allocation Application is not yet published.)":
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/word.txt
    'AND IF YOU ARE A PRIOR ALLOCATEE, A THIRD OBLIGATION FELL ON THE SAME CLOSED DATE: any prior Allocatee that required action by the CDFI Fund — certifying a Subsidiary entity as a CDE, or adding a Subsidiary CDE to an Allocation Agreement — in order to meet the Qualified Equity Investment (QEI) issuance thresholds published in the CY 2026 NOAA had to submit a CDE Certification Application for its Subsidiary CDE(s) through AMIS by 11:59 p.m. ET on August 31, 2026.':
        (("NOAA", True),),

    # rendered_baseline/pdf.txt
    'Agreement — in order to meet the Qualified Equity Investment (QEI) issuance thresholds published in the CY 2026 NOAA had to submit a CDE Certification Application for its Subsidiary CDE(s) through AMIS by 11:59 p.m. ET on August 31,':
        (("NOAA", True),),

    # nmtcapp/renderers/_question_25.py
    'CY 2024-2025 is CLOSED — it was awarded 23 Dec 2025 — and the CY 2026 Application is not yet published.':
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'Provenance: the CY 2026 NOAA is Federal Register document 2026-18883, filed September 14, 2026 and published September 15, 2026; the absence of CY 2026 Application Materials was confirmed on September 14, 2026.':
        (("NOAA", True), ("APPLICATION", False)),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'THE CY 2026 ROUND HAS OPENED, BUT ITS APPLICATION HAS NOT: the CY 2026 NOAA IS PUBLISHED — Federal Register document 2026-18883, publication date September 15, 2026 — and it makes $5 billion available, with applications due 5:00 p.m. ET on November 10, 2026.':
        (("NOAA", True),),

    # nmtcapp/data/historical_awards.py
    'THIS IS A RECORD, NOT A FORECAST: neither the CDFI Fund nor this tool publishes an expected acceptance rate for any future round, and CY 2026 is a $5 billion single round.':
        (),

    # nmtcapp/intelligence/recommendations.py
    "The CDFI Fund publishes no 'Special Targeting' criterion and no bonus points for it: the CY 2024-2025 NOAA sets out exactly two statutory priorities under IRC §45D(f)(2), worth ten additional points in total, and this tool scores both of them elsewhere.":
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'The CY 2026 Allocation Application and its Application Materials are NOT YET PUBLISHED, so the instrument encoded here is still the CY 2024-2025 one.':
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'This tool encodes the CY 2024-2025 NMTC Allocation Application, which is the most recent PUBLISHED Application and is closed and awarded (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    "To be eligible to apply in CY 2026 an organization had EITHER to already be a certified CDE as of the NOAA's Federal Register publication date, September 15, 2026, OR to have submitted its CDE Certification Application through AMIS by 11:59 p.m. ET on August 31, 2026.":
        (("NOAA", True),),

}

#: Why a selected segment asserts NOTHING about either constant. Required
#: for every ``()`` entry above, and read by
#: ``test_a_non_claim_carries_a_written_reason``.
NON_CLAIM_REASONS = {
    'THIS IS A RECORD, NOT A FORECAST: neither the CDFI Fund nor this tool publishes an expected acceptance rate for any future round, and CY 2026 is a $5 billion single round.':
        "Not about publication of a CY 2026 instrument. 'publishes' takes 'an expected acceptance rate' as its object and the sentence's point is that nobody publishes one; 'CY 2026' names the round whose SIZE it states. Neither constant is addressed.",

    "The CDFI Fund publishes no 'Special Targeting' criterion and no bonus points for it: the CY 2024-2025 NOAA sets out exactly two statutory priorities under IRC §45D(f)(2), worth ten additional points in total, and this tool scores both of them elsewhere.":
        "Not about publication of a CY 2026 instrument. The object of 'publishes' is a SCORING CRITERION, and the NOAA it names is the CY 2024-2025 one. Neither constant is addressed.",

    'This tool encodes the CY 2024-2025 NMTC Allocation Application, which is the most recent PUBLISHED Application and is closed and awarded (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        "About the CITED round, not the upcoming one: it says the instrument this package encodes is the most recent PUBLISHED Application and that its round is closed and awarded. CY 2024-2025's publication is not either constant's subject.",

}


# ---------------------------------------------------------------------------
# THE FLOORS, MEASURED — NOT GUESSED
#
# Measured on 2026-09-15 against this tree, by running ``selected()``:
#
#     32 selected occurrences
#     11 distinct segments
#     70 nmtcapp modules scanned (excluding _round_provenance.py)
#     9,110 segments in the corpus in total
#
# Each floor sits BELOW its measurement so that deleting a sentence or two is
# not automatically red, and FAR above zero so that an empty corpus, a broken
# segmenter or a selector that stops matching is. Rule j4: a scan that selects
# nothing must FAIL, because "no violations found" and "nothing was looked at"
# are the same green.
# ---------------------------------------------------------------------------

_MIN_SELECTED_OCCURRENCES = 24        # measured 32
_MIN_SELECTED_SEGMENTS = 8            # measured 11
_MIN_SOURCE_FILES = 50                # measured 70
_MIN_CORPUS_SEGMENTS = 5000           # measured 9,110

#: THE BACKSTOP ON THE ``()`` CLASSIFICATION. ``()`` means "this segment
#: asserts nothing about either constant", and it is the one way a human could
#: wave the 1.6.2 defect through. So the sentence SHAPE of that defect is
#: written down, and no ``()`` entry may match it. Derived from
#: ``UPCOMING_ROUND`` rather than typed, and asserted non-vacuous below.
_ASSERTION_SHAPE = re.compile(
    re.escape(rp.UPCOMING_ROUND)
    + r"\s+(?:NOAA|Allocation Application|Application Materials)"
      r"[^.;]{0,120}?\b(?:is|are|was|were|has|have|had|be|been)\b"
      r"[^.;]{0,60}?\bpublish",
    re.IGNORECASE,
)

#: Every ``(segment, subject, asserts_published)`` stage 2 adjudicates.
_CLAIM_ITEMS = [
    (segment, subject, asserts_published)
    for segment, claims in ROUND_STATUS_CLAIMS.items()
    for subject, asserts_published in claims
]
_CLAIM_IDS = [
    f"{i:02d}-{subject}-{'published' if asserts else 'unpublished'}"
    for i, (_segment, subject, asserts) in enumerate(_CLAIM_ITEMS)
]


# ---------------------------------------------------------------------------
# STAGE 1 — COMPLETENESS
#
# The stage that catches the NEXT one. Everything here is about whether a
# sentence was SEEN, not about whether it is right.
# ---------------------------------------------------------------------------

def test_every_round_status_segment_is_classified(scan):
    """An unclassified round-status sentence FAILS, quoting itself.

    THIS IS THE GATE 1.6.2 DID NOT HAVE. Its author did not decide wrongly
    about ``_question_25``'s last sentence — they never saw it, because no
    scanner in the package looked outside ``_round_provenance``. A registry
    keyed on exact text means a new or reworded sentence cannot enter the
    rendered output without a human classifying it first.
    """
    unclassified = sorted(
        {(segment, label) for label, segment in scan
         if segment not in ROUND_STATUS_CLAIMS}
    )
    assert not unclassified, (
        f"{len(unclassified)} round-status segment(s) are not in "
        "ROUND_STATUS_CLAIMS.\n\n"
        "Each one carries a publication-status word AND a round word, and "
        "nothing in this suite has checked it against "
        f"{sorted(SUBJECT_CONSTANTS.values())}. CLASSIFY IT — add it as a key "
        "with the claims it makes, or with `()` plus a reason in "
        "NON_CLAIM_REASONS saying why it asserts nothing:\n\n"
        + "\n\n".join(f"  {label}\n    {segment!r}"
                      for segment, label in unclassified)
    )


def test_every_registry_key_is_found_in_the_corpus(scan):
    """A registry entry matching nothing is a dead allowlist.

    Without this the registry only ever grows, and a reviewer cannot tell a
    live classification from a sentence that was deleted three releases ago.
    Same property ``test_allowlist_has_no_dead_entries`` holds over the
    invariance allowlist, and for the same reason.
    """
    found = {segment for _label, segment in scan}
    dead = sorted(set(ROUND_STATUS_CLAIMS) - found)
    assert not dead, (
        f"{len(dead)} registry entr(ies) no longer appear anywhere in the "
        "corpus. Either the sentence was reworded — in which case classify "
        "the new spelling and delete this one — or it was removed, in which "
        "case delete this one:\n\n"
        + "\n".join(f"  {segment!r}" for segment in dead)
    )


def test_a_non_claim_carries_a_written_reason():
    """`()` is the one escape hatch here, so it costs a written argument.

    A classification of "this asserts nothing" cannot be re-derived by a
    machine — it is a reading. What CAN be required is that somebody made the
    reading in writing, in the diff, where a reviewer sees it.
    """
    stray = sorted(set(NON_CLAIM_REASONS) - set(ROUND_STATUS_CLAIMS))
    assert not stray, (
        f"NON_CLAIM_REASONS explains {len(stray)} segment(s) that are not in "
        f"ROUND_STATUS_CLAIMS at all: {stray}"
    )
    for segment, claims in ROUND_STATUS_CLAIMS.items():
        if claims:
            assert segment not in NON_CLAIM_REASONS, (
                "a segment with claims also carries a non-claim reason, which "
                f"says two opposite things about it: {segment!r}"
            )
            continue
        reason = NON_CLAIM_REASONS.get(segment, "")
        assert len(reason) >= 60, (
            "a `()` classification means 'this sentence asserts nothing about "
            "whether a CY 2026 instrument has published'. That is a reading, "
            "and it has to be argued rather than asserted. Add it to "
            f"NON_CLAIM_REASONS:\n\n    {segment!r}"
        )

    claims = [s for s, c in ROUND_STATUS_CLAIMS.items() if c]
    non_claims = [s for s, c in ROUND_STATUS_CLAIMS.items() if not c]
    assert len(non_claims) < len(claims), (
        f"{len(non_claims)} of {len(ROUND_STATUS_CLAIMS)} selected segments "
        "are classified as asserting nothing. Measured on 2026-09-15 it was 3 "
        "of 11. If most of what the selector finds is being waved through, "
        "the selector has drifted or the escape hatch is being used as one — "
        "either way stage 2 is adjudicating a minority of what stage 1 sees."
    )


def test_no_non_claim_hides_a_round_status_assertion():
    """The 1.6.2 sentence's SHAPE may never be classified as "asserts nothing".

    ``(The CY 2026 NOAA is not yet published.)`` matches ``_ASSERTION_SHAPE``.
    So would any restatement of it. This is what stops the escape hatch from
    becoming the way the defect comes back.
    """
    hidden = sorted(
        segment for segment, claims in ROUND_STATUS_CLAIMS.items()
        if not claims and list(_ASSERTION_SHAPE.finditer(segment))
    )
    assert not hidden, (
        f"{len(hidden)} segment(s) classified as asserting nothing DO carry "
        f"the shape '<{rp.UPCOMING_ROUND} instrument> ... is/are ... "
        "publish...'. That is the exact shape of the sentence this gate "
        "exists for. Classify them:\n\n"
        + "\n".join(f"  {segment!r}" for segment in hidden)
    )


def test_the_assertion_shape_backstop_is_not_vacuous():
    """A backstop no sentence has ever matched is not a backstop."""
    matched = [segment for segment, claims in ROUND_STATUS_CLAIMS.items()
               if claims and list(_ASSERTION_SHAPE.finditer(segment))]
    assert matched, (
        "_ASSERTION_SHAPE matches none of the registered claims, so "
        "test_no_non_claim_hides_a_round_status_assertion could not fail on "
        "anything. The pattern is broken, not the registry."
    )


# ---------------------------------------------------------------------------
# ANTI-VACUITY. Rule j4: nothing here may pass by having looked at nothing.
# ---------------------------------------------------------------------------

def test_the_scan_reads_a_real_corpus():
    """The corpus, the segmenter and the source walk all still work.

    Stated as three separate floors because they fail for three different
    reasons, and a single "selected nothing" red cannot tell them apart: a
    missing baseline, a segmenter that stopped splitting, and a source walk
    pointed at the wrong tree all look identical from the selection count.
    """
    for fmt in BASELINE_FORMATS:
        path = os.path.join(BASELINE_DIR, fmt + ".txt")
        assert os.path.exists(path), f"no rendered baseline for {fmt}: {path}"

    files = source_files()
    assert len(files) >= _MIN_SOURCE_FILES, (
        f"the source walk found {len(files)} modules under {SOURCE_ROOT}, "
        f"below the {_MIN_SOURCE_FILES} floor (70 measured). It is pointed at "
        "the wrong tree, or the package moved."
    )

    total = sum(len(segments(text)) for _label, text in corpus())
    assert total >= _MIN_CORPUS_SEGMENTS, (
        f"the corpus segmented into {total} sentences, below the "
        f"{_MIN_CORPUS_SEGMENTS} floor (9,110 measured). The segmenter is "
        "broken, and a broken segmenter selects nothing and passes stage 1."
    )


def test_the_scan_selects_at_least_the_measured_floor(scan):
    """A stage-1 scan that selects ZERO segments must FAIL, not pass."""
    assert len(scan) >= _MIN_SELECTED_OCCURRENCES, (
        f"the scan selected {len(scan)} round-status occurrence(s), below the "
        f"{_MIN_SELECTED_OCCURRENCES} floor (32 measured on 2026-09-15). "
        "Either the corpus shrank, or the selector stopped matching — and a "
        "selector that matches nothing makes every other test in this module "
        "pass on an empty set."
    )
    distinct = {segment for _label, segment in scan}
    assert len(distinct) >= _MIN_SELECTED_SEGMENTS, (
        f"the scan selected {len(distinct)} distinct segment(s), below the "
        f"{_MIN_SELECTED_SEGMENTS} floor (11 measured)."
    )


def test_every_baseline_format_contributes_a_claim(scan):
    """A gate satisfied by one format is not a gate.

    The 1.6.2 sentence rendered in all four. A scan that reached only markdown
    would have found it and still have been blind to the three formats a CDE
    is more likely to submit.
    """
    claimed = {
        label for label, segment in scan
        if ROUND_STATUS_CLAIMS.get(segment)
    }
    for fmt in BASELINE_FORMATS:
        label = f"rendered_baseline/{fmt}.txt"
        assert label in claimed, (
            f"no classified round-status CLAIM was found in {label}. The "
            "round-provenance note renders on all four surfaces; a format "
            "contributing none means this gate is not reading it."
        )


def test_both_subjects_and_both_polarities_are_represented():
    """NOAA and APPLICATION, published and not.

    The two constants disagree with each other right now — that is the whole
    reason 1.6.2 split them — so a registry carrying only one subject, or only
    one polarity, is one that cannot tell them apart.
    """
    subjects = {subject for _s, subject, _a in _CLAIM_ITEMS}
    assert subjects == set(SUBJECT_CONSTANTS), (
        f"the registry adjudicates {sorted(subjects)}; the constants are "
        f"{sorted(SUBJECT_CONSTANTS)}. A subject with no registered claim is "
        "a constant nothing is bound to."
    )
    polarities = {asserts for _s, _subject, asserts in _CLAIM_ITEMS}
    assert polarities == {True, False}, (
        f"every registered claim has asserts_published={polarities}. One "
        "polarity means a flipped constant could only ever fail in one "
        "direction."
    )


def test_the_excluded_authority_module_is_still_where_the_exclusion_points():
    """``_round_provenance.py`` is skipped BY NAME, so the name must be live.

    If it is renamed, the exclusion silently stops applying and this gate
    starts asserting that the authority agrees with itself — which it always
    will. Noticing the rename is the point.
    """
    path = os.path.join(SOURCE_ROOT, "renderers", "_round_provenance.py")
    assert os.path.exists(path), (
        f"{SOURCE_EXCLUDED[0]} is not at {path}. The source scan excludes it "
        "by basename; if the module moved or was renamed, update "
        "SOURCE_EXCLUDED rather than leaving an exclusion that matches "
        "nothing."
    )


# ---------------------------------------------------------------------------
# STAGE 2 — CORRECTNESS
# ---------------------------------------------------------------------------

def test_stage_two_has_something_to_adjudicate():
    """Stage 2 parametrises over the registry; an empty one is a silent pass."""
    assert ROUND_STATUS_CLAIMS, "the registry is empty"
    assert len(_CLAIM_ITEMS) >= 6, (
        f"stage 2 adjudicates {len(_CLAIM_ITEMS)} claim(s); 9 were measured on "
        "2026-09-15. Below this the parametrisation is not covering the note."
    )


@pytest.mark.parametrize("segment,subject,asserts_published",
                         _CLAIM_ITEMS, ids=_CLAIM_IDS)
def test_a_registered_claim_agrees_with_its_constant(
        segment, subject, asserts_published):
    """The polarity a sentence states must be the polarity the constant holds.

    This is the assertion that would have gone red on 1.6.2's shipped tree.
    """
    constant = SUBJECT_CONSTANTS[subject]
    actual = getattr(rp, constant)
    assert asserts_published == actual, (
        f"a rendered sentence says the {rp.UPCOMING_ROUND} {subject} "
        f"{'IS' if asserts_published else 'IS NOT'} published, and "
        f"_round_provenance.{constant} is {actual}.\n\n"
        f"    {segment!r}\n\n"
        "One of the two is wrong and they are in different files, which is "
        "precisely how 1.6.2 shipped a document that said the CY 2026 NOAA "
        "was unpublished on page 8 and published on page 26. Fix the sentence "
        "in its own module, regenerate tests/rendered_baseline/, and update "
        "this registry entry in the same commit."
    )
