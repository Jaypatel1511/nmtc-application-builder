"""THE DOCS-KEY GATE: a key the docs tell a caller to read must exist in the dict.

WHAT THIS CLOSES

F3, and the class F3 belongs to. ``docs/workflow/pipeline-analysis.md``
documented ``g["urban_pct"]`` after the key had been deleted from the returned
dict. It shipped. It was caught BY EYE, during a release, by somebody reading
the file for another reason -- which is not a mechanism, it is luck, and luck
does not fire twice in the same place.

No existing gate could see it, and each one misses it for its own reason:

  * ``test_pinned_constants``           asks what a constant PRINTS. A dict key
                                        is not printed; ``urban_pct`` never
                                        reached a rendered surface.
  * ``test_attributed_claims``          audits rendered PROSE for attributions.
                                        A code fence in docs/ renders nothing.
  * ``test_fund_attribution_source``    scans docs/ -- but for claims that name
                                        an AUTHORITY. ``g["urban_pct"]`` names
                                        nobody and asserts nothing.
  * ``test_streamlit_deployment_pin``   resolves IMPORTS. Its own docstring
                                        concedes the boundary verbatim:
                                        "RUNTIME ATTRIBUTE ACCESS.
                                        ``analysis.impact_summary["x"]`` ...
                                        Only import-time names are static."

So the hole was named, in writing, in this suite, by the gate that could not
reach it -- and stayed open for a release anyway. This is the gate on the other
side of that sentence.

WHY IT MATTERS MORE THAN A TYPO IN A DOC

A documented key is an API promise. A caller who writes the documented line
gets ``KeyError`` at runtime, in their own code, with nothing pointing back
here. Between the deletion and the discovery, the published docs site instructs
every reader to write a line that raises.

THE METHOD -- DERIVED ON BOTH SIDES, TYPED ON NEITHER

SCOPE: docs/ AND examples/, AND THE SECOND HALF IS THE SHARPER ONE

The brief for this gate named ``docs/workflow/pipeline-analysis.md``. Scoping
it there would have been site-fixing: the same class lives in
``examples/*.ipynb``, and it lives there in a WORSE form. A stale key in a
markdown fence is a wrong instruction. A stale key in a notebook is EXECUTABLE
CODE THAT RAISES -- and ``examples/01_quickstart.ipynb`` is the first thing a
new user runs.

Both halves were live when this gate was written; see the round's CHANGELOG
entry. The notebook half would have stayed invisible to a docs-only gate, which
is the whole argument for deriving the scan set from what the repository
publishes rather than from what a brief happened to name.

  LEFT SIDE   Every ``<something>["key"]`` the scanned corpus contains, found
              two ways because the defect has two shapes:

              DETECTOR A (AST). Each ``python`` fence is parsed. Local
              aliases are resolved to the attribute they were bound from --
              ``d = analysis.distress_analysis`` makes every later ``d["k"]``
              a read of ``distress_analysis`` -- so the gate sees through the
              indirection the docs actually use. This is the same
              alias-resolution idiom as
              ``tests/integrations/test_mapper_contract._alias_names``, and it
              exists for the same reason: a derivation one binding defeats is
              a derivation that silently checks nothing.

              DETECTOR B (TEXT). The same subscript written in PROSE, or in a
              markdown table cell, or inside a fence that does not parse.
              ``docs/reference/methodology.md:208`` documents
              ``phase2_flags["non_metro_pipeline_qei_pct"]`` in a running
              sentence; ``docs/reference/api.md`` carries twenty signature
              stubs that are not valid Python. Detector A sees neither. A gate
              that only read fences would call methodology.md clean without
              having looked at it.

              DETECTOR A IS INERT ON api.md ENTIRELY, and that is asserted
              rather than described: all twenty of its fences fail to parse on
              every interpreter, so its alias map for that file is empty and
              Detector B carries it alone. ``_DETECTOR_A_INERT_FENCES`` at the
              foot of this module pins the count, because a half-off gate
              reads as a whole one (1.5.0 T3).

  RIGHT SIDE  The dicts this package actually returns, read off LIVE objects
              built from the packaged fixtures. Nothing about the expected key
              set is written down here; it is whatever the code produces today.

The two are matched by ATTRIBUTE NAME, which is unique across the four root
objects -- asserted, not assumed, by
``test_the_dict_attribute_registry_has_no_name_collisions``.

FAILS CLOSED, in every way this repository has been bitten before:

  * An empty document scan errors (round nine was a grep against the wrong
    path set, and silence reading as absence).
  * An empty subscript harvest errors.
  * A root object that fails to build errors rather than skipping.
  * A documented root this gate cannot resolve errors, so a NEW unresolvable
    root is loud instead of silently uncovered -- see
    ``test_the_unresolved_roots_are_the_documented_ones``.
  * The scan runs when ``docs/`` and ``examples/`` are present. MANIFEST.in
    prunes both from the sdist, so their JOINT absence is correct and the
    module skips; exactly one present FAILS, because an absent directory must
    never be indistinguishable from a clean one. Same checkout marker
    ``test_fund_attribution_source`` uses, and for the same reason.

WHAT THIS GATE DOES NOT COVER, STATED RATHER THAN IMPLIED

``cde_attributes`` is an INPUT dict -- what a CDE supplies, not what this
package returns -- so "does the key exist" is not the question to ask of it.
The right question there is whether anything READS the documented key, which is
a different assertion against a different corpus, and merging the two would
give one test two meanings. Its documented keys were checked by hand this round
(``non_metro_commitment_pct``, ``has_favorable_fee_structure``,
``has_prior_reporting_issues``: all read at
``intelligence/win_probability.py:667-685``). It is listed in
``_UNRESOLVED_ROOTS`` so the boundary is a pinned fact rather than an omission.
"""
from __future__ import annotations

