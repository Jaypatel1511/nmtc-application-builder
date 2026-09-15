"""ROUND-STATUS CLAIMS MUST AGREE WITH ``_round_provenance``'S CONSTANTS.

THE DEFECT THIS EXISTS FOR (1.6.2 -> 1.6.3)

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

Every gate in the suite was green. ``tests/test_round_provenance.py`` reads the
note ``_round_provenance`` renders and nothing else, so a round-status sentence
in another module was outside every scanner in the package.

AND THE FIRST VERSION OF THIS MODULE REPRODUCED THE DEFECT IT WAS WRITTEN FOR

1.6.3's build round shipped this selector::

    _STATUS_TOKEN = re.compile(r"\\b(?:published|publishes|publication)\\b")

and required a segment to match it BEFORE it could be required to be
classified. ``\\bpublished\\b`` cannot match inside ``unpublished`` -- ``n`` and
``p`` are both word characters, so there is no boundary between them. Measured:

    False | The CY 2026 NOAA remains unpublished.
    True  | (The CY 2026 NOAA is not yet published.)

Same claim, same falsity, same surface; one word of spelling decided whether
the gate existed. And the blind spot was OCCUPIED on the day it was written:
four round-status sentences in shipped source said "unpublished" and the gate
reported nothing about any of them while reporting "32 selected".

Widening the word list buys one round. ``released``, ``issued``, ``out``,
``available``, ``dropped``, ``live`` are all next, and every version of the
list fails SILENTLY -- which is the one property this gate exists to remove.

WHAT CHANGED, AND IT IS THE WHOLE POINT OF THIS MODULE

**Selection is on the SUBJECT, not on how the claim is spelled.** The subject
of these two constants is the UPCOMING ROUND, and the round has one name,
derived here from ``rp.UPCOMING_ROUND`` rather than typed. A segment that names
the round must be classified in ``ROUND_STATUS_CLAIMS`` no matter what it says
about it -- so a spelling nobody thought of cannot make a sentence invisible,
because nothing about the claim's wording is consulted to decide whether the
sentence is looked at.

Most registry entries are therefore ``()``: they name the round and assert
nothing about publication. That is correct, and it is the price of
completeness. Every key is a sentence about the live round that a human read
once.

    THE STATUS VOCABULARY STILL EXISTS, BUT IT CAN NOW ONLY EVER ADD FAILURES.
    ``_STATUS_VOCABULARY`` appears in exactly two places: as an ADDITIONAL way
    into the corpus (an instrument word plus a status word is selected even
    where the round is not named), and as a COST on the ``()`` classification
    (a ``()`` segment carrying status vocabulary must carry a written reason,
    and may not match ``_ASSERTION_SHAPE`` at all). A spelling missing from
    that list can no longer hide anything: the segment is still selected by the
    round token and still has to be registered. Deleting a word from
    ``_STATUS_VOCABULARY`` cannot turn a red into a green for any segment that
    names the round. That is mutation M9 in the 1.6.3 commit message, and it is
    the proof this module is not the thing it replaced.

THE THREE WAYS IN

  1. The segment names ``rp.UPCOMING_ROUND``. This is the primary selector and
     it consults nothing about the claim.
  2. The segment names an instrument (NOAA / Allocation Application /
     Application Materials) and the corpus item CONTAINING it names the round.
     A docstring that says "CY 2026" in its first paragraph and "the NOAA" in
     its fourth is talking about the same round in both; this resolves that.
  3. The segment names an instrument and carries status vocabulary, wherever it
     is. The context-free net, and the only one the spelling list feeds.

THE TWO STAGES

STAGE 1, COMPLETENESS, is the stage that catches the NEXT one. A selected
segment that is not a key of ``ROUND_STATUS_CLAIMS`` FAILS, quoting itself and
asking to be classified.

STAGE 2, CORRECTNESS, asserts each classified claim's polarity against the
constant it is about. ``("NOAA", False)`` fails while
``UPCOMING_NOAA_PUBLISHED`` is ``True``.

WHAT THIS GATE CANNOT SEE -- read this before trusting it

  * IT READS SENTENCES. A round-status claim expressed as a table cell with no
    verb, as a bare date, as a number, or as a heading is invisible to it.

  * IT READS SOURCE, NOT BEHAVIOUR. String literals, docstrings and ``#``
    comments are all in the corpus -- a false comment is a false claim in
    shipped source, and ``renderers/_word_helpers``'s deliberate historical
    quotation of a superseded rendered value is registered ``()`` with its
    reason rather than excluded by dropping a whole syntactic class. But a
    sentence ASSEMBLED at run time from pieces that individually name nothing
    is not in this corpus. An f-string's interpolations become ``{}``.

  * A SEGMENT THAT NAMES NEITHER THE ROUND NOR AN INSTRUMENT IS NOT SELECTED.
    "It has not been released yet", standing alone in a docstring that never
    names CY 2026 and never names the NOAA, is outside all three nets. That is
    the residual hole and it is a SUBJECT hole, not a spelling one.

  * THE BASELINES ARE A FRESH RENDER, NOT A SNAPSHOT -- but of ONE FIXTURE.
    ``tests/test_rendered_output_baseline.py`` renders all four formats from
    its own fixed fixture on every run and fails on any changed line, so the
    four ``.txt`` files this module reads cannot silently drift from what the
    renderers produce. They are still one fixture: a sentence that renders only
    on a branch that fixture does not take is not in this corpus.

  * NOTHING IS EXCLUDED FROM THE SOURCE SCAN ANY MORE. 1.6.3's build round
    excluded ``_round_provenance.py`` as "the authority", on the stated grounds
    that "its text still reaches this gate through all four rendered
    baselines". That justification was false for the module's DOCSTRING, which
    renders nowhere, and the docstring carried round-status prose. The module
    is scanned. Its CONSTANTS are Python literals, not sentences, so scanning
    it costs a handful of registry entries and closes the hole.

  * IT PROVES INTERNAL AGREEMENT, NOT TRUTH. The constants are assertions
    somebody typed with a date on them, not measurements. This gate proves the
    package AGREES WITH ITSELF. Truth is a different gate and it already
    exists: ``tests/test_round_provenance.test_the_round_claim_has_not_expired``
    makes the claim EXPIRE (``RECHECK_AFTER``, currently 2026-10-05).

MUTATIONS THIS GATE HAS BEEN SEEN TO FAIL UNDER -- a gate never seen to fail is
not evidence, so each is recorded with the command and the red count it
produced. They are in the 1.6.3 commit message.
"""
from __future__ import annotations

import ast
import io
import os
import re
import tokenize

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
#: ``../nmtcapp`` -- so this reads the code actually under test whether the
#: suite runs from the repo, from an unpacked sdist, or against an install.
SOURCE_ROOT = os.path.dirname(os.path.abspath(nmtcapp.__file__))

#: ``streamlit_app/`` ships in the sdist and release.yml's sdist job copies it
#: out of the tarball, so a repo-relative path resolves in both places -- the
#: same resolution ``tests/test_cde_scoring_inputs`` uses, and for the same
#: reason it does NOT resolve ``nmtcapp/`` that way. It carried a false
#: round-status comment ("not yet open") on the day the round opened, and it
#: was in no scanner in this suite.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMLIT_ROOT = os.path.join(REPO_ROOT, "streamlit_app")

# ---------------------------------------------------------------------------
# SELECTION -- ON THE SUBJECT
#
# ``_ROUND_TOKEN`` is derived from ``UPCOMING_ROUND``, not typed, so the
# selector learns the next round's name instead of memorising this one's.
# ---------------------------------------------------------------------------

#: THE PRIMARY SELECTOR. Names the round => must be classified. Nothing about
#: the claim's wording is consulted.
_ROUND_TOKEN = re.compile(re.escape(rp.UPCOMING_ROUND))

#: The instruments whose publication the two constants are about.
_INSTRUMENT_TOKEN = re.compile(
    r"NOAA|Allocation Application|Application Materials"
)

#: PUBLICATION-STATUS VOCABULARY. Read this beside the docstring paragraph
#: above: it is NOT a condition of selection for anything that names the round.
#: It widens the net (instrument + status word, context-free) and it makes the
#: ``()`` classification cost a written argument. Both directions ADD failures.
#: ``publish`` is matched as a STEM WITHOUT A LEADING WORD BOUNDARY, which is
#: the specific thing the 1.6.3 build round got wrong: ``\bpublished\b`` cannot
#: match inside ``unpublished``.
_STATUS_VOCABULARY = re.compile(
    r"publish\w*|publicat\w*|releas\w*|issu\w*|\bopen\w*|\bavailab\w*",
    re.IGNORECASE,
)

