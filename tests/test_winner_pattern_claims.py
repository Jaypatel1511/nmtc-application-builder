"""No surface may claim the house winner constants are measurements of past winners (1.7.2 F2).

THE DEFECT
==========

``streamlit_app/app.py``'s Methodology Disclosure adjudicated this in 1.2.x,
citing ``nmtcapp/data/historical_awards.py`` as denying the claim:

    "Alignment scores measure similarity to this tool's own assumed winner
     patterns, which are unsourced house constants — not measurements of past
     winners, and not a CDFI Fund publication."

The 1.7.1 app settle read found two surfaces on the same app still asserting
the opposite, unqualified: Home's "Getting started" ("score your application
against historical winner patterns") and the Pipeline Optimizer's subtitle
("maximizes composite alignment with historical NMTC winner patterns") -- on
the one page with no disclosure at all. The repo-wide sweep this release ran
found the same claim in the Win Alignment Scorer's own Methodology Notice
("patterns observed in historical NMTC award winners (CY2020–CY2024)"), in
``OptimizationResult.methodology_note`` (rendered on page 3 and by
``summary()``), in the README ("five years of CDFI Fund award data"), in
seven docs pages, in the example notebook, in the sector-mix chart title and
in a dozen docstrings. The one-surface-fixed shape, again.

THE GATE -- R11's SHAPE, APPLIED TO THIS CLAUSE
===============================================

R11 (1.7.1) moved ``LOWER_BOUND_CLAUSE`` into ``renderers/_disclosure``, read
it on every surface, forbade the contradicting sentence document-wide, pinned
the true half so it could not be softened, required the surfaces to state it
identically, and walked the installed package for retyped copies. This does
the same for ``_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE``:

1. FORBIDDEN -- the provenance claim, in every spelling the sweep found and the
   obvious neighbours: "historical ... winners/winner patterns", "observed in
   ... winners", "trained on ... winner data", "typical winner", "what winners
   do", "winning applications", "compares to past winners". Scanned over:

     * every Streamlit page RENDERED, cold and after its action (the list is
       the directory's, via ``test_streamlit_surface_enumeration``);
     * the four generated formats and the CLI, through their committed
       baselines (``tests/rendered_baseline``, ``tests/cli_baseline``), which
       their own gates hold byte-equal to live output;
     * the installed ``nmtcapp`` package, ``streamlit_app/``, ``README.md``
       and ``pyproject.toml`` -- whole files, so comments and docstrings too;
     * in a checkout, ``docs/``, ``mkdocs.yml``, ``examples/``,
       ``CONTRIBUTING.md``, ``CITATION.cff`` and ``scripts/``.

   Rendered text gets NO exemption. Source text may quote a withdrawn phrase
   to record it -- this file's own history section does -- and each such
   RECORD is listed in ``RECORDS`` with its reason, must still match (no dead
   entries), and excuses exactly one line.

2. AGREEMENT -- a user-facing sentence that names winner patterns, winner
   benchmarks, winner figures or a winner distribution must say, in the same
   sentence, that they are this tool's own / assumed / house / unsourced, or
   deny the thing outright. Scanned over rendered pages, README, docs, the
   notebook and the package's string literals (docstrings included; comments
   are maintainers' notes and are held only to rule 1).

3. THE TRUE HALF IS PINNED -- the clause's load-bearing phrases, so a "fix"
   that softens the disclosure to agree with a claim fails.

4. ONE STRING -- the clause is present VERBATIM on every rendered page that
   carries it and in the README and docs copies that cannot interpolate it,
   and no ``.py`` outside ``_disclosure`` retypes it.

WHAT IS DELIBERATELY OUT OF SCOPE
=================================

* ``CHANGELOG.md`` -- a dated record whose entries quote withdrawn wording by
  design, including the 1.7.2 entry that records these very phrases.
* ``tests/`` source -- tests quote the forbidden phrases in order to forbid
  them. The rendered baselines under ``tests/`` ARE scanned: they are output.
* Identifiers -- ``WINNER_DISTRESS_PATTERNS``, ``compare_to_winners``,
  ``winner_p75`` keys. Renaming public API is a minor release, and a name is
  not a sentence; the constants' own comments now say what they are.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from nmtcapp.renderers._disclosure import (
    ASSUMED_WINNER_PATTERNS,
    ASSUMED_WINNER_PATTERNS_CLAUSE,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent

#: RULE 1. Each pattern is one spelling of "these figures were measured from
#: past winners". ``\W+`` spans newlines and ``#``, so a claim hard-wrapped
#: across two lines of a docs page or a comment is still one match. A word
#: token is ``\w+(?:[–-]\w+)*`` -- hyphens only INSIDE a word -- because
#: ``[\w–-]+\W+`` lets both halves claim a dash and backtracks exponentially
#: on a ``# -----`` ruler (measured: 121 s on one page module).
FORBIDDEN = {
    "historical-winners": re.compile(
        r"historical\W+(?:\w+(?:[–-]\w+)*\W+){0,3}?winn\w*", re.I),
    "observed-in-winners": re.compile(
        r"observed\W+in\W+(?:\w+(?:[–-]\w+)*\W+){0,6}?winn\w*", re.I),
    "trained-on-winner-data": re.compile(
        r"trained\W+on\W+(?:\w+(?:[–-]\w+)*\W+){0,4}?winn\w*"
        r"|(?<!non-)(?<!non )\bwinn(?:er|ing)\W+data\b", re.I),
    "typical-winner": re.compile(r"typical\W+winn\w*", re.I),
    "what-winners-do": re.compile(r"what\W+winners\W+(?:do|look|got|have)\b", re.I),
    "winning-applications": re.compile(r"winning\W+applications?\b", re.I),
    "compared-to-past-winners": re.compile(
        r"(?:compar\w*|\bvs\b\.?|versus|against|relative\W+to|stands?)\W+"
        r"(?:\w+(?:[–-]\w+)*\W+){0,3}?(?:past|prior|previous)\W+winn\w*", re.I),
}

#: A match is a DENIAL, not a claim, when its own clause says so before it:
#: "no corpus of winning applications is loaded", "not a measurement of
#: winning applications". Scoped to the clause (split at ; : . — ( ) so a
#: "not" in one clause cannot excuse a claim in the next. A newline is NOT a
#: clause break: a comment wraps a clause across lines.
_NEGATION = re.compile(r"\b(?:not|no|never|nor|none|neither)\b", re.I)
_CLAUSE_BREAK = re.compile(r"[;:.!?—–()\[\]]")
_DENIABLE = {"winning-applications", "compared-to-past-winners"}

#: RULE 2. The nouns of the claim, and what must accompany them.
WINNER_NOUN = re.compile(
    r"(?<!non-)\bwinners?[- ](?:patterns?|benchmarks?|distributions?|figures?|"
    r"statistics|profiles?|bands?|heuristics?|thresholds?)\b", re.I)
QUALIFIER = re.compile(
    r"assumed|\bhouse\b|this tool'?s(?: own)?|this package'?s(?: own)?|"
    r"unsourced|not measurements?|\bno winner|\bnot (?:a|against|derived|"
    r"inferred)\b|never|does not exist", re.I)

#: The provenance clause's load-bearing phrases (RULE 3).
CLAUSE_ANCHORS = (
    "this tool's own assumed winner patterns",
    "unsourced house constants",
    "not measurements of past winners",
    "not a CDFI Fund publication",
)

#: RECORDS -- source lines that QUOTE a withdrawn phrase in order to record
#: that it was withdrawn. ``(path, fragment of that line, why)``. Each must
#: match exactly one line that rule 1 or rule 2 flags; a record that matches
#: nothing is dead and fails. Rendered text can never be a record.
RECORDS = (
    ("nmtcapp/data/historical_awards.py", '"HISTORICAL NMTC WINNERS". They feed',
     "1.2.0's module docstring recording the grep it ran over rendered output"),
    ("nmtcapp/data/historical_awards.py", 'announcements. The "typical winner" patterns below',
     "1.7.2's correction to the data-quality note, naming the phrase it corrects"),
    ("nmtcapp/intelligence/benchmarks.py", '1.5.0: "Compare a pipeline analysis result against historical NMTC winner',
     "the module docstring quoting the summary 1.5.0 withdrew"),
    ("nmtcapp/renderers/_disclosure.py", "historical winners, NOT PROBABILITY OF SELECTION. Use as diagnostic",
     "wrap_disclosure's docstring quoting the truncated disclosure 1.3.1 fixed"),
    ("nmtcapp/renderers/_disclosure.py", "#: Optimizer's subtitle (\"maximizes composite alignment with historical NMTC",
     "the clause's own history, quoting page 3's struck subtitle"),
    ("nmtcapp/renderers/_disclosure.py", '#: application against historical winner patterns") and the Pipeline',
     "the clause's own history, quoting Home's struck sentence"),
    ("nmtcapp/renderers/_disclosure.py", '#: Notice ("patterns observed in historical NMTC award winners"), the',
     "the clause's own history, quoting page 2's struck notice"),
    ("nmtcapp/optimizer/pipeline_optimizer.py", '# "Objective: maximize composite alignment score with historical NMTC winner',
     "the comment recording the methodology note 1.7.2 corrected"),
    ("nmtcapp/visualization/maps.py", '#: ("Application vs. Historical Winner Patterns"), one function over. The',
     "the sector-mix title comment citing B3's precedent"),
    ("nmtcapp/visualization/maps.py", '# THE TITLE SAID "Application vs. Historical Winner Patterns" (B3). It',
     "B3's own record of the suptitle it corrected"),
    ("streamlit_app/app.py", '# "Trained on CY2020-2024 winner data" was withdrawn in 1.2.0. Nothing',
     "the stats-bar comment recording 1.2.0's withdrawal"),
    ("streamlit_app/app.py", '# "observed in historical NMTC award winners" asserted an empirical',
     "the disclosure comment recording the phrase the disclosure replaced"),
    ("streamlit_app/app.py", '# WAS "Score your application\'s alignment with patterns in historical',
     "the feature-card comment recording 1.7.2's correction"),
    ("streamlit_app/pages/3_Pipeline_Optimizer.py", '# WAS "maximizes composite alignment with historical NMTC winner patterns"',
     "the subtitle comment recording 1.7.2's correction"),
    ("streamlit_app/pages/1_Pipeline_Analyzer.py", 'A number a CDE reads as "what winners do" is a',
     "B3's comment explaining why 'Winner' was deleted from two labels"),
    ("streamlit_app/pages/1_Pipeline_Analyzer.py", '# WITHDRAWN IN 1.2.0. This chart used to read "Benchmarks vs. historical',
     "1.2.0's record of the chart title it withdrew"),
    ("streamlit_app/utils.py", 'OBSERVED IN HISTORICAL NMTC AWARD WINNERS (CY2020–CY2024)" (1.7.2 F2). That',
     "render_methodology_warning's docstring recording the notice it replaced"),
    ("docs/workflow/pipeline-analysis.md", 'typical winner patterns" for C and "Application not viable in current form" for',
     "the correction note quoting the grade labels 1.5.x withdrew"),
    ("docs/about/why.md", 'computes "the winner distribution" for those four dimensions',
     "the 1.5.1 correction note quoting the paragraph it corrected"),
    ("docs/quickstart.md", 'This passage said the engine "benchmarks each dimension against historical',
     "the 1.5.1 note quoting the passage it withdrew"),
)

#: Surfaces that must carry the clause VERBATIM (RULE 4). EVERY PAGE, counted
#: from the directory, unless classified here with the reason it does not --
#: a hand-typed list of disclosing pages is the enumeration F4 replaced.
CLAUSE_EXEMPT_PAGES = {
    "pages/1_Pipeline_Analyzer.py": (
        "Its two house-winner figures state their own provenance where they "
        "render -- the distress chart's caption (this tool's own screening "
        "band, not a percentile of past winners) and the jobs-per-QEI caption "
        "(WINNER_IMPACT_BENCHMARKS, this tool's own unsourced figures, not "
        "percentiles of any measured population) -- and rule 2 holds every "
        "sentence on the page to that; it renders no alignment score."
    ),
}
CLAUSE_FILES = ("README.md",)
CLAUSE_CHECKOUT_FILES = (
    "docs/about/limitations.md",
    "docs/workflow/optimization.md",
    "docs/reference/api.md",
)


# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------

def _is_checkout() -> bool:
    """mkdocs.yml is the checkout marker the fund-attribution gate uses: the
    sdist ships neither it nor docs/, so their joint absence is the sdist."""
    return (_REPO_ROOT / "mkdocs.yml").is_file()


def _package_root() -> Path:
    import nmtcapp
    return Path(os.path.abspath(nmtcapp.__file__)).parent


def _source_files() -> dict:
    """``{display path: Path}`` for every source file rule 1 reads."""
    files = {}
    pkg = _package_root()
    for path in sorted(pkg.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        files["nmtcapp/" + path.relative_to(pkg).as_posix()] = path
    app = _REPO_ROOT / "streamlit_app"
    for path in sorted(app.rglob("*")):
        if path.suffix in (".py", ".md", ".txt") and "__pycache__" not in path.parts:
            files[path.relative_to(_REPO_ROOT).as_posix()] = path
    for name in ("README.md", "pyproject.toml"):
        files[name] = _REPO_ROOT / name
    if _is_checkout():
        docs = _REPO_ROOT / "docs"
        assert docs.is_dir(), (
            "mkdocs.yml is present but docs/ is not: a checkout with its docs "
            "tree deleted, which is the state in which a walk scans nothing"
        )
        for root in (docs, _REPO_ROOT / "examples", _REPO_ROOT / "scripts"):
            for path in sorted(root.rglob("*")):
                if path.suffix in (".md", ".py", ".ipynb", ".yml", ".sh") and path.is_file():
                    files[path.relative_to(_REPO_ROOT).as_posix()] = path
        for name in ("mkdocs.yml", "CONTRIBUTING.md", "CITATION.cff"):
            files[name] = _REPO_ROOT / name
    for shown, path in files.items():
        assert path.is_file(), f"{shown} is missing -- the scan would read nothing there"
    return files


def _baseline_files() -> dict:
    out = {}
    for sub in ("rendered_baseline", "cli_baseline"):
        for path in sorted((_REPO_ROOT / "tests" / sub).glob("*.txt")):
            out[f"tests/{sub}/{path.name}"] = path
    return out


def _rendered_units() -> list:
    """``[(location, text)]`` -- one unit per prose element per page state."""
    from tests.streamlit_render import rendered_pages, texts

    units = []
    for rel, states in rendered_pages().items():
        for state in ("cold", "driven"):
            at = states[state]
            assert not at.exception, f"{rel} ({state}) raised: {at.exception}"
            for i, (kind, text) in enumerate(texts(at)):
                units.append((f"rendered:{rel}:{state}:{kind}#{i}", text))
    return units


# ---------------------------------------------------------------------------
# The two rules
# ---------------------------------------------------------------------------

def _line_at(text: str, offset: int):
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return text.count("\n", 0, offset) + 1, text[start:end if end >= 0 else None]


def _denied(text: str, match) -> bool:
    before = text[:match.start()]
    clause = _CLAUSE_BREAK.split(before)[-1]
    return bool(_NEGATION.search(clause))


def forbidden_hits(text: str) -> list:
    """``[(rule, offset, matched text)]`` for every rule-1 claim in ``text``."""
    hits = []
    for rule, pattern in FORBIDDEN.items():
        for m in pattern.finditer(text):
            if rule in _DENIABLE and _denied(text, m):
                continue
            hits.append((rule, m.start(), m.group(0)))
    return hits


_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z*_`>\"'(])")


def unqualified_sentences(text: str) -> list:
    """Sentences naming a winner-pattern noun with no qualifier (rule 2)."""
    flat = re.sub(r"`[^`]*`", " ", text)        # identifiers are not prose
    flat = re.sub(r"\s+", " ", flat)
    return [s for s in _SENTENCE.split(flat)
            if WINNER_NOUN.search(s) and not QUALIFIER.search(s)]


#: Names whose interpolation into an f-string IS the qualifier. An f-string
#: is reconstructed with these substituted by their values, so
#: ``f"those are {ASSUMED_WINNER_PATTERNS_CLAUSE}."`` is read as the sentence
#: it renders. Any other interpolation becomes a neutral placeholder.
_QUALIFYING_NAMES = {
    "ASSUMED_WINNER_PATTERNS": ASSUMED_WINNER_PATTERNS,
    "ASSUMED_WINNER_PATTERNS_CLAUSE": ASSUMED_WINNER_PATTERNS_CLAUSE,
}


def _string_literals(path: Path) -> list:
    """``[(lineno, text)]`` for every string literal (docstrings included),
    with f-strings reconstructed as one unit rather than read in pieces."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out, consumed = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                consumed.add(id(value))
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif (isinstance(value, ast.FormattedValue)
                      and isinstance(value.value, ast.Name)
                      and value.value.id in _QUALIFYING_NAMES):
                    parts.append(_QUALIFYING_NAMES[value.value.id])
                else:
                    parts.append("<value>")
            out.append((node.lineno, "".join(parts)))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in consumed):
            out.append((node.lineno, node.value))
    return out