import ast
import json
import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(_REPO_ROOT, "docs")
EXAMPLES_DIR = os.path.join(_REPO_ROOT, "examples")

#: Floors. Well below today's counts so ordinary growth does not trip them,
#: and well above zero so a broken walk does.
MIN_DOCS_FILES = 8
MIN_NOTEBOOKS = 3
MIN_SUBSCRIPTS = 10

#: Roots documented as dict subscripts that this gate deliberately does not
#: resolve, each with the reason. A root appearing in docs/ that is neither a
#: resolvable attribute nor listed here FAILS -- that is what keeps this list
#: from becoming a place to hide a new blind spot.
_UNRESOLVED_ROOTS = {
    "cde_attributes": (
        "an INPUT dict the CDE supplies, not a dict this package returns. "
        "The question to ask of it is whether anything READS the documented "
        "key, which is a different assertion; see this module's docstring. "
        "Hand-checked 1.5.0: non_metro_commitment_pct, "
        "has_favorable_fee_structure and has_prior_reporting_issues are all "
        "read at intelligence/win_probability.py:667-685."
    ),
    "thesis": (
        "a NESTED shape, not a flat return dict: "
        "examples/02_full_application_walkthrough.ipynb binds it to one "
        "element of the list under generate_content()['subsections']. The "
        "resolver below matches a name to a dict; following a subscript into "
        "a list of dicts and back out would make the derivation guess at "
        "which element, and a derivation that guesses is one that can be "
        "wrong quietly. Hand-checked 1.5.0: 'heading' and 'body' both exist "
        "(subsection elements carry body/heading/type)."
    ),
    "to_dataframe": (
        "a pandas DataFrame from Pipeline.to_dataframe(), so its subscripts "
        "are COLUMNS rather than dict keys. Same defect shape, different "
        "corpus and a different accessor; covering it here would give one "
        "test two meanings. Hand-checked 1.5.0: 'sector' and 'state' are "
        "both columns."
    ),
}

_FENCE = re.compile(r"```python\n(.*?)```", re.S)
#: ``name["key"]`` / ``name['key']`` with a plain single-token base. Both quote
#: styles: markdown uses double, the notebooks use single, and a gate that read
#: one of them would have called the notebooks clean without looking.
#:
#: Deliberately does NOT match ``df[["a", "b"]]`` (a list subscript, whose
#: bracket is followed by another) or ``formats=["word"]`` (a list literal,
#: which has no base NAME immediately before the bracket).
_TEXT_SUBSCRIPT = re.compile(
    r"""\b([A-Za-z_][A-Za-z_0-9]*)\[\s*['"]([A-Za-z_][A-Za-z_0-9]*)['"]\s*\]"""
)


# ---------------------------------------------------------------------------
# RIGHT SIDE -- the live dicts
# ---------------------------------------------------------------------------

