"""Render every Streamlit page the way a CDE walks them, once per session.

Shared by ``tests/test_streamlit_page_provenance.py`` (1.7.2 F1/F3 -- every
page carries the version stamp and the round-provenance note) and
``tests/test_winner_pattern_claims.py`` (1.7.2 F2 -- no page claims the house
winner constants are measurements of past winners). Not a test module itself:
it collects nothing.

WHAT IS RENDERED
================

Every page in ``test_streamlit_surface_enumeration.page_files()`` -- the list
counted from the directory, so a new page cannot be skipped here -- in two
states:

  ``cold``    the page as it first loads, nothing clicked. Page 3 calls
              ``st.stop()`` before its results; anything that must be on every
              page has to be on this render.
  ``driven``  the page after the action a CDE takes on it, with session state
              carried forward exactly as ``tests/test_streamlit_page_drive.py``
              carries it:
                * page 1 -- sample data, "Run Analysis" (the Question 25 basis
                  note lives in an expander that exists only after this);
                * page 2 -- "Score Application", then "Generate
                  recommendations" (the recommendations name the house
                  winner-pattern bands);
                * page 3 -- "Run Optimizer" (its methodology expander renders
                  ``OptimizationResult.methodology_note``);
                * Home and page 4 have no action; ``driven`` is ``cold``.

It runs Streamlit's in-process ``AppTest`` against the real page files --
the same harness, and the same scope limits (no browser, no Streamlit Cloud),
recorded at length in ``tests/test_streamlit_page_drive.py``. Home is run
through ``app.py`` itself, whose ``st.navigation`` renders it as the default
page. Nothing is patched.

NETWORK. Page 1's analysis asks nmtc-mapper for eligibility data; with the
download unavailable it takes its degraded path and still renders. Nothing
here is conditional on the network.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _REPO_ROOT / "streamlit_app"
for _p in (str(_REPO_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: Element kinds whose ``.value`` is prose a CDE reads.
PROSE_KINDS = ("title", "header", "subheader", "markdown", "caption", "info",
               "warning", "success", "error", "text", "toast")

#: The button each page's CDE clicks, in order. Pages absent here have none.
_ACTIONS = {
    "pages/1_Pipeline_Analyzer.py": ("▶  Run Analysis",),
    "pages/2_Win_Alignment_Scorer.py": ("▶  Score Application", "Generate recommendations"),
    "pages/3_Pipeline_Optimizer.py": ("▶  Run Optimizer",),
}

#: Session keys page 1 leaves behind that the downstream pages read.
_CARRIED = ("app", "is_demo_data", "allocation_is_stated", "analysis")


#: Elements whose LABEL (and help tooltip) is prose a CDE reads, beyond the
#: body kinds above. Fix round 1 (P9/X5): st.code, st.metric labels and help,
#: st.dataframe headers, tab and expander labels and every widget's label and
#: help= tooltip were outside the scan -- 1_Pipeline_Analyzer renders the
#: readiness-withdrawal disclosure as st.code.
LABELLED_KINDS = ("expander", "tabs", "metric", "button", "radio", "slider",
                  "select_slider", "number_input", "multiselect", "selectbox",
                  "checkbox", "toggle", "text_input", "text_area",
                  "date_input", "color_picker")


def texts(at) -> list:
    """``[(kind, text), ...]`` for every piece of prose the page rendered:
    bodies, code blocks, labels, help tooltips and table headers."""
    out = []
    for kind in PROSE_KINDS:
        for el in getattr(at, kind, []):
            value = getattr(el, "value", None)
            if isinstance(value, str):
                out.append((kind, value))
    for el in getattr(at, "code", []):
        value = getattr(el, "value", None)
        if isinstance(value, str):
            out.append(("code", value))
    for kind in LABELLED_KINDS:
        for el in getattr(at, kind, []):
            for attr in ("label", "help"):
                text = getattr(el, attr, None)
                if isinstance(text, str) and text.strip():
                    out.append((f"{kind}.{attr}", text))
    for kind in ("dataframe", "table"):
        for el in getattr(at, kind, []):
            value = getattr(el, "value", None)
            columns = getattr(value, "columns", None)
            if columns is not None:
                out.append((f"{kind}.columns", " | ".join(str(c) for c in columns)))
    out.extend(("html", body) for body in html_bodies(at))
    return out


def html_bodies(at) -> list:
    """Bodies of every ``st.html`` element (fix round 2). AppTest has no
    ``at.html`` accessor -- on streamlit 1.50 and 1.64 alike it reports the
    element as an ``UnknownElement`` of type "html" whose proto carries the
    body -- so it is read off the element tree. No page uses st.html today;
    this is so the first one that does is scanned rather than invisible."""
    bodies = []

    def walk(node):
        children = getattr(node, "children", None)
        if not isinstance(children, dict):
            return
        for child in children.values():
            if (type(child).__name__ == "UnknownElement"
                    and getattr(child, "type", None) == "html"):
                body = getattr(child.proto, "body", "")
                if isinstance(body, str) and body.strip():
                    bodies.append(body)
            walk(child)

    walk(at._tree)
    return bodies


def _click(at, label: str) -> None:
    for button in at.button:
        if button.label == label:
            button.click().run()
            return
    raise AssertionError(
        f"no button labelled {label!r}; the page offers "
        f"{[b.label for b in at.button]}"
    )


def _run(relpath: str, carried=None):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(_APP_DIR / relpath), default_timeout=300)
    for key, value in (carried or {}).items():
        at.session_state[key] = value
    at.run()
    return at


@functools.lru_cache(maxsize=1)
def rendered_pages() -> dict:
    """``{relpath: {"cold": AppTest, "driven": AppTest}}`` for every page."""
    from tests.test_streamlit_surface_enumeration import page_files

    pages = page_files()
    out = {}
    carried: dict = {}
    # Page 1 first: its session state is what pages 2 and 3 read.
    ordered = sorted(pages, key=lambda p: (p != "pages/1_Pipeline_Analyzer.py", p))
    for rel in ordered:
        downstream = rel in ("pages/2_Win_Alignment_Scorer.py",
                             "pages/3_Pipeline_Optimizer.py")
        cold = _run(rel, carried if downstream else None)
        if rel not in _ACTIONS:
            out[rel] = {"cold": cold, "driven": cold}
            continue
        driven = _run(rel, carried if downstream else None)
        for label in _ACTIONS[rel]:
            _click(driven, label)
        if rel == "pages/1_Pipeline_Analyzer.py":
            carried = {k: driven.session_state[k] for k in _CARRIED
                       if k in driven.session_state}
        out[rel] = {"cold": cold, "driven": driven}
    return out


def page_text(relpath: str, state: str) -> str:
    """Every prose element one page rendered in one state, one per line."""
    return "\n".join(text for _kind, text in texts(rendered_pages()[relpath][state]))