def _prose_units(files: dict) -> list:
    """``[(display path, lineno, text)]`` units rule 2 reads from source."""
    units = []
    for shown, path in files.items():
        if path.suffix == ".py":
            units.extend((shown, ln, s) for ln, s in _string_literals(path))
        elif path.suffix in (".md", ".ipynb"):
            units.append((shown, 1, path.read_text(encoding="utf-8")))
    return units


@pytest.fixture(scope="module")
def corpus():
    return {
        "source": _source_files(),
        "baselines": _baseline_files(),
        "rendered": _rendered_units(),
    }


def _flagged(corpus) -> list:
    """Every flagged line: ``(where, line, detail, excusable)``."""
    flagged = []
    for shown, path in corpus["source"].items():
        text = path.read_text(encoding="utf-8")
        seen = set()
        for rule, offset, matched in forbidden_hits(text):
            lineno, line = _line_at(text, offset)
            if lineno in seen:
                continue
            seen.add(lineno)
            flagged.append((f"{shown}:{lineno}", line.strip(), f"{rule}: {matched!r}", True))
    for shown, lineno, text in _prose_units(corpus["source"]):
        for sentence in unqualified_sentences(text):
            flagged.append((f"{shown}:{lineno}", sentence.strip(),
                            "unqualified winner noun", True))
    for shown, path in corpus["baselines"].items():
        text = path.read_text(encoding="utf-8")
        for rule, offset, matched in forbidden_hits(text):
            lineno, line = _line_at(text, offset)
            flagged.append((f"{shown}:{lineno}", line.strip(), f"{rule}: {matched!r}", False))
        for sentence in unqualified_sentences(text):
            flagged.append((shown, sentence, "unqualified winner noun", False))
    for where, text in corpus["rendered"]:
        for rule, offset, matched in forbidden_hits(text):
            flagged.append((where, _line_at(text, offset)[1].strip(), f"{rule}: {matched!r}", False))
        for sentence in unqualified_sentences(text):
            flagged.append((where, sentence, "unqualified winner noun", False))
    return flagged