def _live_roots() -> dict:
    """Build the documented objects and return them by root name.

    Constructed from the packaged sample fixtures, which is what every code
    fence in docs/ tells a reader to construct. If any of these raises, this
    gate ERRORS: an unbuildable root means the gate is checking nothing, and a
    gate that passes while checking nothing is the vacuity this suite keeps
    finding.
    """
    app = Application(cde=CDEProfile.sample(), requested_allocation=50_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    analysis = app.analyze()
    return {
        "analysis": analysis,
        "pipeline_result": analysis.pipeline_result,
        "score": app.score_win_probability(),
        "benchmark": app.benchmark(),
    }


def _returned_dicts() -> dict:
    """Dicts a documented FUNCTION returns, keyed by the method name.

    ``examples/02_full_application_walkthrough.ipynb`` binds
    ``content = section_gen.generate_content(app, analysis)`` and then reads
    ``content["section_id"]``. That is the same promise as an attribute's dict
    and breaks the same way, but it hangs off a CALL rather than an attribute,
    so the attribute sweep cannot see it.

    The key set is the INTERSECTION across every section generator, which is
    the only set a caller looping over ``ALL_SECTIONS`` -- as the notebook does
    -- may rely on. A union would bless a key that exists on one generator and
    raises on the next.
    """
    from nmtcapp.sections import ALL_SECTIONS

    app = Application(cde=CDEProfile.sample(), requested_allocation=50_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    analysis = app.analyze()

    common = None
    for generator in ALL_SECTIONS:
        content = generator.generate_content(app, analysis)
        common = set(content) if common is None else common & set(content)

    assert common, (
        "no key is common to every section generator's generate_content(); "
        "the notebook's loop over ALL_SECTIONS cannot rely on any key and "
        "this half of the gate is checking nothing."
    )
    return {"generate_content": [("sections", {k: None for k in common})]}


def _dict_attributes(roots: dict) -> dict:
    """``{attribute_name: (root_name, the_live_dict)}`` for every dict attribute.

    Derived by introspecting the live objects. Nothing here is hand-listed, so
    an attribute added tomorrow is covered on the next run without anyone
    remembering to add it -- which is rule 4 of tests/test_pinned_constants.py
    (THE LIST IS DERIVED, NOT INHERITED).
    """
    found = {}
    for root_name, obj in roots.items():
        for attr in dir(obj):
            if attr.startswith("_"):
                continue
            try:
                value = getattr(obj, attr)
            except Exception:                      # pragma: no cover - defensive
                continue
            if isinstance(value, dict):
                found.setdefault(attr, []).append((root_name, value))
    return found


# ---------------------------------------------------------------------------
# LEFT SIDE -- what docs/ documents
# ---------------------------------------------------------------------------

def _doc_files() -> list:
    return sorted(
        os.path.join(dirpath, name)
        for dirpath, _dirs, names in os.walk(DOCS_DIR)
        for name in names
        if name.endswith(".md")
    )


def _notebook_files() -> list:
    if not os.path.isdir(EXAMPLES_DIR):
        return []
    return sorted(
        os.path.join(EXAMPLES_DIR, name)
        for name in os.listdir(EXAMPLES_DIR)
        if name.endswith(".ipynb")
    )


def _notebook_code(path: str) -> str:
    """Concatenated source of every CODE cell in a notebook.

    Markdown cells are excluded on purpose: a notebook's prose is documentation
    of the same kind docs/ carries, but its code cells are the half that
    actually RAISES, and keeping them separate would blur which is which. The
    prose is covered by the same detector when the notebook is read as text --
    see ``_scan_text``.
    """
    with open(path, encoding="utf-8") as fh:
        nb = json.load(fh)
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "code"
    )


def _alias_map(tree: ast.AST) -> dict:
    """``{local_name: attribute_name}`` for ``x = <anything>.attribute``.

    Three binding forms, because the docs use all three:

        d = analysis.distress_analysis          ATTRIBUTE  -> 'distress_analysis'
        content = gen.generate_content(app, a)  CALL       -> 'generate_content'
        e = d                                   ALIAS      -> whatever d was

    Resolved transitively, for the reason test_mapper_contract._alias_names
    gives: one intermediate binding defeated that derivation once already, and
    it passed green while the thing it guarded was broken.
    """
    aliases = {}
    for _ in range(8):
        before = len(aliases)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            value = node.value
            if isinstance(value, ast.Attribute):
                aliases[target.id] = value.attr
            elif (isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)):
                aliases[target.id] = value.func.attr
            elif isinstance(value, ast.Name) and value.id in aliases:
                aliases[target.id] = aliases[value.id]
        if len(aliases) == before:
            break
    return aliases


