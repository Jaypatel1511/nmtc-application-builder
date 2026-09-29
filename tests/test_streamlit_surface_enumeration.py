"""THE APP'S SURFACE LIST, DERIVED FROM THE DIRECTORY -- NOT FROM MEMORY (1.7.2 F4).

THE DEFECT
==========

The 1.7.1 settle read found that the enumeration kept to stop an unread
surface was itself wrong. ``02_current_state`` recorded "five prose entry
points across four pages" and tabled them. Two of those facts were false:

  * ``streamlit_app/utils.py:119`` is NOT a call site. It is a line inside
    ``md()``'s DOCSTRING, under ``Example::``. A documentation example was
    counted as a rendering surface.
  * The app has FIVE pages, not four. ``streamlit_app/app.py`` (Home) and
    ``pages/3_Pipeline_Optimizer.py`` both render prose -- and neither was in
    the table. They are the two pages the settle read then found defects on
    (F2, F3).

The instrument behind it was

    grep -rn "q25_basis_note\\|round_provenance_paragraphs" streamlit_app/ docs/

which enumerates two FUNCTION NAMES, not the surfaces. A page that calls
neither is invisible to it by construction, and both defective pages called
neither.

WHAT THIS GATE DOES INSTEAD
===========================

1. It counts pages FROM THE FILESYSTEM: ``streamlit_app/app.py`` plus every
   ``streamlit_app/pages/*.py``. A page is a surface whether or not it calls
   any renderer. Every page on disk must be classified in ``PAGE_REGISTRY``
   below, and every registry entry must be a page on disk -- both directions.
2. It reads ``st.navigation``'s ``st.Page`` list out of ``app.py`` and requires
   it to name exactly the files on disk: a page file the navigation does not
   list is unreachable, and a navigation entry with no file is a dead link.
3. It walks each page's AST for every PROSE RENDER SITE -- ``st.markdown``,
   ``st.write``, ``st.caption``, ``st.info``, ``st.warning``, ``st.error``,
   ``st.success``, ``st.title``/``header``/``subheader``, ``st.text``,
   ``st.toast``, ``st.expander`` labels, the same calls on ``st.sidebar`` and
   on layout containers (``col.caption(...)``), and the ``utils`` helpers that
   render prose on a page's behalf. The count per page is pinned in the
   registry, so a new prose site is a REVIEW EVENT: the failure prints the
   derived site list, and whoever adds one re-reads it against the rules the
   other gates in this directory enforce (round provenance, the winner-pattern
   disclosure, the version stamp) before bumping the number.
4. Because it walks the AST, a docstring can never be counted as a site --
   which is the ``utils.py:119`` error, asserted explicitly below.

WHAT IT DOES NOT DO
===================

It does not read what a site SAYS. That is the job of the rendered gates:
``tests/test_streamlit_page_provenance.py`` (every page renders the version
stamp and the round-provenance note, 1.7.2 F1/F3) and
``tests/test_winner_pattern_claims.py`` (no surface claims the house winner
constants are measurements of past winners, 1.7.2 F2). This file guarantees
those gates are run over the RIGHT LIST.

A string built far from its render call and passed in as a variable is still
a site here (the call is what is counted), but its words are only visible to
the rendered gates. Charts' own text (matplotlib ``ax.text``, plotly titles)
is not counted: it is drawn, not rendered as prose, and
``tests/test_streamlit_chart_smoke.py`` owns it.

It runs identically in a checkout and in the sdist job, which copies
``streamlit_app/`` out of the tarball beside ``tests/``.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _REPO_ROOT / "streamlit_app"

#: Calls on ``st`` (or ``st.sidebar``) that put user-facing prose on a page.
ST_PROSE_CALLS = frozenset({
    "markdown", "write", "caption", "info", "warning", "error", "success",
    "title", "header", "subheader", "text", "toast", "expander",
})

#: The same, on a layout container (``left.markdown``, ``c3.caption``). Kept
#: narrower than the ``st`` set on purpose: ``ax.text`` is matplotlib, and
#: ``str.title()`` is not a render call.
CONTAINER_PROSE_CALLS = frozenset({
    "markdown", "write", "caption", "info", "warning", "error", "success",
})

#: ``streamlit_app/utils.py`` functions that render prose ON A PAGE'S BEHALF.
#: A page that calls one of these renders what it renders, so each call is a
#: site on the calling page. ``test_every_prose_helper_in_utils_is_listed``
#: re-derives this set from utils.py so a new helper cannot hide from it.
PROSE_HELPERS = frozenset({
    "render_methodology_warning",
    "render_methodology_disclosure",
    "render_version_stamp",
    "metric_classification",
})

#: A first argument that is a string literal starting with one of these is
#: layout, not prose: a ``<style>`` block, a ``<br>``, a ``---`` divider.
_NON_PROSE_PREFIXES = ("<style", "<br>", "---")

#: The functions whose output IS the round-provenance / Question 25 note. A
#: call to one of these is the thing the old grep counted; it is recorded
#: here per page so the old enumeration's question still has an answer --
#: from the AST, not from a grep over docstrings.
PROVENANCE_FUNCTIONS = frozenset({"round_provenance_paragraphs", "q25_basis_note"})


#: EVERY PAGE, CLASSIFIED. Keyed by path relative to ``streamlit_app/``.
#:
#: ``nav_title``        the title ``app.py``'s ``st.Page`` gives it.
#: ``prose_sites``      the number of prose render sites the AST walk finds.
#:                      A REVIEW TRIGGER, not a measurement to nudge: if it
#:                      moved, read the new site before changing the number.
#: ``provenance_calls`` calls to ``round_provenance_paragraphs`` /
#:                      ``q25_basis_note`` on that page.
#: ``what``             what the page is for, in one line.
PAGE_REGISTRY = {
    "app.py": {
        "nav_title": "Home",
        "prose_sites": 11,
        "provenance_calls": 1,
        "what": "landing page: feature cards, getting-started steps, the "
                "sample CDE, and the Methodology Disclosure",
    },
    "pages/1_Pipeline_Analyzer.py": {
        "nav_title": "Pipeline Analyzer",
        "prose_sites": 66,
        "provenance_calls": 2,
        "what": "load or upload a pipeline, run the analysis, read the "
                "distress / geography / sector / impact report and the "
                "post-analysis Question 25 basis note",
    },
    "pages/2_Win_Alignment_Scorer.py": {
        "nav_title": "Win Alignment Scorer",
        "prose_sites": 39,
        "provenance_calls": 1,
        "what": "score the application against the CY 2024-2025 Review "
                "Process structure",
    },
    "pages/3_Pipeline_Optimizer.py": {
        "nav_title": "Pipeline Optimizer",
        "prose_sites": 26,
        "provenance_calls": 1,
        "what": "select the highest-scoring project subset under QEI, state "
                "and sector constraints",
    },
    "pages/4_About_and_Methodology.py": {
        "nav_title": "About and Methodology",
        "prose_sites": 25,
        "provenance_calls": 1,
        "what": "data sources, scoring methodology, limitations, round "
                "provenance",
    },
}


def page_files() -> list:
    """Every page module on disk, as a path relative to ``streamlit_app/``.

    Home is ``app.py`` -- the navigation entry point defines it as a function
    and marks it ``default=True`` -- and every ``pages/*.py`` is a page.
    """
    assert _APP_DIR.is_dir(), (
        f"{_APP_DIR} is absent. The sdist job copies streamlit_app/ out of "
        "the tarball beside tests/; a run without it cannot enumerate the app."
    )
    found = []
    if (_APP_DIR / "app.py").is_file():
        found.append("app.py")
    found.extend(
        f"pages/{p.name}" for p in sorted((_APP_DIR / "pages").glob("*.py"))
    )
    return found


def _root_name(node):
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def prose_sites(relpath: str) -> list:
    """``[(lineno, kind), ...]`` for every prose render site in one page.

    Walks the AST, so a docstring or a comment can never be counted.
    """
    tree = ast.parse((_APP_DIR / relpath).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        kind = None
        if isinstance(func, ast.Attribute):
            root = _root_name(func.value)
            if root == "st" and func.attr in ST_PROSE_CALLS:
                prefix = "st.sidebar." if isinstance(func.value, ast.Attribute) else "st."
                kind = prefix + func.attr
            elif (root not in (None, "st") and isinstance(func.value, ast.Name)
                  and func.attr in CONTAINER_PROSE_CALLS):
                kind = f"<{func.value.id}>.{func.attr}"
        elif isinstance(func, ast.Name) and func.id in PROSE_HELPERS:
            kind = f"{func.id}()"
        if kind is None:
            continue
        first = node.args[0] if node.args else None
        if (isinstance(first, ast.Constant) and isinstance(first.value, str)
                and first.value.strip().startswith(_NON_PROSE_PREFIXES)):
            continue
        if (isinstance(first, ast.Call) and isinstance(first.func, ast.Name)
                and first.func.id == "md"):
            kind += " (md)"
        out.append((node.lineno, kind))
    return sorted(out)


def provenance_calls(relpath: str) -> list:
    """Line numbers of every call to a round-provenance / Q25 function."""
    tree = ast.parse((_APP_DIR / relpath).read_text(encoding="utf-8"))
    return sorted(
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) in PROVENANCE_FUNCTIONS
             or getattr(node.func, "attr", None) in PROVENANCE_FUNCTIONS)
    )


def enumeration_table() -> str:
    """The whole enumeration, page -> render sites, as printable text."""
    lines = []
    for rel in page_files():
        sites = prose_sites(rel)
        prov = provenance_calls(rel)
        lines.append(f"{rel}  ({len(sites)} prose sites; provenance/Q25 calls "
                     f"at {prov or 'none'})")
        lines.extend(f"    :{ln:<5} {kind}" for ln, kind in sites)
    return "\n".join(lines)


def _navigation_targets() -> dict:
    """``{relpath: title}`` for every ``st.Page(...)`` in app.py.

    A callable target (Home is ``st.Page(home, ...)``) resolves to
    ``app.py``, the module that defines it.
    """
    tree = ast.parse((_APP_DIR / "app.py").read_text(encoding="utf-8"))
    targets = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "Page" and _root_name(node.func) == "st"):
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            rel = first.value
        elif isinstance(first, ast.Name):
            rel = "app.py"
        else:  # pragma: no cover - a shape app.py has never used
            raise AssertionError(f"unrecognised st.Page target at app.py:{node.lineno}")
        title = next((kw.value.value for kw in node.keywords
                      if kw.arg == "title" and isinstance(kw.value, ast.Constant)), None)
        assert rel not in targets, f"{rel} is listed twice in st.navigation"
        targets[rel] = title
    return targets


# ---------------------------------------------------------------------------
# The list itself
# ---------------------------------------------------------------------------

def test_the_app_has_the_pages_the_directory_has():
    """Anti-vacuity: the walk found the app, and more than one page."""
    pages = page_files()
    assert "app.py" in pages, "streamlit_app/app.py (Home) was not found"
    assert len(pages) >= 2, f"the enumeration found only {pages}"


def test_every_page_on_disk_is_classified_and_every_entry_is_a_page():
    """Count pages FROM THE DIRECTORY. Both directions."""
    on_disk = set(page_files())
    registered = set(PAGE_REGISTRY)
    unclassified = sorted(on_disk - registered)
    phantom = sorted(registered - on_disk)
    assert not unclassified and not phantom, (
        "streamlit_app/ and PAGE_REGISTRY disagree about which pages exist.\n"
        f"  on disk, not classified: {unclassified}\n"
        f"  classified, not on disk: {phantom}\n\n"
        "A page is a surface whether or not it calls any renderer -- the "
        "1.7.1 settle read found its two defective pages were exactly the two "
        "an enumeration by function name could not see. Classify the new "
        "page in PAGE_REGISTRY (and in the rendered gates' page lists) rather "
        "than deleting the entry for a page that moved.\n\n"
        f"The derived enumeration:\n{enumeration_table()}"
    )


def test_the_navigation_lists_exactly_the_pages_on_disk():
    """A page file the navigation omits is unreachable; an entry with no
    file is a dead link. Titles must match the registry."""
    nav = _navigation_targets()
    assert set(nav) == set(page_files()), (
        f"st.navigation lists {sorted(nav)}; the directory has "
        f"{sorted(page_files())}"
    )
    wrong = {rel: (title, PAGE_REGISTRY[rel]["nav_title"])
             for rel, title in nav.items()
             if rel in PAGE_REGISTRY and PAGE_REGISTRY[rel]["nav_title"] != title}
    assert not wrong, f"navigation titles disagree with PAGE_REGISTRY: {wrong}"


@pytest.mark.parametrize("relpath", sorted(PAGE_REGISTRY))
def test_the_prose_render_sites_are_the_ones_classified(relpath):
    """The per-page count is a review trigger. Read the new site; then move it."""
    if not (_APP_DIR / relpath).is_file():
        pytest.fail(f"{relpath} is registered but absent -- see the "
                    "both-directions test above")
    sites = prose_sites(relpath)
    expected = PAGE_REGISTRY[relpath]["prose_sites"]
    assert len(sites) == expected, (
        f"{relpath} has {len(sites)} prose render sites; PAGE_REGISTRY "
        f"records {expected}.\n\nRead the sites that were added or removed "
        "against the round-provenance, version-stamp and winner-pattern "
        "gates BEFORE changing the number -- a count moved to make this pass "
        "without reading the site is the grep this file replaced.\n\n"
        + "\n".join(f"    :{ln:<5} {kind}" for ln, kind in sites)
    )


@pytest.mark.parametrize("relpath", sorted(PAGE_REGISTRY))
def test_the_provenance_call_count_is_the_one_classified(relpath):
    """The old enumeration's own question, answered from the AST."""
    calls = provenance_calls(relpath)
    expected = PAGE_REGISTRY[relpath]["provenance_calls"]
    assert len(calls) == expected, (
        f"{relpath} calls round_provenance_paragraphs / q25_basis_note at "
        f"{calls or 'no line'}; PAGE_REGISTRY records {expected}"
    )


def test_a_docstring_is_not_a_surface():
    """``utils.py``'s ``md()`` docstring carries a provenance call under
    ``Example::``. The old enumeration counted it as a site. The AST walk
    must not -- and the text must actually still be there, or this proves
    nothing."""
    utils_src = (_APP_DIR / "utils.py").read_text(encoding="utf-8")
    assert "st.info(md(round_provenance_paragraphs()[0]))" in utils_src, (
        "the md() docstring example this test exists for has moved; find "
        "another docstring-only occurrence to anchor on rather than deleting "
        "the check"
    )
    assert provenance_calls("utils.py") == [], (
        "the AST walk counts a call in utils.py; utils.py carries the "
        "provenance call only inside md()'s docstring"
    )


def test_every_prose_helper_in_utils_is_listed():
    """A utils function that renders prose is a site on every page that
    calls it; a new one must join PROSE_HELPERS or it is invisible above.

    Derived: any top-level function in utils.py whose body makes a prose
    render call on ``st`` or on a parameter (a container passed in).
    """
    tree = ast.parse((_APP_DIR / "utils.py").read_text(encoding="utf-8"))
    rendering = set()
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        params = {a.arg for a in fn.args.args}
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            root = _root_name(node.func.value)
            if node.func.attr in CONTAINER_PROSE_CALLS | {"metric"} and (
                    root == "st" or root in params):
                first = node.args[0] if node.args else None
                if (isinstance(first, ast.Constant) and isinstance(first.value, str)
                        and first.value.strip().startswith(_NON_PROSE_PREFIXES)):
                    continue
                rendering.add(fn.name)
    assert rendering == set(PROSE_HELPERS), (
        f"utils.py functions that render prose: {sorted(rendering)}; "
        f"PROSE_HELPERS lists {sorted(PROSE_HELPERS)}"
    )


if __name__ == "__main__":  # pragma: no cover - a reporting aid
    # ``python tests/test_streamlit_surface_enumeration.py`` prints the table
    # this file derives, so the next settle read is run from it rather than
    # from a list in a knowledge file.
    print(enumeration_table())