#: The subjects a claim can be about, and the constant each is bound to.
SUBJECT_CONSTANTS = {
    "NOAA": "UPCOMING_NOAA_PUBLISHED",
    "APPLICATION": "UPCOMING_APPLICATION_PUBLISHED",
}

# ---------------------------------------------------------------------------
# SEGMENTATION
#
# THE CORPUS IS HARD-WRAPPED. markdown and pdf break sentences across lines, so
# a scan of raw lines misses every sentence that does not fit on one -- which is
# most of the round-provenance note. Whitespace is therefore collapsed.
#
# BUT COLLAPSING EVERYTHING WELDS UNRELATED RECORDS TOGETHER. Measured on this
# corpus: a flat collapse merged an Excel cell, a Word paragraph and a PDF page
# header into single pseudo-sentences, and selected 42 segments of which 14
# were welding artifacts -- a registry whose keys break whenever an unrelated
# cell moves, which is the recorded reason gates here get bypassed.
#
# So each projection's OWN record separators are honoured as block boundaries
# first, whitespace is collapsed WITHIN a block, and blocks are then split into
# sentences.
# ---------------------------------------------------------------------------

#: Page furniture and projection markers. Kept as blocks of their own rather
#: than dropped -- nothing in the corpus is invisible to this scan.
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
    interpolations become ``{}`` -- this gate reads the sentence's WORDS, and a
    value it cannot evaluate is not one of them.
    """
    with io.open(path, encoding="utf-8") as fh:
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


def _comment_blocks(path: str) -> list:
    """Every RUN of consecutive ``#`` comment lines in ``path``, joined.

    A false comment is a false claim in shipped source, so comments are in the
    corpus. They are joined by RUN rather than taken per line because comments
    here are hard-wrapped exactly as the prose is -- ``_round_provenance``'s
    own ``#:`` block splits one sentence across four lines, and four fragments
    are four unreadable registry keys instead of one sentence a human can
    classify. The leading ``#`` and the ``#:`` doc-comment marker are stripped.
    """
    runs = []
    current = []
    previous_line = None
    with io.open(path, "rb") as fh:
        for token in tokenize.tokenize(fh.readline):
            if token.type != tokenize.COMMENT:
                continue
            body = token.string.lstrip("#").lstrip(":").strip()
            if previous_line is not None and token.start[0] == previous_line + 1:
                current.append(body)
            else:
                if current:
                    runs.append(" ".join(current))
                current = [body]
            previous_line = token.start[0]
    if current:
        runs.append(" ".join(current))
    return runs


def source_files() -> list:
    """Every module the scan reads, sorted. NOTHING is excluded.

    ``nmtcapp`` through the installed package, ``streamlit_app`` through the
    repo root -- see the note on ``STREAMLIT_ROOT``.
    """
    paths = []
    for root in (SOURCE_ROOT, STREAMLIT_ROOT):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for name in sorted(filenames):
                if name.endswith(".py"):
                    paths.append(os.path.join(dirpath, name))
    return sorted(paths)


def _label(path: str, kind: str) -> str:
    base = REPO_ROOT if path.startswith(REPO_ROOT + os.sep) else \
        os.path.dirname(SOURCE_ROOT)
    return os.path.relpath(path, base) + kind


def corpus() -> list:
    """``[(label, text)]`` -- the four baselines, then every source item."""
    items = []
    for fmt in BASELINE_FORMATS:
        path = os.path.join(BASELINE_DIR, fmt + ".txt")
        assert os.path.exists(path), (
            f"no rendered baseline for {fmt} at {path}. This gate reads the "
            "rendered output through those four files; without them it would "
            "pass having examined no rendered text at all."
        )
        with io.open(path, encoding="utf-8") as fh:
            items.append((f"rendered_baseline/{fmt}.txt", fh.read()))
    for path in source_files():
        for text in _python_literals(path):
            items.append((_label(path, ""), text))
        for text in _comment_blocks(path):
            items.append((_label(path, " [#]"), text))
    return items


def selected() -> list:
    """``[(label, segment)]`` -- every segment about the upcoming round.

    Three nets, described in the module docstring. ``finditer``, not
    ``search``: a segment carrying the tokens more than once is the normal case
    here and the scan must not stop at the first.
    """
    hits = []
    for label, text in corpus():
        names_round = bool(list(_ROUND_TOKEN.finditer(text)))
        for segment in segments(text):
            if list(_ROUND_TOKEN.finditer(segment)):
                hits.append((label, segment))
                continue
            if not list(_INSTRUMENT_TOKEN.finditer(segment)):
                continue
            if names_round or list(_STATUS_VOCABULARY.finditer(segment)):
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
# either constant.
#
# MOST ENTRIES ARE ``()`` AND THAT IS THE DESIGN, NOT A FAILURE OF IT. Stage 1
# selects on the SUBJECT — a segment that names the upcoming round is read,
# whatever it says — so the registry holds every sentence in the rendered
# output, the package source and the Streamlit app that mentions the round.
# Measured here: 104 segments, of which 25 carry claims and
# 79 assert nothing. The alternative, requiring a publication word
# before a sentence is looked at, is what shipped in the build round and it
# was blind to four sentences in this tree on the day it was written.
#
# A ``()`` entry that carries publication-status vocabulary costs a written
# reason in ``NON_CLAIM_REASONS``; one that carries none is free, because
# there is nothing in it to argue about.
#
# A segment can make BOTH claims -- the note's provenance sentence states the
# NOAA's publication date and the Application's absence in one breath -- so the
# value is a tuple rather than a single pair.
#
# THE COMMENTS ABOVE EACH KEY ARE THE CORPUS MEMBERS IT WAS FOUND IN, recorded
# so a reviewer can see at a glance which surfaces a sentence reaches. They are
# not read by any assertion; test_every_registry_key_is_found_in_the_corpus
# re-derives the live answer. A label ending " [#]" is a ``#`` comment run.
# ---------------------------------------------------------------------------

ROUND_STATUS_CLAIMS = {
    # nmtcapp/renderers/_question_25.py
    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    "(Those area lists are the CY 2024-2025 Application's; the CY 2026 Allocation Application is not yet published.)":
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    '* The CY 2026 **Allocation Application** and its Application Materials are **NOT published**.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    '* The CY 2026 **NOAA** is **PUBLISHED** -- Federal Register document 2026-18883, filed 14 Sep 2026 08:45 ET, publication date 15 Sep 2026.':
        (("NOAA", True),),

    # rendered_baseline/markdown.txt
    '**QEI in Deep Distress Tracts (a share of QEI, not of QLICIs — see the basis note below):** 52.2% **QEI in Severely Distressed Tracts, Deep Distress included (a share of QEI, not of QLICIs — see the basis note below):** 85.3% **— of which severely distressed but not also deep:** 33.1% **QEI in LIC (Standard Eligible) Tracts:** 14.7% **QEI in NMTC Native Areas (CDE-declared, not verified by this tool):** 5.9% **QEI in High Migration Rural (HMR) Tracts:** 12.7% **BASIS NOTE — the CDFI Fund\'s two distress commitments are measured on QLICIs, not on QEI:** Question 25 of the CY 2024-2025 NMTC Allocation Application (printed pp. 38-41) sets both commitments, and both are measured on QLICIs — specifically on QLICIs "in terms of aggregate dollar amounts", tested for each QLICI.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    '**That is the correct engineering choice.** There is no other defensible one: the CY 2026 Application is unpublished, and a tool that declined to encode any instrument until it appeared would be useless during exactly the window a CDE needs it.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    '**The CY 2024-2025 Application is not unreliable.** It is a real federal instrument, retrieved and hash-verified, and it is the best available basis for preparing a CY 2026 application.':
        (),

    # streamlit_app/pages/4_About_and_Methodology.py
    '*Both instruments re-opened and text-extracted locally with pypdf on 2026-08-22 for the two citations added above — Review Process, 7pp, 187,497 bytes, SHA-256 `ad0dc777eab0dc8cf437d970418bcdbea8403eb99b79dd1662f4ce94eab98749`; Allocation Application, 142pp, 1,525,626 bytes, SHA-256 `0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bded8de12834f`.':
        (),

    # nmtcapp/renderers/_question_22.py
    '31, verbatim: "Question 22 will not be evaluated and scored in Phase I of Allocation Application reviews.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/word.txt
    'AND IF YOU ARE A PRIOR ALLOCATEE, A THIRD OBLIGATION FELL ON THE SAME CLOSED DATE: any prior Allocatee that required action by the CDFI Fund — certifying a Subsidiary entity as a CDE, or adding a Subsidiary CDE to an Allocation Agreement — in order to meet the Qualified Equity Investment (QEI) issuance thresholds published in the CY 2026 NOAA had to submit a CDE Certification Application for its Subsidiary CDE(s) through AMIS by 11:59 p.m. ET on August 31, 2026.':
        (("NOAA", True),),

    # nmtcapp/renderers/_round_provenance.py
    'AND IF YOU ARE A PRIOR ALLOCATEE, A THIRD OBLIGATION FELL ON THE SAME CLOSED DATE: any prior Allocatee that required action by the CDFI Fund — certifying a Subsidiary entity as a CDE, or adding a Subsidiary CDE to an Allocation Agreement — in order to meet the Qualified Equity Investment (QEI) issuance thresholds published in the {} NOAA had to submit a CDE Certification Application for its Subsidiary CDE(s) through AMIS by {}.':
        (("NOAA", True),),

    # nmtcapp/renderers/_round_provenance.py [#]
    'Aggregate allocation authority the CY 2026 NOAA makes available.':
        (),

    # rendered_baseline/pdf.txt
    'Agreement — in order to meet the Qualified Equity Investment (QEI) issuance thresholds published in the CY 2026 NOAA had to submit a CDE Certification Application for its Subsidiary CDE(s) through AMIS by 11:59 p.m. ET on August 31,':
        (("NOAA", True),),

    # nmtcapp/renderers/_word_helpers.py [#]
    'An 80-char cut with an ellipsis silently removed the tail of any long cell — including Section B\'s severe-distress row, whose value ended "…Review Process; the CY 2026 NOAA is not yet published)".':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'An annual-rate comparison would be a NEW inference, and this package does not make those; the NOAA states an amount and does not compare it to anything.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'An organization that did neither CANNOT APPLY IN CY 2026.':
        (),

    # rendered_baseline/markdown.txt
    "Application Round: CY 2026 Requested Allocation: **$70,000,000** Prepared: <RUNDATE> Readiness Grade: **B** (84.9/100 — this tool's own unsourced house heuristic, not a CDFI Fund evaluation)":
        (),

    # rendered_baseline/word.txt
    'Application Round:|CY 2026':
        (),

    # rendered_baseline/word.txt
    'BASIS NOTE — the CDFI Fund\'s two distress commitments are measured on QLICIs, not on QEI|Question 25 of the CY 2024-2025 NMTC Allocation Application (printed pp. 38-41) sets both commitments, and both are measured on QLICIs — specifically on QLICIs "in terms of aggregate dollar amounts", tested for each QLICI.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    "But it is a PROXY for the CY 2026 instrument, not that instrument, so every round-specific figure in this document must be re-verified against the CY 2026 Application Materials on the day the Fund releases them — specifically: the allocation authority and the number of awards available; the CDE certification deadline for eligibility; Question 25's QLICI-denominated commitment levels, its area-type lists and its ladder; Question 22's QLICI-denominated Non-Metropolitan minimum and maximum; Question 15's product-flexibility ladder; the scoring thresholds in the Review Process.":
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    'But it is a PROXY for the {} instrument, not that instrument, so every round-specific figure in this document must be re-verified against the {} Application Materials on the day the Fund releases them — specifically: {}.':
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    'CONFIDENTIAL — Great Lakes Regional Capital CDE, LLC — NMTC CY 2026 — Generated <RUNDATE>':
        (),

    # nmtcapp/renderers/_question_22.py
    'CY 2024-2025 NMTC Program Allocation Application, re-downloaded, re-hashed and text-extracted LOCALLY with pypdf.':
        (),

    # nmtcapp/renderers/_question_25.py
    'CY 2024-2025 NMTC Program Allocation Application, retrieved 2026-08-17 and text-extracted LOCALLY with pypdf — not fetched through a summarising model, which is the provenance failure this whole cycle exists to correct.':
        (),

    # nmtcapp/renderers/_question_25.py
    'CY 2024-2025 is CLOSED — it was awarded 23 Dec 2025 — and the CY 2026 Application is not yet published.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_question_22.py
    'CY 2024-2025 is a CLOSED round being used as a proxy for the CY 2026 Allocation Application, which is not yet published; see ``_round_provenance``.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    'CY 2026':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'CY 2026 Allocation Application submitted to the CDFI Fund':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'CY 2026 CDE Certification Application submitted through AMIS':
        (),

    # streamlit_app/utils.py
    'CY 2026 will make 5 billion available".':
        (),

    # rendered_baseline/excel.txt
    "CY 2026 | Prepared: <RUNDATE> | Readiness Grade: B (84.9/100) — this tool's own unsourced house heuristic, not a CDFI Fund evaluation":
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    'Carried as the rendered string because the note states it as prose, and it is the one CY 2026 figure the NOAA settles; every OTHER round-specific figure in this package is still CY 2024-2025 and ``RECHECK_ITEMS`` still says so.':
        (),

    # rendered_baseline/pdf.txt
    'Distress Level Commitments Item Value QEI in Deep Distress Tracts (a share of QEI, not of QLICIs — see the basis note below) 52.2% QEI in Severely Distressed Tracts, Deep Distress included (a share of QEI, not of QLICIs — see the basis note below) 85.3% — of which severely distressed but not also deep 33.1% QEI in LIC (Standard Eligible) Tracts 14.7% QEI in NMTC Native Areas (CDE-declared, not verified by this tool) 5.9% QEI in High Migration Rural (HMR) Tracts 12.7% BASIS NOTE — the CDFI Fund\'s two distress commitments are measured on QLICIs, not on QEI Question 25 of the CY 2024-2025 NMTC Allocation Application (printed pp. 38-41) sets both commitments, and both are measured on QLICIs — specifically on QLICIs "in terms of aggregate dollar amounts", tested for each QLICI.':
        (),

    # rendered_baseline/pdf.txt
    'Dominant Sector Affordable Housing Total Jobs to Be Created 532 Sector Diversity Score 93.8/100 QEI Deployment Strategy and Timeline Great Lakes Regional Capital CDE, LLC targets a CY 2026 award.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'Every other CY 2026 date named above is already determined.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'Every round-specific citation in this package names the **CY 2024-2025** NMTC Allocation Application, and names it the way you name a live instrument.':
        (),

    # rendered_baseline/pdf.txt
    'Executive Summary Great Lakes Regional Capital CDE, LLC respectfully requests $70.0 million in New Markets Tax Credit allocation for CY 2026.':
        (),

    # rendered_baseline/word.txt
    'FTR| | Great Lakes Regional Capital CDE, LLC — NMTC CY 2026 Application | CONFIDENTIAL':
        (),

    # rendered_baseline/word.txt
    'Great Lakes Regional Capital CDE, LLC requests $70.0 million in New Markets Tax Credit allocation for CY 2026.':
        (),

    # rendered_baseline/markdown.txt
    'Great Lakes Regional Capital CDE, LLC respectfully requests $70.0MM in New Markets Tax Credit allocation for application round CY 2026.':
        (),

    # rendered_baseline/markdown.txt
    # rendered_baseline/word.txt
    'Great Lakes Regional Capital CDE, LLC targets a CY 2026 award.':
        (),

    # rendered_baseline/excel.txt
    'Great Lakes Regional Capital CDE, LLC | CY 2026 | Generated <RUNDATE>':
        (),

    # rendered_baseline/pdf.txt
    'Great Lakes Regional Capital CDE, LLC — NMTC CY 2026 Application | CONFIDENTIAL':
        (),

    # rendered_baseline/pdf.txt
    'Great Lakes Regional Capital CDE, LLC — NMTC CY 2026 | CONFIDENTIAL':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'It is set by the NOAA, it is not a figure this tool computes, and nothing in this document moves it.':
        (),

    # nmtcapp/renderers/_methodology.py
    'It said only that the CY 2026 NOAA was unpublished.':
        (),

    # rendered_baseline/pdf.txt
    "NEW MARKETS TAX CREDIT ALLOCATION APPLICATION Great Lakes Regional Capital CDE, LLC Application Round: CY 2026 Requested NMTC Allocation: $70,000,000 Preparation Date: <RUNDATE> Readiness Assessment: Grade B — 84.9/100 (this tool's own unsourced house heuristic, not a CDFI Fund evaluation) Contact: Dana Okonkwo | dokonkwo@greatlakesregional.example.org | 216-555-0142 CONFIDENTIAL — Prepared for CDFI Fund Review Only | Do Not Distribute Without CDE Authorization":
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'Neither route is still open: the AMIS window closed on August 31, 2026, and the as-of date the NOAA sets, September 15, 2026, has arrived.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'Neither route is still open: the AMIS window closed on {}, and the as-of date the NOAA sets, {}, has arrived.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'Non-Metropolitan county designations under the CY 2026 NOAA follow OMB Bulletin 20-01, applied using 2020 census tracts.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'Provenance: the CY 2026 NOAA is Federal Register document 2026-18883, filed September 14, 2026 and published September 15, 2026; the absence of CY 2026 Application Materials was confirmed on September 14, 2026.':
        (("NOAA", True), ("APPLICATION", False)),

    # nmtcapp/renderers/_round_provenance.py
    'Provenance: the {} NOAA is Federal Register document {}, filed {} and published {}; the absence of {} Application Materials was confirmed on {}.':
        (("NOAA", True), ("APPLICATION", False)),

    # rendered_baseline/excel.txt
    'Question 25 of the CY 2024-2025 NMTC Allocation Application (printed pp. 38-41) sets both commitments, and both are measured on QLICIs — specifically on QLICIs "in terms of aggregate dollar amounts", tested for each QLICI.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'Recorded here because it is a CY 2026 fact this module is the right place to hold; it changes no figure in this package and is not rendered into the note.':
        (),

    # nmtcapp/core/application_round.py
    'Replacing "CY2025" with "CY 2026" would swap a false claim for an unverified one — a guess about the reader\'s own submission, rendered as fact, with nothing on the page to say it was guessed.':
        (),

    # nmtcapp/core/application_round.py
    'Running header/footer phrase — "NMTC CY 2026" or just "NMTC".':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'So the text below tells a CDE **what to re-check when CY 2026 publishes**, not that it cannot rely on anything.':
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'THE CY 2026 CDE CERTIFICATION CUTOFFS ARE SETTLED AND ONE OF THEM HAS ALREADY CLOSED.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'THE CY 2026 FACTS, AND WHERE THEY CAME FROM':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'THE CY 2026 ROUND HAS OPENED, BUT ITS APPLICATION HAS NOT: the CY 2026 NOAA IS PUBLISHED — Federal Register document 2026-18883, publication date September 15, 2026 — and it makes $5 billion available, with applications due 5:00 p.m. ET on November 10, 2026.':
        (("NOAA", True), ("APPLICATION", False)),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'THE ONLY CY 2026 DEADLINE YOU CAN STILL MISS IS THE APPLICATION DEADLINE: 5:00 p.m. ET on November 10, 2026.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'THE {} ROUND HAS OPENED, BUT ITS APPLICATION HAS NOT: the {} NOAA IS PUBLISHED — Federal Register document {}, publication date {} — and it makes {} available, with applications due {}.':
        (("NOAA", True), ("APPLICATION", False)),

    # nmtcapp/data/historical_awards.py
    'THIS IS A RECORD, NOT A FORECAST: neither the CDFI Fund nor this tool publishes an expected acceptance rate for any future round, and CY 2026 is a $5 billion single round.':
        (),

    # nmtcapp/renderers/_question_25.py
    'That is the right call and it is not the same as the instrument being current; see ``renderers/_round_provenance`` for the disclosure and for what a CDE must re-check when CY 2026 lands.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    "That the qualifying set is closed is this package's inference, not the NOAA's statement.":
        (),

    # nmtcapp/intelligence/recommendations.py
    "The CDFI Fund publishes no 'Special Targeting' criterion and no bonus points for it: the CY 2024-2025 NOAA sets out exactly two statutory priorities under IRC §45D(f)(2), worth ten additional points in total, and this tool scores both of them elsewhere.":
        (),

    # streamlit_app/pages/4_About_and_Methodology.py
    'The CDFI Fund publishes no percentage here, and its test is not a percentage at all.** Question 23 of the CY 2024-2025 Allocation Application (p.34) is a dropdown: *"Does the Applicant intend to use substantially all of the proceeds of its QEIs to make QLICIs in one or more businesses in which persons Unrelated to the Applicant hold the majority equity interest?':
        (),

    # streamlit_app/pages/4_About_and_Methodology.py
    'The CDFI Fund publishes no such criterion and no bonus points for it.** The CY 2024-2025 NOAA (89 FR 92283, 21 Nov 2024), section V.B(b), sets out the complete set of additional points under IRC §45D(f)(2): *"the CDFI Fund will ascribe additional points to entities that meet one or both of the statutory priorities"* — a DBC track record (up to five points) and Investments in Unrelated Entities (five points) — *"Thus, Applicants that meet the requirements of both priority categories can receive up to a total of ten additional points."* Two priorities, ten points, and both are scored separately under Priority Points below.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'The CY 2026 Allocation Application and its Application Materials are NOT YET PUBLISHED, so the instrument encoded here is still the CY 2024-2025 one.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py [#]
    'The CY 2026 NOAA, pinned to its Federal Register identity rather than to a page that can be re-edited underneath a citation.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    "The CY 2026 deadlines are Eastern Time deadlines, so answering with this machine's local date would be wrong by up to a day on the day it matters most.":
        (),

    # nmtcapp/data/schema.py [#]
    "The Fund's published threshold on distress targeting is SEVERE_DISTRESS_MIN_PCT (0.85) in nmtcapp/data/benchmark_thresholds.py, sourced to the CY 2024-2025 NMTC Allocation Application Review Process — use that one for anything a CDE submits, and cite the round it belongs to.":
        (),

    # nmtcapp/renderers/_round_provenance.py
    "The NOAA carries the allocation authority, the application deadline and the certification rule; it does NOT carry Question 25's ladder, Question 22's Non-Metropolitan bounds, Question 15's product-flexibility ladder or the Review Process thresholds.":
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    "The NOAA is verified against the Federal Register document named above; the ABSENCE of CY 2026 Application Materials was confirmed by this package's maintainer on this date.":
        (("APPLICATION", False),),

    # nmtcapp/renderers/_round_provenance.py
    'The NOAA states TWO eligibility routes.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'The NOAA\'s cure language carries "except, if necessary and at the request of the CDFI Fund", and it governs missing materials inside a SUBMITTED application -- a different object from the certification eligibility this paragraph is about.':
        (),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'The QEI issuance thresholds themselves are in the NOAA, Federal Register document 2026-18883; this tool neither computes them nor reproduces them.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'The QEI issuance thresholds themselves are in the NOAA, Federal Register document {}; this tool neither computes them nor reproduces them.':
        (),

    # nmtcapp/data/benchmark_thresholds.py [#]
    'The Review Process is a SUMMARY of how the Fund scores; the Allocation Application is the INSTRUMENT the Applicant fills in, and the sweep never opened it for this question.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'The earliest CY 2026 deadline that has NOT yet passed, or ``None``.':
        (),

    # streamlit_app/pages/1_Pipeline_Analyzer.py
    'The published CY 2024-2025 bar for full Community Outcomes credit is 85% of QLICIs in areas of higher distress (Allocation Application, Question 25(a)) — **a share of QLICIs, while the bars above are shares of QEI**.':
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    'The round is OPEN and the Application Materials can drop on any business day between now and the deadline; a horizon measured in months cannot catch that inside a window that is itself only eight weeks long.':
        (("NOAA", True), ("APPLICATION", False)),

    # nmtcapp/renderers/_round_provenance.py
    'The {} Allocation Application and its Application Materials are NOT YET PUBLISHED, so the instrument encoded here is still the {} one.':
        (("APPLICATION", False),),

    # nmtcapp/renderers/_question_25.py
    'They are also a summary, and the summary loses two things the **instrument** — the Allocation Application itself, Question 25 at printed pp. 38-41 — states plainly:':
        (),

    # streamlit_app/utils.py [#]
    'This line applied SAMPLE_APPLICATION_ROUND unconditionally, so a real upload got "CY 2026" asserted onto every generated document.':
        (),

    # streamlit_app/pages/2_Win_Alignment_Scorer.py [#]
    "This page names CY 2024-2025 four times -- in its title docstring, in the sentence under the heading, in the sidebar's Highly Qualified citation and in the sub-score disclosure -- and said nothing about that round being closed and awarded on 23 Dec 2025, or about CY 2026 at all.":
        (),

    # nmtcapp/intelligence/recommendations.py
    'This surface cited the CY 2024-2025 Review Process thirteen times on a single run and said nothing about that round being closed and awarded, or about CY 2026 at all.':
        (),

    # nmtcapp/sections/base.py [#]
    'This tool does not encode the real limits — the CY 2026 Application Materials are unpublished — so it must not state one.':
        (("APPLICATION", False),),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'This tool encodes the CY 2024-2025 NMTC Allocation Application, which is the most recent PUBLISHED Application and is closed and awarded (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'This tool encodes the {} NMTC Allocation Application, which is the most recent PUBLISHED Application and is {} (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'Those live in the Application Materials, which do not exist yet.':
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    'Through 1.6.1 this was one boolean named ``UPCOMING_MATERIALS_PUBLISHED`` covering both, and the pair came apart on 2026-09-15: the NOAA published, the Application did not.':
        (("NOAA", True), ("APPLICATION", False)),

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    "To be eligible to apply in CY 2026 an organization had EITHER to already be a certified CDE as of the NOAA's Federal Register publication date, September 15, 2026, OR to have submitted its CDE Certification Application through AMIS by 11:59 p.m. ET on August 31, 2026.":
        (("NOAA", True),),

    # nmtcapp/renderers/_round_provenance.py
    "To be eligible to apply in {} an organization had EITHER to already be a certified CDE as of the NOAA's Federal Register publication date, {}, OR to have submitted its CDE Certification Application through AMIS by {}.":
        (("NOAA", True),),

    # nmtcapp/renderers/_round_provenance.py
    'Two statements went past the NOAA and are gone:':
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    "WHETHER THE UPCOMING ROUND'S NOAA HAS PUBLISHED -- and, SEPARATELY, whether the Allocation Application has.":
        (),

    # nmtcapp/renderers/_round_provenance.py [#]
    'What a CDE must re-verify when CY 2026 materials appear.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    'What is left is arithmetic on two dates the NOAA does state: the AMIS window closed, and the as-of date has arrived.':
        (),

    # streamlit_app/utils.py [#]
    'What it names today is CY 2026 — its NOAA published 15 Sep 2026, applications due 10 Nov 2026, and the round a CDE using this tool would in fact enter.':
        (("NOAA", True),),

    # nmtcapp/renderers/_round_provenance.py [#]
    '``NOAA_PUBLICATION_DATE`` is an AS-OF date: it fixes whose certification counts, and no reader can act on it on the day.':
        (),

    # nmtcapp/renderers/_round_provenance.py
    '``UPCOMING_MATERIALS_PUBLISHED = False`` rendered the sentence "The CY 2026 Allocation Application and NOAA are NOT YET PUBLISHED".':
        (),

    # streamlit_app/utils.py [#]
    '``data/historical_awards`` records that "CY 2026 is a $5 billion single round" -- $5B is the national allocation authority competed in one round, across every applicant.':
        (),

    # nmtcapp/core/application_round.py
    '``noun`` preserves each renderer\'s own phrasing -- the Markdown builder says "for application round CY 2026" where Word and PDF say "for CY 2026".':
        (),

    # nmtcapp/core/application_round.py
    'allocation_round_clause("CY 2026") # \' for CY 2026\' allocation_round_clause("CY 2026", "application round ") # \' for application round CY 2026\' allocation_round_clause(None, "application round ") # \'\'':
        (),

    # nmtcapp/core/application_round.py
    'is_round_specified("CY 2026") # True':
        (),

}

#: Why a selected segment that DOES carry publication-status vocabulary still
#: asserts nothing about either constant. Required for every such ``()`` entry
#: above, and read by
#: ``test_a_non_claim_that_carries_status_vocabulary_is_argued_in_writing``.
NON_CLAIM_REASONS = {
    # nmtcapp/renderers/_round_provenance.py
    '**The CY 2024-2025 Application is not unreliable.** It is a real federal instrument, retrieved and hash-verified, and it is the best available basis for preparing a CY 2026 application.':
        "About the CITED round's reliability, not about publication. "
        "'available' here qualifies 'basis' — the best available BASIS "
        'for preparing a CY 2026 application — and no CY 2026 instrument '
        'is said to have published or not.',

    # streamlit_app/pages/4_About_and_Methodology.py
    '*Both instruments re-opened and text-extracted locally with pypdf on 2026-08-22 for the two citations added above — Review Process, 7pp, 187,497 bytes, SHA-256 `ad0dc777eab0dc8cf437d970418bcdbea8403eb99b79dd1662f4ce94eab98749`; Allocation Application, 142pp, 1,525,626 bytes, SHA-256 `0280c6bc7b35f6015e2c2b1be4b1c07b3864f2dcbaeadfbbbf8bded8de12834f`.':
        'A retrieval record for the two CY 2024-2025 PDFs, with their '
        "byte counts and SHA-256s. 're-opened' is a file being opened on "
        'this machine on 2026-08-22, not a round or an instrument '
        'becoming available.',

    # nmtcapp/renderers/_round_provenance.py [#]
    'Aggregate allocation authority the CY 2026 NOAA makes available.':
        'States WHAT FIGURE the NOAA carries — the aggregate allocation '
        "authority — not whether the NOAA has published. 'available' is "
        'the money the NOAA makes available to applicants, not the '
        "instrument's availability.",

    # nmtcapp/renderers/_word_helpers.py [#]
    'An 80-char cut with an ellipsis silently removed the tail of any long cell — including Section B\'s severe-distress row, whose value ended "…Review Process; the CY 2026 NOAA is not yet published)".':
        'A deliberate historical record of the 1.5.x Word truncation '
        'defect, which QUOTES the superseded rendered value verbatim in '
        "order to show what was being cut. The quoted text is 1.6.1's, "
        "not this release's claim; see QUOTED_HISTORY.",

    # streamlit_app/utils.py
    'CY 2026 will make 5 billion available".':
        "A quoted fragment of a sentence about the round's SIZE — $5 "
        'billion of allocation authority — reproduced to show the wording '
        "this module must not retype. 'available' is the money, and no "
        "instrument's publication is addressed.",

    # nmtcapp/renderers/_methodology.py
    'It said only that the CY 2026 NOAA was unpublished.':
        "TRUE AS HISTORY AND ONLY AS HISTORY: it reports what 1.5.0's "
        'one-sentence disclosure said, in the past tense, as the defect '
        "that release's successor fixed. Rewriting it would falsify the "
        'record; see QUOTED_HISTORY.',

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'Neither route is still open: the AMIS window closed on August 31, 2026, and the as-of date the NOAA sets, September 15, 2026, has arrived.':
        'About the two CDE-CERTIFICATION ELIGIBILITY ROUTES closing, not '
        "about publication. 'open' is a window for submitting a "
        'certification application; the NOAA is named only as the '
        'document that SETS the as-of date.',

    # nmtcapp/renderers/_round_provenance.py
    'Neither route is still open: the AMIS window closed on {}, and the as-of date the NOAA sets, {}, has arrived.':
        'The source template of the rendered sentence above, and it '
        'asserts the same thing: the two CDE-certification routes have '
        "closed. 'open' is the AMIS window, not an instrument's "
        'publication state.',

    # nmtcapp/data/historical_awards.py
    'THIS IS A RECORD, NOT A FORECAST: neither the CDFI Fund nor this tool publishes an expected acceptance rate for any future round, and CY 2026 is a $5 billion single round.':
        "Not about publication of a CY 2026 instrument. 'publishes' takes "
        "'an expected acceptance rate' as its object and the sentence's "
        "point is that nobody publishes one; 'CY 2026' names the round "
        'whose SIZE it states.',

    # nmtcapp/intelligence/recommendations.py
    "The CDFI Fund publishes no 'Special Targeting' criterion and no bonus points for it: the CY 2024-2025 NOAA sets out exactly two statutory priorities under IRC §45D(f)(2), worth ten additional points in total, and this tool scores both of them elsewhere.":
        'Not about publication of a CY 2026 instrument. The object of '
        "'publishes' is a SCORING CRITERION, and the NOAA it names is the "
        'CY 2024-2025 one. Neither constant is addressed.',

    # streamlit_app/pages/4_About_and_Methodology.py
    'The CDFI Fund publishes no percentage here, and its test is not a percentage at all.** Question 23 of the CY 2024-2025 Allocation Application (p.34) is a dropdown: *"Does the Applicant intend to use substantially all of the proceeds of its QEIs to make QLICIs in one or more businesses in which persons Unrelated to the Applicant hold the majority equity interest?':
        'Not about publication of a CY 2026 instrument. The object of '
        "'publishes' is a PERCENTAGE THRESHOLD, and the Allocation "
        'Application it names is the CY 2024-2025 one, quoted for its '
        'Question 23 wording.',

    # streamlit_app/pages/4_About_and_Methodology.py
    'The CDFI Fund publishes no such criterion and no bonus points for it.** The CY 2024-2025 NOAA (89 FR 92283, 21 Nov 2024), section V.B(b), sets out the complete set of additional points under IRC §45D(f)(2): *"the CDFI Fund will ascribe additional points to entities that meet one or both of the statutory priorities"* — a DBC track record (up to five points) and Investments in Unrelated Entities (five points) — *"Thus, Applicants that meet the requirements of both priority categories can receive up to a total of ten additional points."* Two priorities, ten points, and both are scored separately under Priority Points below.':
        'Not about publication of a CY 2026 instrument. The object of '
        "'publishes' is a SCORING CRITERION ('Special Targeting'), and "
        'the NOAA it cites is the CY 2024-2025 one at 89 FR 92283.',

    # nmtcapp/data/schema.py [#]
    "The Fund's published threshold on distress targeting is SEVERE_DISTRESS_MIN_PCT (0.85) in nmtcapp/data/benchmark_thresholds.py, sourced to the CY 2024-2025 NMTC Allocation Application Review Process — use that one for anything a CDE submits, and cite the round it belongs to.":
        "Not about publication of a CY 2026 instrument. 'published' "
        'modifies a THRESHOLD the Fund has already set, sourced to the CY '
        "2024-2025 Review Process; the sentence's subject is which "
        'constant a CDE should cite.',

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'The QEI issuance thresholds themselves are in the NOAA, Federal Register document 2026-18883; this tool neither computes them nor reproduces them.':
        "Locates a figure and disclaims computing it. 'issuance' belongs "
        "to 'Qualified Equity Investment issuance thresholds'; naming the "
        "NOAA's Federal Register document number is a citation, not an "
        'assertion about its publication state.',

    # nmtcapp/renderers/_round_provenance.py
    'The QEI issuance thresholds themselves are in the NOAA, Federal Register document {}; this tool neither computes them nor reproduces them.':
        'The source template of the rendered sentence above, asserting '
        'the same thing: where the QEI issuance thresholds live, and that '
        'this tool does not reproduce them. No publication state is '
        'asserted.',

    # nmtcapp/data/benchmark_thresholds.py [#]
    'The Review Process is a SUMMARY of how the Fund scores; the Allocation Application is the INSTRUMENT the Applicant fills in, and the sweep never opened it for this question.':
        'About which of two CY 2024-2025 documents a threshold should '
        'have been read from, and about a retrieval sweep that never '
        "opened the Allocation Application PDF. 'opened' is a file, not a "
        'round.',

    # streamlit_app/pages/1_Pipeline_Analyzer.py
    'The published CY 2024-2025 bar for full Community Outcomes credit is 85% of QLICIs in areas of higher distress (Allocation Application, Question 25(a)) — **a share of QLICIs, while the bars above are shares of QEI**.':
        "Not about publication of a CY 2026 instrument. 'published' "
        'modifies the CY 2024-2025 BAR (85% of QLICIs) that Question '
        "25(a) sets; the sentence's point is the QLICI/QEI denominator "
        'difference.',

    # rendered_baseline/excel.txt
    # rendered_baseline/markdown.txt
    # rendered_baseline/pdf.txt
    # rendered_baseline/word.txt
    'This tool encodes the CY 2024-2025 NMTC Allocation Application, which is the most recent PUBLISHED Application and is closed and awarded (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        'About the CITED round, not the upcoming one: it says the '
        'instrument this package encodes is the most recent PUBLISHED '
        'Application and that its round is closed and awarded. CY '
        "2024-2025's publication is not either constant's subject.",

    # nmtcapp/renderers/_round_provenance.py
    'This tool encodes the {} NMTC Allocation Application, which is the most recent PUBLISHED Application and is {} (it opened 19 Nov 2024, closed 29 Jan 2025, and was awarded 23 Dec 2025 with $10 billion in allocation authority).':
        'The source template of the rendered sentence above, asserting '
        'the same thing about the CITED round: it is the most recent '
        'PUBLISHED Application, and it is closed and awarded. Neither CY '
        '2026 constant is addressed.',

    # nmtcapp/renderers/_round_provenance.py [#]
    "WHETHER THE UPCOMING ROUND'S NOAA HAS PUBLISHED -- and, SEPARATELY, whether the Allocation Application has.":
        'Names what the two constants below RECORD — one for the NOAA, '
        'one separately for the Allocation Application — without stating '
        "either polarity. It is the field description, not the field's "
        'value.',

    # nmtcapp/renderers/_round_provenance.py [#]
    '``NOAA_PUBLICATION_DATE`` is an AS-OF date: it fixes whose certification counts, and no reader can act on it on the day.':
        'About what the date is FOR — fixing whose CDE certification '
        "counts — not about whether the NOAA published. 'publication' "
        "appears only inside the constant's own name.",

    # nmtcapp/renderers/_round_provenance.py
    '``UPCOMING_MATERIALS_PUBLISHED = False`` rendered the sentence "The CY 2026 Allocation Application and NOAA are NOT YET PUBLISHED".':
        'A historical record of the single boolean this module carried '
        'through 1.6.1, QUOTING the sentence that boolean rendered. The '
        'quoted text is superseded, and quoting it is the point; see '
        'QUOTED_HISTORY.',

}

#: See ``_MAX_QUOTED_HISTORY`` below. Segments that match the hard
#: assertion-shape backstop and are still ``()``, because each QUOTES a
#: superseded release rather than asserting anything about this one.
QUOTED_HISTORY = (
    'An 80-char cut with an ellipsis silently removed the tail of any long cell — including Section B\'s severe-distress row, whose value ended "…Review Process; the CY 2026 NOAA is not yet published)".',
    'It said only that the CY 2026 NOAA was unpublished.',
    '``UPCOMING_MATERIALS_PUBLISHED = False`` rendered the sentence "The CY 2026 Allocation Application and NOAA are NOT YET PUBLISHED".',
)


# ---------------------------------------------------------------------------
# THE FLOORS, MEASURED -- NOT GUESSED
#
# Measured on 2026-09-15 against this tree, by running ``selected()``:
#
#     179 selected occurrences
#     104 distinct segments
#     79 modules scanned (nmtcapp + streamlit_app, nothing excluded)
#     13,177 segments in the corpus in total
#
# Each floor sits BELOW its measurement so that deleting a sentence or two is
# not automatically red, and FAR above zero so that an empty corpus, a broken
# segmenter or a selector that stopped matching is. Rule j4: a scan that
# selects nothing must FAIL, because "no violations found" and "nothing was
# looked at" are the same green.
# ---------------------------------------------------------------------------

_MIN_SELECTED_OCCURRENCES = 130        # measured 179
_MIN_SELECTED_SEGMENTS = 75     # measured 104
_MIN_SOURCE_FILES = 55             # measured 79
_MIN_CORPUS_SEGMENTS = 9500           # measured 13,177

#: THE HARD BACKSTOP ON THE ``()`` CLASSIFICATION. ``()`` means "this segment
#: asserts nothing about either constant", and it is the one way a human could
#: wave the 1.6.2 defect through. So the sentence SHAPE of that defect is
#: written down, and no ``()`` entry may match it.
#:
#: THE ROUND WORD IS DECOUPLED FROM THE INSTRUMENT WORD (1.6.3 fix round). The
#: build round's version required ``CY 2026`` IMMEDIATELY BEFORE the instrument
#: word, so all three of these were selected by stage 1 and then escaped the
#: backstop -- they could have been waved through as ``()``:
#:
#:     The NOAA for CY 2026 is not yet published.
#:     The CY 2026 round's NOAA is not yet published.
#:     The CY 2026 Application is not yet published.
#:
#: and the third is a spelling THIS REPOSITORY ALREADY USES, at
#: ``renderers/_question_25``. The round token is now a lookahead over the
#: clause, the instrument is an alternation that includes a bare "Application",
#: and the status word is the same STEM-MATCHED vocabulary the rest of this
#: module uses, so "remains unpublished" and "has not been released" match
#: where ``\bpublished\b`` could not.
_ASSERTION_SHAPE = re.compile(
    r"(?=[^.;]{0,240}?" + re.escape(rp.UPCOMING_ROUND) + r")"
    r"[^.;]{0,240}?\b(?:NOAA|Allocation Application|Application Materials"
    r"|Application)\b"
    r"[^.;]{0,120}?\b(?:is|are|was|were|has|have|had|be|been|being"
    r"|remains?|stays?|appears?|appeared)\b"
    r"[^.;]{0,90}?(?:publish\w*|publicat\w*|releas\w*|issu\w*|\bavailab\w*)",
    re.IGNORECASE,
)

#: SEGMENTS THAT MATCH ``_ASSERTION_SHAPE`` AND ARE STILL ``()``, BECAUSE THEY
#: QUOTE A SUPERSEDED RELEASE RATHER THAN ASSERTING ANYTHING.
#:
#: This is the ONE exception to the hard backstop and it is deliberately
#: awkward: an entry costs a registry key, a written reason AND a line here,
#: and the list is capped. The alternative considered was rewriting the three
#: records so they no longer quote the sentence they are a record OF -- which
#: is what the build round's docstring proposed ("if comments are ever brought
#: into this corpus, that record has to be reworded first"). It was rejected:
#: a historical record that cannot quote what it records is not a record, and
#: ``renderers/_methodology``'s "It said only that the CY 2026 NOAA was
#: unpublished" is TRUE -- about 1.5.0, in the past tense, which is the whole
#: sentence. Deleting the quotation to satisfy a regex would make the suite
#: green by making the documentation worse.
#:
#: WHAT KEEPS THIS FROM BECOMING THE ESCAPE HATCH: every member is also a
#: ``()`` key with a >=60-character reason, the cap below is asserted, and
#: ``test_quoted_history_is_small_and_live`` fails if an entry stops matching
#: the shape -- i.e. if somebody parks a non-quotation here.
_MAX_QUOTED_HISTORY = 6

# ---------------------------------------------------------------------------

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


def _has_vocabulary(segment: str) -> bool:
    return bool(list(_STATUS_VOCABULARY.finditer(segment)))


# ---------------------------------------------------------------------------
# STAGE 1 -- COMPLETENESS
#
# The stage that catches the NEXT one. Everything here is about whether a
# sentence was SEEN, not about whether it is right.
# ---------------------------------------------------------------------------

def test_every_round_status_segment_is_classified(scan):
    """An unclassified segment about the upcoming round FAILS, quoting itself.

    THIS IS THE GATE 1.6.2 DID NOT HAVE, and the selector behind it is the
    thing 1.6.3's build round got wrong. Selection is on the SUBJECT: a segment
    that names ``rp.UPCOMING_ROUND`` is required to be classified whatever it
    says, so no spelling of the claim can keep a sentence out of this list.
    """
    unclassified = sorted(
        {(segment, label) for label, segment in scan
         if segment not in ROUND_STATUS_CLAIMS}
    )
    assert not unclassified, (
        f"{len(unclassified)} segment(s) about {rp.UPCOMING_ROUND} are not in "
        "ROUND_STATUS_CLAIMS.\n\n"
        "Each one names the upcoming round, or names one of its instruments in "
        "a context about it, and nothing in this suite has checked it against "
        f"{sorted(SUBJECT_CONSTANTS.values())}. CLASSIFY IT — add it as a key "
        "with the claims it makes, or with `()` if it asserts nothing about "
        "whether a CY 2026 instrument has published. MOST ENTRIES ARE `()` AND "
        "THAT IS CORRECT: the price of selecting on the subject instead of on "
        "the wording is that every sentence about the round gets read once.\n\n"
        + "\n\n".join(f"  {label}\n    {segment!r}"
                      for segment, label in unclassified)
    )


def test_every_registry_key_is_found_in_the_corpus(scan):
    """A registry entry matching nothing is a dead allowlist.

    Without this the registry only ever grows, and a reviewer cannot tell a
    live classification from a sentence that was deleted three releases ago.
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