def _scan_text(text: str, code_blocks: list) -> list:
    """Every ``(root, key, line)`` in one file's text.

    Detector A parses ``code_blocks`` to build the alias map; Detector B then
    sweeps the raw text with those aliases resolved. The union is taken
    deliberately: B alone cannot resolve ``d``, and A alone cannot see prose,
    a markdown table cell, or a fence that does not parse.

    Line numbers are reported against the RAW TEXT, so a failure message points
    at the line a reader can open -- which for a notebook is the JSON line
    carrying the cell source.
    """
    aliases = {}
    for block in code_blocks:
        try:
            tree = ast.parse(block)
        except SyntaxError:
            continue                    # Detector B still reads this text.
        aliases.update(_alias_map(tree))

    found = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for base, key in _TEXT_SUBSCRIPT.findall(line):
            found.append((aliases.get(base, base), key, lineno))
    return found


def _subscripts_in(path: str) -> list:
    """Every ``(root, key, line)`` documented in one markdown file or notebook."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    if path.endswith(".ipynb"):
        return _scan_text(text, [_notebook_code(path)])
    return _scan_text(text, [m.group(1) for m in _FENCE.finditer(text)])


def _documented() -> dict:
    """``{(root, key): [(file, line), ...]}`` across docs/ and examples/."""
    documented = {}
    for path in _doc_files() + _notebook_files():
        rel = os.path.relpath(path, _REPO_ROOT)
        for root, key, lineno in _subscripts_in(path):
            documented.setdefault((root, key), []).append((rel, lineno))
    return documented


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def docs_present():
    """The CHECKOUT marker, and it must be BOTH trees or NEITHER.

    MANIFEST.in prunes ``docs`` and ``examples`` together, so the tarball
    carries neither and their joint absence is the sdist. One present and the
    other missing is a checkout with a tree deleted, and that must FAIL rather
    than skip -- an absent directory may never be indistinguishable from a
    clean one, which is the property ``test_fund_attribution_source`` states
    for its own half.
    """
    docs = os.path.isdir(DOCS_DIR)
    examples = os.path.isdir(EXAMPLES_DIR)
    if not docs and not examples:
        pytest.skip(
            "docs/ and examples/ are both absent (this is an unpacked sdist, "
            "not a checkout). MANIFEST.in carries `prune docs` and `prune "
            "examples`, so the tarball ships neither, and this gate asks a "
            "question about the repository."
        )
    assert docs and examples, (
        f"docs/ present={docs}, examples/ present={examples}. MANIFEST.in "
        "prunes both, so in a real sdist neither exists and this gate skips. "
        "Exactly one present means a checkout with a tree deleted, and half "
        "this gate would be silently switched off."
    )
    return True


@pytest.fixture(scope="module")
def registry():
    combined = _dict_attributes(_live_roots())
    for name, entries in _returned_dicts().items():
        combined.setdefault(name, []).extend(entries)
    return combined


@pytest.fixture(scope="module")
def documented(docs_present):
    return _documented()


# ---------------------------------------------------------------------------
# Vacuity guards -- every one of these has a real precedent in this suite
# ---------------------------------------------------------------------------

def test_the_docs_walk_finds_files(docs_present):
    files = _doc_files()
    assert len(files) >= MIN_DOCS_FILES, (
        f"the docs walk found only {len(files)} markdown files under "
        f"{DOCS_DIR}. Every assertion below would be vacuous."
    )


def test_the_notebook_walk_finds_files(docs_present):
    """The half a docs-only gate would have missed, kept non-vacuous."""
    files = _notebook_files()
    assert len(files) >= MIN_NOTEBOOKS, (
        f"the examples walk found only {len(files)} notebooks under "
        f"{EXAMPLES_DIR}. The notebook half of this gate is the one that "
        "found live KeyErrors in 01_quickstart; a zero here switches it off."
    )


def test_the_notebook_code_extraction_is_not_empty(docs_present):
    """A notebook whose code cells yield nothing is a broken extraction."""
    empty = [
        os.path.relpath(p, _REPO_ROOT)
        for p in _notebook_files()
        if not _notebook_code(p).strip()
    ]
    assert not empty, (
        f"extracted no code-cell source from {empty}. Either the notebook "
        "format changed or the extraction broke; both make this gate read "
        "those files as clean."
    )


def test_the_subscript_harvest_is_not_empty(documented):
    assert len(documented) >= MIN_SUBSCRIPTS, (
        f"harvested only {len(documented)} documented dict subscripts from "
        "docs/. The detectors are broken; a silent zero here is the shape of "
        "round nine's grep against the wrong path set."
    )


def test_the_dict_attribute_registry_has_no_name_collisions(registry):
    """Matching by attribute name is only sound while names are unique."""
    collisions = {
        attr: [root for root, _ in entries]
        for attr, entries in registry.items()
        if len(entries) > 1
    }
    assert not collisions, (
        f"two root objects now expose a dict under the same attribute name: "
        f"{collisions}. This gate resolves a documented `x[\"k\"]` by "
        "attribute name alone, so a collision makes the resolution ambiguous "
        "and the assertion below could check the wrong dict. Disambiguate the "
        "resolution before adding the attribute."
    )


def test_the_live_roots_all_expose_dicts(registry):
    roots = {root for entries in registry.values() for root, _ in entries}
    assert roots == {"analysis", "pipeline_result", "score", "benchmark",
                     "sections"}, (
        f"expected every documented root to contribute dicts; got "
        f"{sorted(roots)}. A root contributing nothing means its half of this "
        "gate is switched off -- which is how a docs-only scope would have "
        "left the notebooks uncovered."
    )


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------

def test_every_documented_key_exists(registry, documented):
    """A key docs/ tells a caller to read must exist in the dict it names.

    THE ASSERTION F3 NEEDED. ``g["urban_pct"]`` was documented after the key
    was deleted from ``geographic_diversity``; this is the line that goes red
    on that.
    """
    missing = []
    for (root, key), sites in sorted(documented.items()):
        if root not in registry:
            continue                    # ruled by the boundary test below
        _root_name, live = registry[root][0]
        if key not in live:
            where = ", ".join(f"{f}:{n}" for f, n in sites)
            missing.append(
                f"  {root}[\"{key}\"]  documented at {where}\n"
                f"      {root} actually returns: {sorted(live)}"
            )

    assert not missing, (
        f"{len(missing)} key(s) documented in docs/ or examples/ do not exist "
        "in the dict "
        "the documentation names. A caller who writes the documented line "
        "gets a KeyError, in their own code, with nothing pointing back "
        "here.\n\nFix the DOCS to match the code, or restore the key -- do "
        "not delete this test.\n\n" + "\n".join(missing)
    )


def test_the_unresolved_roots_are_the_documented_ones(registry, documented):
    """A documented subscript root must be resolvable, or listed with a reason.

    Without this, ``test_every_documented_key_exists`` would silently skip any
    root it could not resolve -- so renaming a returned attribute would take
    its documented keys OUT of the gate's scope rather than failing it, and the
    gate would go green on exactly the change it exists to catch.
    """
    unresolved = sorted({
        root for (root, _key) in documented
        if root not in registry and root not in _UNRESOLVED_ROOTS
    })
    assert not unresolved, (
        f"docs/ or examples/ documents dict subscripts on {unresolved}, which "
        "this gate "
        "cannot resolve to a live dict and which are not listed in "
        "_UNRESOLVED_ROOTS.\n\nEither the attribute was renamed (in which case "
        "the docs are stale and the keys under it are unguarded), or it is a "
        "new kind of dict that needs a ruling. Add it to _UNRESOLVED_ROOTS "
        "WITH A REASON, or make it resolvable. Do not leave it unlisted: an "
        "unresolved root is a silently uncovered one."
    )


def test_the_boundary_list_is_still_live(documented):
    """A ruled exception that no longer appears in docs/ is a stale ruling."""
    dead = sorted(
        root for root in _UNRESOLVED_ROOTS
        if not any(r == root for r, _k in documented)
    )
    assert not dead, (
        f"_UNRESOLVED_ROOTS names {dead}, which the scanned corpus no longer "
        "documents. A "
        "ruling that guards nothing reads as coverage; delete the entry."
    )


# ---------------------------------------------------------------------------
# DETECTOR A'S BLIND SPOT, MEASURED RATHER THAN DESCRIBED (1.5.0 T3)
# ---------------------------------------------------------------------------

#: Files where Detector A is STRUCTURALLY INERT, and how many fences in each.
#:
#: ``docs/reference/api.md`` is a signature reference. Its fences hold
#: declarations, not statements -- ``Application(cde: CDEProfile, ...)`` and
#: ``score_win_probability() -> WinProbabilityScore`` are not valid Python and
#: never will be. ``ast.parse`` raises SyntaxError on every one, ``_scan_text``
#: hits its ``continue``, and the alias map for that entire file is empty on
#: EVERY interpreter. This is not the environment class: it is invariant.
#:
#: The gate is therefore DEGRADED, NOT BLIND -- Detector B sweeps the same raw
#: text and still reports subscripts from it. But a half-off gate reads as a
#: whole one, and this project has shipped that reading before. So the
#: inertness is pinned as a NUMBER here rather than left as a sentence in the
#: module docstring, where it could drift silently: if a fence in api.md
#: becomes parseable, or a new unparseable fence appears in a file that had
#: none, this fails and somebody states which detector now covers what.
_DETECTOR_A_INERT_FENCES = {"docs/reference/api.md": 20}

#: Total ``python`` fences across ``_doc_files()``, pinned for the same reason:
#: it is the denominator that makes the number above mean something. Twenty
#: unparseable out of 73 is a quarter of the corpus; twenty out of 5,000 would
#: not be worth a comment. Measured, not estimated.
#:
#: 72 -> 73 in the 1.5.1 audit round (B2). The added fence is the one-liner in
#: docs/workflow/recommendations.md showing a reader how to enumerate the
#: categories the engine ACTUALLY emits -- added because that page documented
#: five categories the engine cannot emit, so the correction is worth
#: something only if a reader can check it against their own install. It
#: parses, so Detector A's inert count is unchanged.
_TOTAL_PYTHON_FENCES = 73


def test_detector_A_is_inert_on_exactly_the_files_this_gate_says_it_is(docs_present):
    """The silently-halved half, asserted (1.5.0 T3).

    Detector A resolves aliases so that ``d = analysis.distress_analysis``
    makes every later ``d["k"]`` a read of ``distress_analysis``. It can only
    do that for fences that PARSE. Where none parses, the file is covered by
    Detector B alone -- prose-and-table matching with no alias resolution --
    and any subscript written through a local binding there is invisible to
    this gate entirely.

    That is a real and acceptable limitation. What is NOT acceptable is it
    being invisible: a reader seeing "DETECTOR A (AST)" in the module docstring
    has no way to learn that it contributes nothing to a quarter of the corpus.
    """
    counted = {}
    total = 0
    for path in _doc_files():
        rel = os.path.relpath(path, _REPO_ROOT)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for match in _FENCE.finditer(text):
            total += 1
            try:
                ast.parse(match.group(1))
            except SyntaxError:
                counted[rel] = counted.get(rel, 0) + 1

    assert total, (
        "no ``python`` fences found under docs/ at all. The fence regex or the "
        "walk is broken, and every assertion below would pass over nothing."
    )
    assert total == _TOTAL_PYTHON_FENCES, (
        f"docs/ now holds {total} ``python`` fences, not "
        f"{_TOTAL_PYTHON_FENCES}. That is fine -- but the unparseable count "
        "below is only interpretable against a stated denominator, so update "
        "both together and say what moved."
    )
    assert counted == _DETECTOR_A_INERT_FENCES, (
        f"the set of fences Detector A cannot parse has MOVED.\n\n"
        f"  recorded: {_DETECTOR_A_INERT_FENCES}\n"
        f"  measured: {counted}\n\n"
        "Detector A is structurally inert for any file listed here -- its "
        "alias map is empty, so subscripts written through a local binding in "
        "that file are covered by NOTHING. Detector B still reads the raw "
        "text, so the gate is degraded rather than blind.\n\n"
        "If a NEW file appears above, say in the docstring which detector "
        "covers it and why that is enough. If a count DROPPED because a fence "
        "became parseable, that is a coverage improvement -- record the new "
        "number. Do not delete this assertion to make it pass: it exists "
        "because a silently-halved gate reads as a whole one."
    )


# ---------------------------------------------------------------------------
# THE SAME CLASS, ONE SHAPE WIDER: a stale DATAFRAME COLUMN in a notebook
# (1.5.5 audit close)
# ---------------------------------------------------------------------------
#
# WHAT THIS MODULE ALREADY SAID, AND WHERE IT FELL SHORT. The header above
# states the case for scanning ``examples/`` in as many words: "A stale key in
# a markdown fence is a wrong instruction. A stale key in a notebook is
# EXECUTABLE CODE THAT RAISES." It was right, and it did not go far enough.
# Detector A resolves ``<root>["literal"]``. It cannot see
#
#     cols = ["Project Name", "State", "Sector (NAICS)", ...]
#     display(df_pipeline[cols].head(8))
#
# because the subscript's slice is a NAME, and the literals sit one binding
# away in a list. That is not a hypothetical shape. It is
# ``examples/02_full_application_walkthrough.ipynb`` cell 14, and it has been
# raising ``KeyError: "['Sector (NAICS)'] not in index"`` since ad2c7ba
# (2026-08-14) renamed the column to "Sector (as supplied)" -- because the tool
# was inventing the NAICS code it filed. The rename was right. The notebook was
# never updated, no gate looked, and the walkthrough has shipped broken through
# four releases.
#
# FOUND BY EXECUTING THE NOTEBOOKS, which is what the 1.5.5 audit-close brief
# asked for on a different question entirely (the CY2025 round literal). The
# round fix touches cell 3; this defect is in cell 14 and is unrelated to it.
# Both notebooks were executed before and after that fix and the error set is
# identical, so this is pre-existing at c5f546b and is recorded as its own
# finding rather than folded into the round work.
#
# WHY THE GATE IS NOT "EXECUTE THE NOTEBOOKS IN CI". That would catch this and
# much more, and it is the wrong trade here: the walkthrough renders four
# document formats and takes the better part of a minute, on four interpreters,
# for a check whose failure mode is a renamed string. The invariant that
# actually matters is narrower and is derivable on both sides with no
# execution at all -- which is this module's whole method.
#
#   LEFT SIDE   Every string literal a notebook uses as a column selector ON A
#               VARIABLE IT BOUND FROM A ``build_*`` CALL: directly
#               (``df["X"]``), as a list (``df[["X","Y"]]``), or through a
#               local list binding (``cols = [...]; df[cols]``). Both alias
#               resolutions are the same idiom ``_alias_map`` uses for
#               attributes, for the same stated reason: a derivation one
#               binding defeats checks nothing. The variable map is built
#               across the WHOLE notebook, because a notebook's cells share
#               one namespace and the binding is routinely cells away from
#               the use.
#
#   RIGHT SIDE  The columns THAT BUILDER produces, read off a LIVE DataFrame
#               built from the packaged fixtures. Nothing is written down here.
#
# NOT A SHAPE HEURISTIC, and the first draft of this gate was one. It filtered
# candidate literals to those containing a space or a parenthesis, on the
# stated ground that every column has one -- and its own self-check
# immediately falsified that: ``City``, ``State``, ``Sector``, ``Sectors``,
# ``Notes``, ``OZ`` and ``HMR`` are all real columns. A filter that wrong
# would have hidden a stale one-word column, which is the defect class the
# gate exists for. Binding the subscript to the builder that produced it needs
# no filter at all: a subscript on anything else is simply not a candidate,
# and the comparison is against that builder's own column set rather than
# against the union.
#
# FAILS CLOSED the same ways the rest of this module does: an empty builder
# harvest errors, an empty selector harvest errors, and the scan runs only
# under the ``docs_present`` checkout marker.


def _live_table_columns() -> dict:
    """``{builder_name: [columns]}`` for every table builder, from live frames.

    Built from the packaged fixtures rather than from a recorded list, so a
    renamed column moves the right side of this gate on its own.

    Example::

        _live_table_columns()["build_pipeline_table"]
    """
    import importlib
    import pkgutil

    import nmtcapp.tables as tables_pkg

    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=20)
    app = Application(cde=cde, requested_allocation=65_000_000)
    app.add_pipeline(pipeline)
    analysis = app.analyze()

    # The builders take different shapes; try each in turn rather than
    # hard-coding a signature per builder, which would go stale the way
    # everything hand-typed in this repository has.
    candidate_args = [(pipeline, cde), (cde,), (analysis,), (app,), (pipeline,), ()]

    produced = {}
    for module_info in pkgutil.iter_modules(tables_pkg.__path__):
        module = importlib.import_module(f"nmtcapp.tables.{module_info.name}")
        for name, fn in vars(module).items():
            if not (name.startswith("build_") and callable(fn)):
                continue
            for args in candidate_args:
                try:
                    frame = fn(*args)
                except Exception:
                    continue
                if hasattr(frame, "columns"):
                    produced[name] = list(frame.columns)
                break
    return produced


def _frame_variables(cells: list, builders: set) -> dict:
    """``{local_name: builder_name}`` for ``df = build_x(...)`` across a notebook.

    Whole-notebook, not per-cell: cells share one namespace and the binding is
    routinely several cells above the use.

    Example::

        _frame_variables(nb["cells"], {"build_pipeline_table"})
    """
    bound = {}
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        for node in ast.walk(ast.parse("".join(cell.get("source", [])))):
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Call)):
                continue
            fn = node.value.func
            name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
            if name in builders:
                bound[node.targets[0].id] = name
    return bound


def _notebook_column_selectors() -> list:
    """``(location, builder, literal)`` for every column selected on a frame.

    Example::

        _notebook_column_selectors()[:1]
    """
    builders = set(_live_table_columns())
    found = []
    for path in _notebook_files():
        with open(path, encoding="utf-8") as fh:
            cells = json.load(fh).get("cells", [])
        frame_vars = _frame_variables(cells, builders)
        label = os.path.basename(path)
        for index, cell in enumerate(cells):
            if cell.get("cell_type") != "code":
                continue
            tree = ast.parse("".join(cell.get("source", [])))

            # ``name = ["A", "B"]`` -- the binding Detector A cannot follow.
            list_alias = {}
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                        and isinstance(node.targets[0], ast.Name)
                        and isinstance(node.value, (ast.List, ast.Tuple))):
                    continue
                literals = [e.value for e in node.value.elts
                            if isinstance(e, ast.Constant)
                            and isinstance(e.value, str)]
                if literals:
                    list_alias[node.targets[0].id] = literals

            for node in ast.walk(tree):
                if not (isinstance(node, ast.Subscript)
                        and isinstance(node.value, ast.Name)
                        and node.value.id in frame_vars):
                    continue
                slice_node = node.slice
                if isinstance(slice_node, ast.Constant) and \
                        isinstance(slice_node.value, str):
                    picks = [slice_node.value]
                elif isinstance(slice_node, ast.Name):
                    picks = list_alias.get(slice_node.id, [])
                elif isinstance(slice_node, (ast.List, ast.Tuple)):
                    picks = [e.value for e in slice_node.elts
                             if isinstance(e, ast.Constant)
                             and isinstance(e.value, str)]
                else:
                    picks = []
                for literal in picks:
                    found.append(
                        (f"{label} cell {index}", frame_vars[node.value.id], literal)
                    )
    return found


def test_the_table_column_harvest_is_not_empty(docs_present):
    """Fails closed: silence on either side must not read as cleanliness."""
    produced = _live_table_columns()
    assert produced, (
        "no build_* function under nmtcapp/tables/ returned a DataFrame. The "
        "right side of the column gate is empty and it would pass over nothing."
    )
    assert _notebook_column_selectors(), (
        "no column selectors harvested from examples/*.ipynb at all. Either "
        "the notebook walk, the frame-variable map or the subscript harvest "
        "is broken, and the gate below would pass over nothing."
    )


def test_every_notebook_column_selector_exists_in_a_real_table(docs_present):
    """A column an example notebook selects must be one that builder produces.

    THE FAILURE THIS CATCHES is not a typo in a doc. It is a cell that raises
    ``KeyError`` in the reader's own notebook, in the walkthrough ``README.md``
    links as the front door.
    """
    produced = _live_table_columns()
    stale = [
        f"{where}: {builder}(...)[{literal!r}]"
        for where, builder, literal in _notebook_column_selectors()
        if literal not in produced[builder]
    ]
    assert not stale, (
        "an example notebook selects a DataFrame column its builder does not "
        "produce. The cell raises KeyError when a reader runs it:\n  "
        + "\n  ".join(stale)
        + "\n\nThe columns that DO exist are whatever the builder returns "
          "today; if a column was deliberately renamed, the notebook is part "
          "of the rename."
    )