def _record_for(where: str, line: str):
    path = where.rsplit(":", 1)[0]
    for rec_path, fragment, _why in RECORDS:
        if rec_path == path and fragment in line:
            return (rec_path, fragment)
    # rule-2 sentences are whitespace-flattened; compare flattened too
    flat_line = re.sub(r"\s+", " ", line)
    for rec_path, fragment, _why in RECORDS:
        if rec_path == path and re.sub(r"\s+", " ", fragment) in flat_line:
            return (rec_path, fragment)
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_the_scan_reads_what_it_claims_to(corpus):
    """Anti-vacuity: every tree was reached and the rendered pages said something."""
    src = corpus["source"]
    assert sum(1 for p in src if p.startswith("nmtcapp/")) >= 60, "package walk read too little"
    assert sum(1 for p in src if p.startswith("streamlit_app/")) >= 7, "app walk read too little"
    if _is_checkout():
        assert sum(1 for p in src if p.startswith("docs/")) >= 15, "docs walk read too little"
        assert any(p.startswith("examples/") for p in src), "examples/ was not read"
    assert len(corpus["baselines"]) >= 5, "the rendered/CLI baselines were not found"
    rendered_pages = {w.split(":")[1] for w, _ in corpus["rendered"]}
    from tests.test_streamlit_surface_enumeration import page_files
    assert rendered_pages == set(page_files()), (
        f"rendered {sorted(rendered_pages)}; the directory has {sorted(page_files())}")
    assert sum(len(t) for _, t in corpus["rendered"]) > 50_000, (
        "the rendered pages carry almost no text -- AppTest drove nothing")