def test_a_non_claim_that_carries_status_vocabulary_is_argued_in_writing():
    """``()`` PLUS a publication word costs a written argument.

    THE DIRECTION OF THE VOCABULARY LIST IS THE POINT. It is not consulted to
    decide whether a segment is looked at — the round token does that — so a
    spelling missing from ``_STATUS_VOCABULARY`` cannot hide a sentence. It is
    consulted only HERE, to make the ``()`` classification more expensive. A
    word added to the list can only turn a free ``()`` into one that needs an
    argument; a word missing from it leaves the segment selected, registered
    and read. The list can make this gate stricter and can never make it
    blinder, which is exactly what the build round's version could not say.

    A ``()`` segment with no status vocabulary at all needs no reason: there is
    nothing in it to argue about, and demanding sixty characters of prose for
    "Application Round:|CY 2026" would buy nothing and teach people to write
    filler.
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
        if not _has_vocabulary(segment):
            continue
        reason = NON_CLAIM_REASONS.get(segment, "")
        assert len(reason) >= 60, (
            "this segment is classified as asserting nothing about whether a "
            f"{rp.UPCOMING_ROUND} instrument has published, and it carries "
            "publication-status vocabulary. That is a reading, and it has to "
            "be argued rather than asserted. Add it to NON_CLAIM_REASONS:\n\n"
            f"    {segment!r}"
        )


def test_no_non_claim_hides_a_round_status_assertion():
    """The 1.6.2 sentence's SHAPE may never be classified as "asserts nothing".

    ``(The CY 2026 NOAA is not yet published.)`` matches ``_ASSERTION_SHAPE``,
    and so do the three restatements the build round's pattern missed — see the
    note on ``_ASSERTION_SHAPE``, where they are written out and
    ``test_the_assertion_shape_catches_the_restatements_it_missed`` runs them.
    This is what stops the escape hatch from becoming the way the defect comes
    back. No written reason buys an exemption; the only exemption is
    QUOTED_HISTORY, which is capped and separately tested.
    """
    hidden = sorted(
        segment for segment, claims in ROUND_STATUS_CLAIMS.items()
        if not claims
        and segment not in QUOTED_HISTORY
        and list(_ASSERTION_SHAPE.finditer(segment))
    )
    assert not hidden, (
        f"{len(hidden)} segment(s) classified as asserting nothing DO carry "
        f"the shape '<{rp.UPCOMING_ROUND} ... instrument> ... is/are ... "
        "publish/release...'. That is the exact shape of the sentence this "
        "gate exists for. Classify them with the claims they make:\n\n"
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


#: The sentence this package shipped, and the restatements of it that the
#: build round's ``_ASSERTION_SHAPE`` did not match. Written as literals on
#: purpose: they are the test's INPUT, not a claim the package makes, and they
#: are why this module's segments are read from the corpus rather than typed.
_SHAPE_MUST_MATCH = (
    "(The CY 2026 NOAA is not yet published.)",
    "The NOAA for CY 2026 is not yet published.",
    "The CY 2026 round's NOAA is not yet published.",
    "The CY 2026 Application is not yet published.",
    "The CY 2026 NOAA remains unpublished.",
    "The CY 2026 NOAA has not been released.",
    "The CY 2026 Allocation Application has not been issued.",
)
#: Sentences the backstop must NOT match, or legitimate `()` classifications
#: become impossible and the escape hatch stops existing.
_SHAPE_MUST_NOT_MATCH = (
    "The CY 2024-2025 NOAA is published.",
    "Aggregate allocation authority the CY 2026 NOAA makes available.",
    "Neither route is still open: the AMIS window closed on August 31, 2026.",
    "CY 2026 is a $5 billion single round.",
)


@pytest.mark.parametrize("sentence", _SHAPE_MUST_MATCH)
def test_the_assertion_shape_catches_the_restatements_it_missed(sentence):
    """F2: the round word and the instrument word are no longer adjacent.

    The build round's pattern was
    ``CY 2026\\s+(?:NOAA|Allocation Application|Application Materials)``, which
    required the two to touch. Three of the seven sentences below are the same
    claim with a word in between, and one of them is a spelling this repository
    already uses.
    """
    assert list(_ASSERTION_SHAPE.finditer(sentence)), (
        "_ASSERTION_SHAPE does not match a restatement of the sentence this "
        f"gate exists for, so that restatement could be waved through as `()`:"
        f"\n\n    {sentence!r}"
    )


@pytest.mark.parametrize("sentence", _SHAPE_MUST_NOT_MATCH)
def test_the_assertion_shape_does_not_swallow_everything(sentence):
    """A backstop that matches every sentence forbids the `()` classification.

    Stated as its own test because "make the regex wider" is the obvious
    response to the test above, and a pattern that matches the whole corpus
    would pass it while making the registry unmaintainable.
    """
    assert not list(_ASSERTION_SHAPE.finditer(sentence)), (
        "_ASSERTION_SHAPE matches a sentence that asserts nothing about a "
        f"{rp.UPCOMING_ROUND} instrument's publication, so no such sentence "
        f"could ever be classified `()`:\n\n    {sentence!r}"
    )


def test_the_status_vocabulary_is_not_vacuous():
    """The vocabulary adds failures, so it has to match something real.

    It cannot make this gate blind — nothing about selection consults it for a
    segment that names the round — but a pattern that matched nothing would
    silently switch off the written-reason requirement on every `()` entry.
    """
    matched = [segment for segment in ROUND_STATUS_CLAIMS
               if _has_vocabulary(segment)]
    assert len(matched) >= 20, (
        f"_STATUS_VOCABULARY matches {len(matched)} registry segment(s); 46 "
        "were measured on 2026-09-15. The pattern is broken, and a broken one "
        "makes every `()` entry free."
    )
    assert _has_vocabulary("The CY 2026 NOAA remains unpublished."), (
        "_STATUS_VOCABULARY does not match 'unpublished'. That is the exact "
        "defect this module was rewritten for: `\\bpublished\\b` cannot match "
        "inside `unpublished`, so the stem must be matched WITHOUT a leading "
        "word boundary."
    )


def test_quoted_history_is_small_and_live():
    """The one exemption from the hard backstop, kept small and kept honest."""
    assert QUOTED_HISTORY, (
        "QUOTED_HISTORY is empty, so test_no_non_claim_hides_a_round_status_"
        "assertion's exemption branch is never taken and this test guards "
        "nothing. Delete the exemption rather than leaving it unexercised."
    )
    assert len(QUOTED_HISTORY) <= _MAX_QUOTED_HISTORY, (
        f"{len(QUOTED_HISTORY)} segments are exempted from the assertion-shape "
        f"backstop; the cap is {_MAX_QUOTED_HISTORY}. This list is for records "
        "that QUOTE a superseded release. If it is growing, the escape hatch "
        "has become the classification."
    )
    for segment in QUOTED_HISTORY:
        assert segment in ROUND_STATUS_CLAIMS, (
            f"exempted segment is not in the registry at all: {segment!r}"
        )
        assert not ROUND_STATUS_CLAIMS[segment], (
            "an exempted segment carries claims, so the exemption does "
            f"nothing and says the opposite of the classification: {segment!r}"
        )
        assert len(NON_CLAIM_REASONS.get(segment, "")) >= 60, (
            "an exemption from the hard backstop costs a written reason as "
            f"well as a `()`: {segment!r}"
        )
        assert list(_ASSERTION_SHAPE.finditer(segment)), (
            "this segment is exempted from the assertion-shape backstop but "
            "does not match the shape, so the exemption is parking something "
            f"the backstop was never going to catch: {segment!r}"
        )


# ---------------------------------------------------------------------------
# ANTI-VACUITY. Rule j4: nothing here may pass by having looked at nothing.
# ---------------------------------------------------------------------------

def test_the_scan_reads_a_real_corpus():
    """The corpus, the segmenter and the source walk all still work.

    Stated as separate floors because they fail for different reasons, and a
    single "selected nothing" red cannot tell them apart: a missing baseline, a
    segmenter that stopped splitting, and a source walk pointed at the wrong
    tree all look identical from the selection count.
    """
    for fmt in BASELINE_FORMATS:
        path = os.path.join(BASELINE_DIR, fmt + ".txt")
        assert os.path.exists(path), f"no rendered baseline for {fmt}: {path}"

    assert os.path.isdir(STREAMLIT_ROOT), (
        f"streamlit_app/ is not at {STREAMLIT_ROOT}. It ships in the sdist and "
        "release.yml's sdist job copies it out of the tarball, so this path "
        "resolves in both places — a missing directory means the layout moved "
        "and this scan would silently stop reading a surface that carried a "
        "false round-status comment on the day the round opened."
    )

    files = source_files()
    assert len(files) >= _MIN_SOURCE_FILES, (
        f"the source walk found {len(files)} modules under {SOURCE_ROOT} and "
        f"{STREAMLIT_ROOT}, below the {_MIN_SOURCE_FILES} floor "
        f"(79 measured). It is pointed at the wrong tree, or the "
        "package moved."
    )

    total = sum(len(segments(text)) for _label, text in corpus())
    assert total >= _MIN_CORPUS_SEGMENTS, (
        f"the corpus segmented into {total} sentences, below the "
        f"{_MIN_CORPUS_SEGMENTS} floor (13,177 measured). The segmenter is "
        "broken, and a broken segmenter selects nothing and passes stage 1."
    )


def test_the_scan_selects_at_least_the_measured_floor(scan):
    """A stage-1 scan that selects ZERO segments must FAIL, not pass."""
    assert len(scan) >= _MIN_SELECTED_OCCURRENCES, (
        f"the scan selected {len(scan)} occurrence(s) about "
        f"{rp.UPCOMING_ROUND}, below the {_MIN_SELECTED_OCCURRENCES} floor "
        f"(179 measured on 2026-09-15). Either the corpus shrank, or the "
        "selector stopped matching — and a selector that matches nothing makes "
        "every other test in this module pass on an empty set."
    )
    distinct = {segment for _label, segment in scan}
    assert len(distinct) >= _MIN_SELECTED_SEGMENTS, (
        f"the scan selected {len(distinct)} distinct segment(s), below the "
        f"{_MIN_SELECTED_SEGMENTS} floor (104 measured)."
    )


def test_the_corpus_reaches_every_surface_it_claims_to(scan):
    """Baselines, package source and the Streamlit app each contribute.

    A gate satisfied by one surface is not a gate. The 1.6.2 sentence rendered
    in all four formats; the four sentences the BUILD round's selector could
    not see were in package source and in ``streamlit_app/``, which was not in
    the corpus at all.
    """
    labels = {label for label, _segment in scan}
    for fmt in BASELINE_FORMATS:
        assert f"rendered_baseline/{fmt}.txt" in labels, (
            f"nothing about {rp.UPCOMING_ROUND} was selected from "
            f"rendered_baseline/{fmt}.txt. The round-provenance note renders "
            "on all four surfaces; a format contributing none means this gate "
            "is not reading it."
        )
    assert any(label.startswith("nmtcapp/") for label in labels), (
        "no package source module contributed a segment."
    )
    assert any(label.startswith("streamlit_app/") for label in labels), (
        "no streamlit_app module contributed a segment, so the surface that "
        "said the round was 'not yet open' on the day it opened is not being "
        "read."
    )
    assert any(label.endswith(" [#]") for label in labels), (
        "no `#` comment contributed a segment. A false comment is a false "
        "claim in shipped source; four of the sentences that provoked this "
        "rewrite were comments."
    )


def test_every_baseline_format_contributes_a_claim(scan):
    """And each rendered format must contribute a CLASSIFIED CLAIM, not just
    a mention. A format that only ever yields `()` is one stage 2 never reads.
    """
    claimed = {
        label for label, segment in scan
        if ROUND_STATUS_CLAIMS.get(segment)
    }
    for fmt in BASELINE_FORMATS:
        label = f"rendered_baseline/{fmt}.txt"
        assert label in claimed, (
            f"no classified round-status CLAIM was found in {label}."
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


def test_the_authority_module_is_in_the_corpus():
    """``_round_provenance.py`` is SCANNED now, not excluded.

    The build round excluded it as "the authority", on the stated grounds that
    "its text still reaches this gate through all four rendered baselines".
    That was false for the module's DOCSTRING, which renders nowhere and
    carried round-status prose. This test fails if the exclusion comes back by
    the module being moved out from under the walk.
    """
    path = os.path.join(SOURCE_ROOT, "renderers", "_round_provenance.py")
    assert path in source_files(), (
        f"{path} is not in the source walk. The module that DEFINES the two "
        "constants also states them in prose, in a docstring that renders "
        "nowhere; leaving it unscanned is how its own sentences go unread."
    )


# ---------------------------------------------------------------------------
# STAGE 2 -- CORRECTNESS
# ---------------------------------------------------------------------------

def test_stage_two_has_something_to_adjudicate():
    """Stage 2 parametrises over the registry; an empty one is a silent pass."""
    assert ROUND_STATUS_CLAIMS, "the registry is empty"
    assert len(_CLAIM_ITEMS) >= 20, (
        f"stage 2 adjudicates {len(_CLAIM_ITEMS)} claim(s); 31 "
        "were measured on 2026-09-15. Below this the parametrisation is not "
        "covering the note."
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
        f"a sentence in the shipped package says the {rp.UPCOMING_ROUND} "
        f"{subject} {'IS' if asserts_published else 'IS NOT'} published, and "
        f"_round_provenance.{constant} is {actual}.\n\n"
        f"    {segment!r}\n\n"
        "One of the two is wrong and they are in different files, which is "
        "precisely how 1.6.2 shipped a document that said the CY 2026 NOAA "
        "was unpublished on page 8 and published on page 26. Fix the sentence "
        "in its own module, regenerate tests/rendered_baseline/ if it renders, "
        "and update this registry entry in the same commit."
    )
