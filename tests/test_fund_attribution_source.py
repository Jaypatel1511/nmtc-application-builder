"""THE source-side Fund-attribution gate: docs/ and the Streamlit tables, which no gate reached.

WHY THIS AND NOT test_attributed_claims.py

tests/test_attributed_claims.py renders four disjoint scenarios in four formats
and audits the RENDERED CORPUS. That is the right shape for anything a CDE
files. It has one blind spot, and the 1.2.2 sweep walked straight into it:

  a claim that renders on NO fixture is invisible to it.

Both claims 1.2.2 was opened to close --- the Product Flexibility sentence at
intelligence/recommendations.py:232 and the Unrelated Entities sentence at
:622 --- fire only when their sub-score is below a cut (``pf < 8``, ``ue < 4``).
No packaged fixture scores that low. Neither sentence appears anywhere in
tests/rendered_baseline/, so neither the invariance gate, the attribution gate,
nor the D1 baseline had ever seen either one. They were live on PyPI and on the
published docs site for the whole 1.2.1 cycle regardless.

WHY THIS AND NOT test_qlici_basis.py::_scanned_trees

_scanned_trees() carries a contract --- "trees present in BOTH a checkout and
the sdist" --- which is why it resolves ``nmtcapp`` through the imported package
and hard-asserts isdir() on each tree. docs/ cannot join that set: MANIFEST.in
line 88 is ``prune docs``, verified by building the tarball (0 entries under
docs/, and no mkdocs.yml either). Adding docs/ to _scanned_trees() would turn a
CORRECT sdist into a red release job. So the docs half lives here, with its own
presence rule, and _scanned_trees() keeps its one honest invariant.

WHAT COUNTS AS AN ATTRIBUTION

Two detectors, because the defect has two shapes and only one of them contains
the word "Fund":

  D-A  PROSE. A string that names an authority AND makes a claim about what it
       does, requires, awards, publishes or expects. This is the shape at
       recommendations.py:232/:326/:504 and validation/eligibility_check.py:71.

  D-B  TABULAR. A markdown table row stating a threshold. The methodology
       tables state the Fund's scoring criteria and are introduced as such, so
       the attribution is carried by the table, not the row --- and the row is
       where the number is. docs/reference/methodology.md:42 is

           | Product Flexibility | 10 | 50%+ below-market rate OR 5+ indicia ... |

       which contains no authority token at all. A detector keyed on "CDFI
       Fund" misses it, and missing it is exactly how the claim survived a
       release whose entire subject was sweeping that claim's siblings.

FAILS CLOSED, ON EACH HALF SEPARATELY

  * The .py half runs everywhere. Both trees must exist and yield files.
  * The docs half runs when mkdocs.yml is present, which is the CHECKOUT
    marker: the tarball ships neither docs/ nor mkdocs.yml, so their joint
    absence is the sdist and is fine. Deleting docs/ from a checkout leaves
    mkdocs.yml behind and therefore FAILS, which is the property that matters
    --- an absent directory must never be indistinguishable from a clean one.
  * Every scan asserts a floor on files seen and on matches found. A gate that
    can pass while scanning nothing is the vacuity this package keeps shipping.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

ALLOWLIST_PATH = os.path.join(
    os.path.dirname(__file__), "fund_attribution_allowlist.txt"
)

#: Floors. Deliberately well below the true counts (70 .py files, 15 docs
#: files, 36 table rows at 1.2.2) so ordinary growth does not trip them, and
#: well above zero so a broken walk does.
MIN_PY_FILES = 40
MIN_DOCS_FILES = 8
MIN_MATCHES = 25

#: Adjudicated-but-unfixed false Fund attributions, counted as DISTINCT
#: DEFECTS and not as entries. Every defect lives on one to six surfaces at
#: once --- the Product Flexibility sentence alone rendered in
#: docs/reference/methodology.md twice, in the Streamlit About page twice and
#: in intelligence/recommendations.py twice --- so an entry count would move
#: whenever a sentence was duplicated or deleted and would say nothing about
#: whether a false attribution had been found or fixed. A DEFECT entry's
#: citation therefore opens with its defect tag, and this pin counts the
#: distinct tags.
#:
#: 6 -> 0 IN 1.2.2 ROUND 2. Round 1 ruled D1-D6 against the primary source and
#: shipped the gate WITHOUT fixing any of them; all six were live on PyPI and
#: on the published docs site for the whole 1.2.1 cycle. Round 2 fixed all six
#: across their 20 surfaces, so every DEFECT entry has been reclassified to the
#: kind that states its true provenance --- CITED where the corrected text
#: quotes a document and page, HOUSE where the number is this tool's own.
#:
#: ZERO IS NOT A WEAKER PIN THAN SIX. The assertion is equality, so a seventh
#: defect appearing tomorrow makes len(tags) == 1 and fails exactly as an
#: eighth would have failed against 6. What the pin forbids is a DEFECT entry
#: being added without someone deliberately raising this number, and it forbids
#: that just as firmly at 0. Proved by planting a DEFECT row and observing the
#: failure; see CHANGELOG.md for the run.
#:
#: WHAT ZERO DOES NOT MEAN, AND THE 1.3.0 FINDING THAT ESTABLISHED IT.
#:
#:     EXPECTED_DEFECTS = 0 means "no false attributions among those RULED".
#:     It does not mean "none remain". A gate is exactly as good as the
#:     DOCUMENT its allowlist was ruled against.
#:
#: This is not a caveat, it is a measured result. The 1.2.2 sweep ruled every
#: entry below against the CY 2024-2025 NMTC Program *Review Process* — a
#: seven-page summary of how the CDFI Fund scores an application — and the pin
#: went 6 -> 0 honestly on that basis. In 1.3.0 the *Allocation Application*
#: was retrieved for the same question and two CITED entries turned out to be
#: correct quotations of an incomplete source: the 85% is denominated in
#: aggregate QLICI DOLLARS over a one-of-five / two-of-seven area test, and the
#: 20% is not a bar at all but the top rung of a 0/5/10/15/20 ladder over four
#: area types. Both errors instructed a CDE to UNDERSTATE its own qualifying
#: share to a federal agency, and both sat under a green gate reading zero.
#:
#: Neither was re-tagged DEFECT, because DEFECT means "the authority does not
#: state it" and the Review Process does state both sentences. They were
#: re-ruled CITED against the Application instead, with the correction carried
#: in the rendered text. So the count stayed at 0 through a round that found
#: two real false-negative defects — which is the point of writing this here.
#:
#: THE RULE THIS LEAVES BEHIND: a summary document is a safe source for how the
#: Fund SCORES and an unsafe source for what the Applicant is asked to COMMIT
#: TO, because the thing the Applicant fills in is the Application. Every
#: citation below that names the Review Process for a commitment, a
#: percentage, or a list of areas is owed a check against the Application. The
#: 1.3.0 sweep of all such citations is recorded in CHANGELOG.md.
EXPECTED_DEFECTS = 0
#: Matched anywhere in the citation, not anchored: each citation opens with
#: the location the claim was first found at, and the tag follows it.
_DEFECT_TAG = re.compile(r"\b(D[1-9]\d*):")

KINDS = {"CITED", "HOUSE", "LABEL", "PLACEHO", "DISCLAIM", "AUDIENCE",
         "SELFREP", "NARRATIVE", "DEFECT"}


# ---------------------------------------------------------------------------
# Detector A --- prose attributions
# ---------------------------------------------------------------------------

#: Naming one of these is what makes a claim an ATTRIBUTION rather than an
#: opinion. "the Fund" is included deliberately: three of the seven defects
#: found in the 1.2.2 sweep use it in a continuation sentence after naming the
#: CDFI Fund in full one sentence earlier.
AUTHORITIES = (
    "cdfi fund", "review process", "allocation application", "noaa",
    "the fund", "§45d", "45d(", "1.45d-1", "irc §", "treas. reg", "cfr",
    # IMPLICIT. "Full credit" and "priority points" name no authority and are
    # attributions anyway: there is no credit in this package other than the
    # Fund's scoring, and every Recommendation carrying one also carries a
    # citation= field pointing at the Review Process. Without these two,
    # intelligence/recommendations.py:622 --- "Full credit requires committing
    # substantially all (90%+) QEIs ..." , the sentence S2 was opened to close
    # --- names nobody and slips the gate entirely.
    "full credit", "priority points",
    # IMPLICIT, ADDED 1.2.2 ROUND 2. "Highly Qualified" is the CDFI Fund's OWN
    # NAME for its own gate, so a sentence stating a bar "required for Highly
    # Qualified status" attributes that bar to the Fund as surely as one saying
    # so in words. "Top Tier" earns its place for the opposite reason: it is
    # this package's INVENTED tier, and a sentence that states cut points for it
    # is making a provenance claim by omission.
    #
    # NOT THEORETICAL. Round 2 added these after finding TWO live D4 surfaces
    # that round 1 had not listed and the gate could not see, both invisible
    # precisely because they name no authority:
    #
    #   streamlit_app/pages/2_Win_Alignment_Scorer.py --- "**Top Tier gate:**
    #     95+ aggregate AND 45+ in each section", rendered directly beneath
    #     "**Highly Qualified gate:** 85+ ...", in the same weight and shape, so
    #     a CDE reads a matched pair of Fund gates. Only one of them was.
    #
    #   intelligence/win_probability.py --- "Top Tier (100/100) ... High
    #     probability of Phase 2 advancement; award may approach the maximum
    #     requested." An AWARD PREDICTION, resting on an invented gate, in a
    #     package whose docs disclaim predicting selection.
    #
    # Measured before adopting: 9 further strings become adjudicated, all nine
    # genuine statements of the gating thresholds. D4's true surface count is
    # therefore SIX, not the four round 1 recorded.
    "highly qualified", "top tier",
)

#: A claim about what the authority DOES. Jay's rule for the 1.2.2 sweep: "A
#: claim about what the Fund does, requires or awards is an attribution whether
#: or not a number follows it." Bare names --- "CDFI Fund NMTC Eligibility
#: Table", the confidentiality banner, a link in a Sources list --- carry no
#: verb and are not attributions; they are why this list exists rather than
#: matching on the authority token alone.
CLAIM_VERBS = (
    "require", "award", "expect", "publish", "state", "uses ", "use the",
    "look for", "looks for", "value", "ask", "hold", "evaluate", "score",
    "flag", "designate", "defin", "prefer", "consider", "credit for",
    "full credit", "threshold", "must ", "need", "allow", "grant", "weight",
    "rank", "gate", "commit", "gives", "give ", "assess", "bar for",
)


# ---------------------------------------------------------------------------
# Detector B --- tabular thresholds
# ---------------------------------------------------------------------------

#: A number that functions as a bar. "10" alone is a max-points column and not
#: a threshold; "50%", "5+", ">= 45" are.
_THRESHOLD = re.compile(r"\d\s*%|≥|≤|>=|<=|\bpts\b|\bpoints\b|\d+\+")

#: A markdown table separator row (|---|---|) states nothing.
_SEPARATOR = re.compile(r"^\|[\s\-:|]+\|$")

#: X3. Detector B fires only inside a table that DECLARES itself a statement of
#:     the application's scoring criteria, identified by its header row. Without
#:     this the detector also matched this tool's own component-weight table
#:     (docs/workflow/pipeline-analysis.md:61-66, six rows of internal scoring
#:     weights) and an API field constraint (`expected_jobs_created` ... must be
#:     >= 0). Neither attributes anything to anyone, and burying the four real
#:     tabular defects among them is how a list stops being reviewed.
#:     A header token must identify a HEADER. "criterion |" was in this tuple
#:     and matched any DATA row whose first cell ended in the word — the
#:     planted-defect proof for this round wrote
#:     "| Planted Criterion | 5 | 60%+ of QLICIs in planted areas |",
#:     which the gate classified as a header and skipped, passing green on a
#:     deliberately planted false attribution. It was redundant as well as
#:     wrong: every header it was meant to catch ("| Criterion | Max points |
#:     Key threshold |") already carries two other tokens here.
_CRITERIA_TABLE_HEADER = (
    "key threshold", "section minimums", "max points", "sub-criterion",
    "aggregate base score",
)


# ---------------------------------------------------------------------------
# Narrowings. Recorded, not deleted --- deleting a trigger narrows the gate
# silently and forever; a narrowing is reviewable and has to be argued past.
# ---------------------------------------------------------------------------

#: X1. A clause that DISCLAIMS an attribution is the opposite of making one.
#:     "(market assumption, not a CDFI Fund parameter)" names the Fund in order
#:     to deny it. Counting these would push the gate toward rewarding silence
#:     over disclosure, which is the failure this package spent 1.2.1 undoing.
_DISCLAIMERS = (
    "not a cdfi fund", "publishes no", "not a federal", "no such weighting",
    "unsourced house heuristic", "house heuristic", "house band",
    "this tool's own", "not affiliated with", "does not publish",
    "not calibrated against award data", "does not predict an award",
    "is not a cdfi fund threshold", "no cdfi fund eligibility data",
    "not tool-verified", "refusing to use it",
)

#: X1-EXCEPT. A disclaimer that ALSO asserts a Fund figure in the same breath
#:     is still making the assertion. validation/eligibility_check.py:96 is the
#:     paradigm: it correctly disclaims this tool's house band AND states "The
#:     published CY 2024-2025 severe-distress bar for full credit is 85% of
#:     QLICIs" in the same string. Exempting it on the strength of the
#:     disclaimer would hide the half that is a Fund claim. Precedent:
#:     _AFFIRMS_A_FUND_BAR in tests/test_qlici_basis.py.
_AFFIRMS_ANYWAY = (
    "the published", "the fund's own", "the cdfi fund's own", "fund's bar",
    "bar for full credit", "commitment is measured", "asks for",
)

#: X1-EXCEPT, SECOND LIMB, added in 1.2.2 round 2. A token list could not keep
#: up. Round 2 rewrote six defect surfaces into disclosures that DISCLAIM this
#: tool's threshold and QUOTE the Fund's real one in the same string, and every
#: one of them slipped X1 on a token the disclaimer list already held --- two of
#: them by accident, because adding the words "publishes no" to the Streamlit
#: Community Outcomes and Priority Points blobs silently exempted blobs that had
#: been ADJUDICATED the release before. A round whose subject is unreviewed Fund
#: quotations must not stop reviewing its own.
#:
#: The general rule, rather than more tokens: A STRING THAT CITES A DOCUMENT
#: LOCATION IS ASSERTING WHAT THAT DOCUMENT SAYS. A page, a question number, a
#: statute or regulation section, a Part/Step, or a Federal Register cite is a
#: claim of provenance, and a claim of provenance is reviewable no matter how
#: much disclaiming surrounds it. Measured before adopting: 8 strings move from
#: exempt to adjudicated, and all 8 are Fund quotations.
_CITES_A_LOCATION = re.compile(
    r"\bpp?\.\s?\d|\bquestion\s+\d|§|\bpart\s+i{1,3}\b|\b\d+\s+fr\s+\d{4,}|"
    r"\bstep\s+\d"
)


def _is_disclaimer(text: str) -> bool:
    low = text.lower()
    if not any(d in low for d in _DISCLAIMERS):
        return False
    if any(a in low for a in _AFFIRMS_ANYWAY):
        return False
    return not _CITES_A_LOCATION.search(low)


#: X2. STATED SCOPE LIMIT. This gate's subject is a BAR attributed to an
#:     authority --- a threshold, a share, a points award, a "full credit"
#:     condition. Descriptive prose that names the Fund without stating a bar
#:     ("the CDFI Fund revises scoring criteria between rounds", "derived from
#:     CDFI Fund award announcements") is NOT matched here. That is a decision,
#:     not an oversight: 149 strings name an authority, 100+ of them state no
#:     bar, and an allowlist of 149 hand-written citations is one nobody reads
#:     --- which is the failure mode that put six fabricated citations into the
#:     sibling allowlist in the first place. Rendered descriptive claims remain
#:     covered by tests/test_attributed_claims.py over the four scenarios.
#:     Widening this to bare descriptive prose is a deliberate future decision.
_BAR = re.compile(
    # "N bonus points" / "N additional points" / "N pts": allow the qualifier
    # between the number and the noun. Without the gap, the Special Targeting
    # sentence at recommendations.py:504 --- "awards up to 5 bonus points" ---
    # states a bar the regex cannot see.
    r"\d\s*%|\d[\w\s-]{0,14}\b(?:points?|pts)\b|\bfull credit\b|"
    r"\bsubstantially all\b|\bat least\b|\bminimum\b|\bnear-?100\b|\d\s*\+"
)


def _is_prose_attribution(text: str) -> bool:
    low = text.lower()
    if not any(a in low for a in AUTHORITIES):
        return False
    if not any(v in low for v in CLAIM_VERBS):
        return False
    if not _BAR.search(low):
        return False
    return not _is_disclaimer(text)


def _table_rows(text: str):
    """Yield (line_offset, row) for threshold rows of a criteria table (X3).

    Runs over a WHOLE text --- a .md file, or one .py string literal holding a
    markdown table --- because the "is this a criteria table" state lives in
    the header row and has to survive to the rows beneath it. Feeding this one
    line at a time resets that state on every call and silently matches
    nothing, which is precisely how the first draft of this gate missed
    docs/reference/methodology.md:42, the line 1.2.2 was opened to close.
    """
    in_criteria_table = False
    for offset, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if not line.startswith("|"):
            in_criteria_table = False
            continue
        low = line.lower()
        if any(h in low for h in _CRITERIA_TABLE_HEADER):
            in_criteria_table = True
            continue
        if _SEPARATOR.match(line):
            continue
        if in_criteria_table and _THRESHOLD.search(line):
            yield offset, line


def _normalise(clause: str) -> str:
    """Collapse to attributive shape: lowercase, digits -> N, whitespace flat.

    Keys the allowlist on the CLAIM, so the same sentence duplicated into
    docs/reference/methodology.md and streamlit_app/pages/4_About_and_
    Methodology.py shares ONE reviewable entry --- and the dead-entry test then
    keeps that pair honest. The 1.2.2 sweep found every one of the seven
    defects living on two or three surfaces at once; a location-keyed list
    would have recorded them as twenty-one unrelated problems.
    """
    s = " ".join(clause.split()).lower()
    s = re.sub(r"\d[\d,._]*", "N", s)
    return s.strip(" |-—*#>")


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _string_units(tree):
    """Yield (text, lineno) for every string a reader sees as ONE sentence.

    An f-string is NOT one Constant. ``f"... {pct}+ of NMTC pipeline ..."``
    parses to a JoinedStr whose Constant parts are split at every interpolation,
    so the authority and the bar land in different nodes and a scanner keyed on
    either finds a fragment that says nothing. That is not hypothetical: it is
    intelligence/recommendations.py:326, "The CDFI Fund requires {70%}+ of NMTC
    pipeline ... AND {90%}+ of prior allocation deployed on schedule" --- one of
    the seven defects this round ruled, and invisible to the first draft of this
    gate. Interpolations render as "N" so the reconstructed sentence normalises
    the same way a literal digit does.

    Constants inside a JoinedStr are consumed here and not yielded again, so a
    fragment cannot also be scanned (and allowlisted) on its own.
    """
    consumed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    consumed.add(id(v))
                    parts.append(v.value)
                else:
                    # A DIGIT, not a letter. Every threshold in this package
                    # reaches its sentence through interpolation
                    # (f"...{_DEPLOYMENT_PCT_TEXT}+ of prior allocation..."),
                    # so a non-numeric placeholder leaves the reconstructed
                    # sentence with no bar for _BAR to find and the whole
                    # f-string reconstruction buys nothing. _normalise maps
                    # digits to N afterwards, so the key is unaffected.
                    parts.append("0")
            yield "".join(parts), node.lineno
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in consumed):
            yield node.value, node.lineno


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _py_trees() -> list:
    """nmtcapp via the IMPORTED package, streamlit_app via the root.

    Same reasoning as _scanned_trees(): the sdist job has no checkout, but it
    unpacks a tarball that carries both (MANIFEST.in: recursive-include
    streamlit_app *.py *.txt *.md).
    """
    import nmtcapp
    trees = [
        os.path.dirname(os.path.abspath(nmtcapp.__file__)),
        os.path.join(_repo_root(), "streamlit_app"),
    ]
    for t in trees:
        assert os.path.isdir(t), (
            f"{t} is not a directory --- this gate would scan nothing and pass "
            "vacuously"
        )
    return trees


def _docs_dir():
    """docs/ when this is a checkout, None when it is an unpacked sdist.

    mkdocs.yml is the marker. Verified against a built tarball: the sdist
    carries neither docs/ nor mkdocs.yml, so 'both absent' is the sdist and is
    legitimate. 'mkdocs.yml present, docs/ absent' is a deleted docs tree and
    must fail --- see test_docs_tree_is_present_when_this_is_a_checkout.
    """
    root = _repo_root()
    if not os.path.isfile(os.path.join(root, "mkdocs.yml")):
        return None
    return os.path.join(root, "docs")


def _scan():
    """{normalised clause: [locations]} plus the file counts, fail-closed."""
    found: dict = {}
    py_files = 0
    docs_files = 0

    def record(clause, where):
        key = _normalise(clause)
        if key:
            found.setdefault(key, []).append(where)

    for tree in _py_trees():
        for dirpath, dirnames, filenames in os.walk(tree):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                py_files += 1
                src = open(path, encoding="utf-8").read()
                rel = os.path.relpath(path, _repo_root())
                # AST, not regex: a comment is not a node, so the FIX-3 notes
                # that QUOTE the sentences they removed can never match. The
                # line-oriented scans in test_qlici_basis.py need an explicit
                # leading-'#' skip for exactly that reason.
                for text, lineno in _string_units(ast.parse(src)):
                    if _is_prose_attribution(text):
                        record(text, f"{rel}:{lineno}")
                    for offset, row in _table_rows(text):
                        record(row, f"{rel}:{lineno + offset}")

    docs = _docs_dir()
    if docs is not None:
        for dirpath, dirnames, filenames in os.walk(docs):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                docs_files += 1
                rel = os.path.relpath(path, _repo_root())
                body = open(path, encoding="utf-8").read()
                for i, line in enumerate(body.splitlines(), 1):
                    if _is_prose_attribution(line):
                        record(line, f"{rel}:{i}")
                # Whole-file, not per-line: the criteria-table header has to
                # survive to the rows under it. See _table_rows.
                for offset, row in _table_rows(body):
                    record(row, f"{rel}:{offset + 1}")

    return found, py_files, docs_files


@pytest.fixture(scope="module")
def scan():
    return _scan()


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

def _load_allowlist() -> dict:
    entries = {}
    with open(ALLOWLIST_PATH, encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            kind, citation, claim = raw.rstrip("\n").split(" | ", 2)
            entries[claim] = (kind, citation)
    return entries


# ---------------------------------------------------------------------------
# Fail-closed pins
# ---------------------------------------------------------------------------

def test_py_scan_sees_the_source_tree():
    _, py_files, _ = _scan()
    assert py_files >= MIN_PY_FILES, (
        f"only {py_files} .py files scanned (floor {MIN_PY_FILES}) --- the walk "
        "is broken and this gate would pass vacuously"
    )


def test_docs_tree_is_present_when_this_is_a_checkout():
    """mkdocs.yml without docs/ is a deleted docs tree, not an sdist."""
    root = _repo_root()
    if not os.path.isfile(os.path.join(root, "mkdocs.yml")):
        pytest.skip("no mkdocs.yml --- unpacked sdist, docs/ legitimately absent")
    assert os.path.isdir(os.path.join(root, "docs")), (
        "mkdocs.yml is present but docs/ is not. In an sdist BOTH are absent "
        "(MANIFEST.in: prune docs; mkdocs.yml is not shipped), so this is a "
        "checkout with its docs tree removed --- the state in which an "
        "os.walk-based gate silently scans nothing and passes."
    )


def test_docs_scan_is_not_vacuous():
    _, _, docs_files = _scan()
    if _docs_dir() is None:
        pytest.skip("unpacked sdist --- no docs tree to scan")
    assert docs_files >= MIN_DOCS_FILES, (
        f"only {docs_files} .md files scanned under docs/ (floor "
        f"{MIN_DOCS_FILES}) --- docs/ exists but the walk found almost nothing"
    )


def test_scan_is_not_empty(scan):
    found, _, _ = scan
    assert len(found) >= MIN_MATCHES, (
        f"only {len(found)} attributing string(s) found (floor {MIN_MATCHES}). "
        "This package states the CY 2024-2025 gating scores, the LIC "
        "eligibility workbook and the two distress commitments, so a near-empty "
        "match set means the detectors broke, not that the source is clean."
    )


def test_allowlist_entries_carry_a_citation():
    allow = _load_allowlist()
    assert allow, "the allowlist is empty --- every match would fail"
    for claim, (kind, citation) in allow.items():
        assert kind in KINDS, f"unknown kind {kind!r} for {claim[:60]!r}"
        assert len(citation.strip()) >= 12, (
            f"allowlist entry has no real citation: {claim[:60]!r}"
        )
        # Unlike test_attributed_claims.py, a citation here is VERIFIED, not
        # merely recorded: every CITED entry in this file was checked against
        # the primary source retrieved in the 1.2.2 sweep, and names the page
        # or question it was read from.
        if kind in {"CITED", "DEFECT"}:
            assert any(ch.isdigit() for ch in citation), (
                f"a {kind} entry must name a document with a page, question or "
                f"year: {claim[:60]!r} -> {citation!r}"
            )


def test_every_defect_entry_carries_a_defect_tag():
    """Without a tag a DEFECT entry cannot be counted, and the pin goes blind."""
    for claim, (kind, citation) in _load_allowlist().items():
        if kind != "DEFECT":
            continue
        assert _DEFECT_TAG.search(citation), (
            "a DEFECT entry's citation must open with its defect tag "
            f"(D1, D2, ...): {claim[:80]!r} -> {citation[:60]!r}"
        )


def test_defect_count_is_pinned():
    """A ruled defect must stay ruled, and the count must not drift up quietly."""
    allow = _load_allowlist()
    tags = {
        _DEFECT_TAG.search(cit).group(1)
        for k, cit in allow.values()
        if k == "DEFECT" and _DEFECT_TAG.search(cit)
    }
    assert len(tags) == EXPECTED_DEFECTS, (
        f"{len(tags)} distinct false Fund attributions ruled ({sorted(tags)}), "
        f"pinned at {EXPECTED_DEFECTS}. A new tag means the sweep found another "
        "one --- rule it against the primary source, raise the pin "
        "deliberately, and tell whoever is scoping the round before fixing "
        "anything. The 1.2.2 sweep was scoped for two and found seven."
    )


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def test_every_fund_attribution_is_adjudicated(scan):
    found, _, _ = scan
    allow = _load_allowlist()
    unlisted = sorted(set(found) - set(allow))
    if unlisted:
        detail = []
        for claim in unlisted:
            locs = ", ".join(found[claim][:4])
            detail.append(f"  {locs}\n    {claim[:200]}")
        pytest.fail(
            f"{len(unlisted)} source string(s) attribute a threshold or a "
            f"requirement to the CDFI Fund, the Review Process or a regulation "
            f"without adjudication. The allowlist has {len(allow)} entries.\n\n"
            "Rule each one against the PRIMARY SOURCE and add it:\n"
            "  CITED     the Fund states it --- cite document + page/question\n"
            "  HOUSE     this tool's own judgement --- and the RENDERED text "
            "must say so on its face, not merely this list\n"
            "  DEFECT    the Fund does NOT state it --- record the ruling and "
            "raise EXPECTED_DEFECTS deliberately\n"
            "  LABEL / PLACEHO / DISCLAIM / AUDIENCE / SELFREP as applicable\n\n"
            "Do not add an entry you have not opened the source for. Six "
            "entries in the sibling allowlist once cited a CDFI Fund annual "
            "report that does not exist.\n\n"
            + "\n".join(detail)
        )


def test_allowlist_has_no_dead_entries(scan):
    """An entry matching nothing is stale; the list must describe the source.

    SCOPED TO WHAT WAS ACTUALLY SCANNED. In an unpacked sdist there is no
    docs/ tree, so the eleven docs-derived entries below match nothing through
    no fault of their own --- and an unscoped check turns a CORRECT sdist into
    a red release job. That is the same trap that keeps docs/ out of
    _scanned_trees(), one layer further in: it is not enough for the SCAN to
    tolerate the missing tree if the list built from that scan does not.
    Caught by running this module inside a real unpacked tarball; every
    presence test skipped cleanly and this one still failed.
    """
    found, _, _ = scan
    scanning_docs = _docs_dir() is not None
    dead = []
    for claim, (_, citation) in _load_allowlist().items():
        if claim in found:
            continue
        loc = citation[1:citation.index("]")] if citation.startswith("[") else ""
        if not scanning_docs and loc.startswith("docs/"):
            continue  # docs/ is not present here; not evidence of staleness
        dead.append(claim)
    dead.sort()
    assert not dead, (
        f"{len(dead)} allowlist entr(ies) match no source string. Remove them "
        "so the list stays a description of what ships:\n"
        + "\n".join(f"  {d[:160]}" for d in dead)
    )


# ---------------------------------------------------------------------------
# DETECTOR C --- COMMENTS. The half no scan could ever reach (1.5.2 T2).
#
# THE FINDING. nmtcapp/data/schema.py carried, directly above
# READINESS_SCORING_WEIGHTS and for the whole life of the constant:
#
#     # Weights reflect relative importance in CDFI Fund published scoring
#     # rubric.
#
# False, and contradicted by this package's own registry, which rules the same
# constant an "unsourced house heuristic" whose weighting "the CDFI Fund
# publishes no" version of. It is the IDENTICAL defect 1.2.0 removed from
# MIN_GEOGRAPHIC_DIVERSITY ("CDFI Fund historically prefers >=3 states"), one
# dict away in the same file, and it outlived that fix by five releases.
#
# TWO INDEPENDENT REASONS THE EXISTING GATE COULD NOT SEE IT, and both had to
# be true at once:
#
#   1. A COMMENT IS NOT AN AST NODE. _scan() parses each .py file with
#      ast.parse and walks Constant/JoinedStr nodes, which is a deliberate
#      choice recorded at its call site -- it is what stops the FIX-3 notes
#      that QUOTE removed sentences from matching them. Correct for that
#      purpose, and it means no comment in this package has ever been read by
#      this gate.
#
#   2. _BAR REQUIRES A FIGURE. Even fed to _is_prose_attribution directly, the
#      sentence names an authority ("CDFI Fund") and a claim verb
#      ("published") and contains NO NUMBER, so the X2 scope limit -- "this
#      gate's subject is a BAR attributed to an authority" -- excludes it.
#      A comment sweep alone would not have caught this one.
#
# WHAT THE SWEEP MEASURED. Applying _is_prose_attribution to every contiguous
# comment block under nmtcapp/ and streamlit_app/ yields 47 blocks that name an
# authority and state a bar. Read individually, all 47 are the audit notes this
# package writes to record WHY a figure is house or how a Fund quotation was
# ruled -- they are the disclosure record, not defects. An allowlist of 47
# hand-written citations is the one nobody reads, which is the failure mode
# that put six fabricated citations into the sibling allowlist in the first
# place, and the schema.py sentence is not among the 47 anyway.
#
# SO THE GATE IS NOT THE BROAD SWEEP. It asks the narrow question the broad
# sweep cannot: does a comment CONTRADICT THE REGISTRY? A constant this package
# has already ruled HOUSE may not have a comment above it attributing it to the
# CDFI Fund. That is checkable with no allowlist at all, it fails closed, and
# it is exactly the shape of both known instances of the defect.
#
# STATED SCOPE LIMIT, because a gate is as good as the ground it claims. This
# does NOT adjudicate comments above constants that are not registry-ruled
# HOUSE, comments inside function bodies, or the 47 audit notes above. Those
# remain covered by review, and widening this is a deliberate future decision.
# ---------------------------------------------------------------------------

import io as _io
import tokenize as _tokenize

_PINNED_PATH = os.path.join(os.path.dirname(__file__), "pinned_constants.txt")

#: A ruling that the value is this package's own. Uppercase HOUSE is this
#: package's idiom for it -- benchmark_thresholds writes "D4 --- HOUSE, NOT
#: PUBLISHED" -- so the tag is matched case-sensitively in the raw block, and
#: the lowercase phrase list is the prose form of the same statement.
_HOUSE_TAG = re.compile(r"\bHOUSE\b")


def _house_ruled_constants() -> list:
    """Dotted names the constant registry rules HOUSE, deduplicated.

    Subscripts are stripped: a comment sits above the DICT, so a dict with any
    HOUSE-ruled key is in scope. schema.NMTC_PROGRAM_CONSTRAINTS is the case
    that makes this matter -- four of its six keys are house or waived market
    figures and its header comment read "CDFI Fund NMTC program hard
    constraints", which is false about all six.
    """
    names = set()
    with open(_PINNED_PATH, encoding="utf-8") as handle:
        for line in handle:
            row = line.strip()
            if not row or row.startswith("#") or row.startswith("WAIVE"):
                continue
            parts = [p.strip() for p in row.split("|")]
            if len(parts) < 4 or not parts[2].upper().startswith("HOUSE"):
                continue
            names.add(parts[0].split("[")[0])
    return sorted(names)


def _module_paths() -> dict:
    """{module basename: path} for every .py under the imported package."""
    import nmtcapp
    root = os.path.dirname(os.path.abspath(nmtcapp.__file__))
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in sorted(filenames):
            if name.endswith(".py"):
                out.setdefault(name[:-3], os.path.join(dirpath, name))
    return out


def _comment_block_above(lines: list, lineno: int) -> str:
    """The contiguous ``#`` block immediately above a 1-indexed line.

    Contiguous means no blank line and no code between: that is what makes the
    block a comment ABOUT this assignment rather than the tail of an unrelated
    note further up.
    """
    out = []
    index = lineno - 2
    while index >= 0:
        stripped = lines[index].strip()
        if not stripped.startswith("#"):
            break
        out.append(stripped.lstrip("#").strip())
        index -= 1
    return "\n".join(reversed(out))


def _assignment_line(tree, const: str):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == const:
                return node.lineno
    return None


def _attributes_to_the_fund(block: str) -> bool:
    """The block names an authority and does not rule the value house."""
    low = block.lower()
    if not any(authority in low for authority in AUTHORITIES):
        return False
    if _HOUSE_TAG.search(block):
        return False
    return any(disclaimer in low for disclaimer in _DISCLAIMERS) is False


def _house_comment_offenders() -> tuple:
    """(offenders, examined). Shared by the gate and by its red-proof."""
    modules = _module_paths()
    offenders = []
    examined = []
    for full in _house_ruled_constants():
        module, const = full.rsplit(".", 1)
        path = modules.get(module)
        if path is None:
            continue  # resolution is test_every_pinned_constant_name_resolves'
        source = open(path, encoding="utf-8").read()
        lineno = _assignment_line(ast.parse(source), const)
        if lineno is None:
            continue
        block = _comment_block_above(source.splitlines(), lineno)
        examined.append(full)
        if block and _attributes_to_the_fund(block):
            rel = os.path.relpath(path, _repo_root())
            offenders.append(f"  {full}  ({rel}:{lineno})\n      {block[:300]}")
    return offenders, examined


def test_no_house_constant_is_attributed_to_the_fund_in_its_own_comment():
    """T2 (1.5.2). A comment may not contradict the constant registry.

    Proved red by planting, on this tree: restoring "Weights reflect relative
    importance in CDFI Fund published scoring rubric." above
    READINESS_SCORING_WEIGHTS turns this test red naming that constant, and
    restoring "CDFI Fund NMTC program hard constraints" above
    NMTC_PROGRAM_CONSTRAINTS turns it red naming that one. Both were live at
    fde3eca and neither turned anything red there.
    """
    offenders, examined = _house_comment_offenders()

    # FAIL CLOSED. A registry that stopped yielding HOUSE rows, or a walk that
    # resolved no module, would pass this vacuously.
    assert len(examined) >= 10, (
        f"only {len(examined)} HOUSE-ruled constants were examined "
        f"({examined}). This gate reads tests/pinned_constants.txt for rows "
        "whose SOURCE column opens with HOUSE and resolves each to its "
        "definition; too few means the registry format moved or the module "
        "walk found nothing, and the gate is passing on ground it never read."
    )

    assert not offenders, (
        f"{len(offenders)} constant(s) this package's own registry rules "
        "HOUSE carry a comment attributing them to a federal authority, with "
        "no disclaimer in the same block.\n\n"
        "A comment is not a rendered surface and no CDE reads one. It is "
        "worse than that: it is a claim a future round re-cites having "
        "assumed somebody checked it, which is how 'CDFI Fund historically "
        "prefers >=3 states' survived nine releases above "
        "MIN_GEOGRAPHIC_DIVERSITY.\n\n"
        "Either the comment is wrong -- correct it and say what the value "
        "actually is -- or the registry ruling is wrong, in which case change "
        "the ruling and its citation, not this test.\n\n"
        + "\n".join(offenders)
    )


def test_the_comment_sweep_can_see_comments_at_all():
    """NON-VACUITY FOR DETECTOR C, asserted rather than assumed.

    ``_comment_block_above`` returning "" everywhere would make the gate above
    green forever. This proves it reads real blocks off the real tree, and it
    proves the specific property that made the defect invisible: the EXISTING
    string scan cannot see the same text.
    """
    modules = _module_paths()
    source = open(modules["schema"], encoding="utf-8").read()
    lineno = _assignment_line(ast.parse(source), "READINESS_SCORING_WEIGHTS")
    block = _comment_block_above(source.splitlines(), lineno)

    assert len(block) > 200, (
        "the comment block above READINESS_SCORING_WEIGHTS is "
        f"{len(block)} characters; the sweep is reading nothing:\n{block!r}"
    )
    assert "HOUSE" in block, (
        "the corrected comment no longer rules this constant HOUSE:\n" + block
    )

    # And the AST scan the rest of this module uses genuinely cannot reach it.
    literals = [text for text, _ in _string_units(ast.parse(source))]
    assert not any("relative importance in CDFI Fund" in t for t in literals)
    for text in literals:
        assert block[:120] not in text, (
            "the comment block is reachable as a string literal, so detector "
            "C is redundant and this module's premise is wrong."
        )


def test_docstrings_are_already_covered_by_the_existing_string_scan():
    """Docstrings need no detector C, and that is PROVED here, not assumed.

    T2 asked for a sweep of "comments and docstrings". A module, class or
    function docstring is an ``ast.Expr`` wrapping an ``ast.Constant``, so
    ``_string_units`` already yields it and ``_scan`` already adjudicates it --
    which is why eleven docstring-derived entries sit in the allowlist. Adding
    a second detector for docstrings would double-count them. Asserted against
    a real docstring so a future change to _string_units cannot quietly make
    this false.
    """
    modules = _module_paths()
    source = open(modules["_round_provenance"], encoding="utf-8").read()
    tree = ast.parse(source)
    # The RAW node value, not ast.get_docstring(), which cleans indentation
    # and would compare a normalised string against unnormalised literals.
    first = tree.body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    raw = first.value.value
    assert isinstance(raw, str) and len(raw) > 200, (
        "_round_provenance has no module docstring to test with"
    )

    literals = [text for text, _ in _string_units(tree)]
    assert raw in literals, (
        "_string_units no longer yields module docstrings, so the docstring "
        "half of the T2 sweep is NOT covered and detector C must grow one."
    )
    # And the scan actually adjudicates it: this docstring is allowlisted, so
    # a scan that skipped docstrings would leave a dead allowlist entry.
    assert any(_is_prose_attribution(text) for text, _ in _string_units(tree)), (
        "_round_provenance yields no prose attribution at all, so this file "
        "no longer demonstrates that docstrings reach the detector."
    )