def test_no_surface_claims_the_winner_patterns_were_measured(corpus):
    """RULES 1 AND 2, every surface. The only exemption is a listed RECORD in source."""
    offending = []
    for where, line, detail, excusable in _flagged(corpus):
        if excusable and _record_for(where, line):
            continue
        offending.append(f"  {where}\n      {detail}\n      | {line[:220]}")
    assert not offending, (
        "a surface states or implies that this tool's winner patterns are "
        "measurements of past winners. They are "
        f"{ASSUMED_WINNER_PATTERNS_CLAUSE!r} "
        "(renderers/_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE). Interpolate "
        "the clause, or say what the figure actually is -- and do not describe "
        "the Win Alignment Scorer's score with it: that score applies the CY "
        "2024-2025 Review Process structure and reads no WINNER_* constant.\n\n"
        + "\n".join(offending)
    )


def test_every_record_still_records_exactly_one_line(corpus):
    """No dead records, and no record wide enough to excuse two lines.

    SCOPED TO WHAT WAS SCANNED: in the sdist job docs/ is absent, so a docs
    record has nothing to match there and is not dead -- the same rule
    test_fund_attribution_source's dead-entry check applies.
    """
    counts = {(p, f): set() for p, f, _ in RECORDS if p in corpus["source"]}
    for where, line, _detail, excusable in _flagged(corpus):
        if not excusable:
            continue
        rec = _record_for(where, line)
        if rec:
            counts[rec].add(where)
    bad = {k: sorted(v) for k, v in counts.items() if len(v) != 1}
    assert not bad, (
        "RECORDS entries must each excuse exactly one flagged line (dead or "
        f"too wide): {bad}")
    for rel in CLAUSE_EXEMPT_PAGES:
        assert rel in _pages(), f"CLAUSE_EXEMPT_PAGES names {rel}, which is not a page"
    for path, _fragment, why in RECORDS:
        assert len(why) >= 30, f"record in {path} carries no real reason: {why!r}"
        assert not path.startswith("rendered:"), "rendered text can never be a record"


def test_the_clause_keeps_its_true_half():
    """RULE 3. Agreement by softening the disclosure is not the fix."""
    for anchor in CLAUSE_ANCHORS:
        assert anchor in ASSUMED_WINNER_PATTERNS_CLAUSE, (
            f"ASSUMED_WINNER_PATTERNS_CLAUSE no longer says {anchor!r}; "
            "data/historical_awards.py and tests/scoring_attribution.txt still "
            "rule every winner constant HOUSE and unsourced"
        )
    assert ASSUMED_WINNER_PATTERNS_CLAUSE.startswith(ASSUMED_WINNER_PATTERNS)


def _pages() -> list:
    from tests.test_streamlit_surface_enumeration import page_files
    return page_files()


@pytest.mark.parametrize("relpath", _pages())
def test_each_page_renders_the_clause_verbatim_or_is_classified(relpath):
    """RULE 4, rendered, on the COLD load. Markdown bold is stripped first:
    Home and page 3 bold the noun phrase, as Home always has."""
    from tests.streamlit_render import page_text
    if relpath in CLAUSE_EXEMPT_PAGES:
        assert len(CLAUSE_EXEMPT_PAGES[relpath]) >= 60, (
            f"{relpath}'s exemption gives no real reason")
        return
    text = page_text(relpath, "cold").replace("**", "")
    assert ASSUMED_WINNER_PATTERNS_CLAUSE in text, (
        f"{relpath} does not render the provenance clause verbatim.\n"
        f"Expected: {ASSUMED_WINNER_PATTERNS_CLAUSE!r}"
    )


def test_the_home_and_optimizer_disclosures_are_one_string():
    """The Methodology Disclosure is rendered on Home and page 3 from one
    constant; the two renders must be byte-identical to it."""
    import utils  # streamlit_app/, on sys.path via tests.streamlit_render
    from tests.streamlit_render import rendered_pages, texts

    # st.info lifts a leading emoji into its icon slot, so AppTest reports
    # the body without the "⚠️ ". Compare bodies, and require the emoji to be
    # the only difference.
    expected = utils.METHODOLOGY_DISCLOSURE
    assert expected.startswith("⚠️ ")
    body = expected[len("⚠️ "):]
    for rel in ("app.py", "pages/3_Pipeline_Optimizer.py"):
        infos = [t for k, t in texts(rendered_pages()[rel]["cold"]) if k == "info"]
        assert body in infos, (
            f"{rel} does not render utils.METHODOLOGY_DISCLOSURE as an st.info")


def test_the_copies_that_cannot_interpolate_state_it_verbatim():
    """RULE 4, files. Markdown cannot interpolate a Python constant, so the
    README and docs copies are held to it character for character -- change
    the constant and these go red rather than drifting."""
    names = list(CLAUSE_FILES) + (list(CLAUSE_CHECKOUT_FILES) if _is_checkout() else [])
    missing = [n for n in names
               if ASSUMED_WINNER_PATTERNS_CLAUSE not in
               re.sub(r"\s+", " ", (_REPO_ROOT / n).read_text(encoding="utf-8"))]
    assert not missing, f"the clause is not stated verbatim in: {missing}"


def test_no_python_module_retypes_the_clause():
    """Walks the INSTALLED package and streamlit_app/ -- the sdist job has no
    ``<repo>/nmtcapp``, and a walk over a missing directory would pass."""
    fragment = "unsourced house constants — not"
    copies, walked = [], 0
    trees = [_package_root(), _REPO_ROOT / "streamlit_app"]
    for tree in trees:
        for path in tree.rglob("*.py"):
            if "__pycache__" in path.parts or path.name == "_disclosure.py":
                continue
            walked += 1
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if fragment in line:
                    copies.append(f"{path}:{lineno}")
    assert walked >= 60, f"walked only {walked} modules; the sweep read nothing"
    assert not copies, (
        f"the provenance clause is retyped at {copies}; read "
        "_disclosure.ASSUMED_WINNER_PATTERNS_CLAUSE instead")
