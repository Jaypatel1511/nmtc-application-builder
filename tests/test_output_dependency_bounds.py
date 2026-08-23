"""A dependency that decides the bytes of a filed document needs an UPPER bound.

THE DEFECT THIS GATE EXISTS FOR (1.5.5 B7)
==========================================

``main`` went red on all four interpreters with NOT ONE COMMIT BETWEEN THE
GREEN RUN AND THE RED ONE. The same tree had been green on the pull request
eleven hours earlier. One failure, identical everywhere::

    tests/test_rendered_output_baseline.py::
        test_the_rendered_output_matches_the_reviewed_baseline[pdf]
    AssertionError: 4 rendered line(s) changed in the pdf output

and the whole diff was TWO LEADING SPACES. No number, word or sentence moved::

    -Metric                                    - **Award 1 (FY2019):** ...
    + Metric                                   +  **Award 1 (FY2019):** ...

WHAT CHANGED WAS NOT THIS REPOSITORY. ``pypdf`` published 6.16.2 on
2026-08-23, inside that eleven-hour window, and ``pyproject.toml`` asked for
``pypdf>=4.0`` — so CI resolved a library that had not existed when the pull
request passed. 6.16.2 rewrote the space/newline heuristic in
``_text_extraction/__init__.py`` to take its scale factors from the combined
text x CTM matrix rather than the text matrix alone, and a gap that used to
fall below the space threshold now clears it.

``reportlab`` was tested FIRST and REFUTED: the failure reproduces on
reportlab 4.5.1 and on 5.0.1 alike, and disappears on either the moment pypdf
goes back one patch release. The bisect is recorded in ``pyproject.toml``
beside the pin — 6.16.1 GREEN, 6.16.2 RED, alternated twice.

THE FILED DOCUMENT NEVER MOVED. ``pypdf`` is in the ``dev`` extra and nowhere
else: not ``pdf``, not ``output``, not ``docs``, not
``streamlit_app/requirements.txt``. No CDE installs it. What drifted was THIS
REPOSITORY'S MEASUREMENT of a document that is byte-identical.

WHY A GATE AND NOT JUST A PIN
=============================

Because this is the THIRD member of the class to be recorded and the FIRST to
fire. ``streamlit>=1.28.0`` and ``mkdocs>=1.5`` are both open at the top end
against known-breaking majors. A pin fixes today's instance; nothing stops the
next one, and the failure arrives looking like a defect in this package rather
than a release somewhere else.

An unbounded dependency means A THIRD PARTY CAN CHANGE WHAT THIS PACKAGE
PRINTS, OR WHAT ITS GATES READ, WITHOUT A COMMIT AND WITHOUT A REVIEW. For a
tool whose output goes into a federal filing, that is the property to refuse.

  ⚠️  SCOPE LIMIT -- READ THIS BEFORE TRUSTING A GREEN FROM THIS FILE  ⚠️

  THIS GATE IS NOT A DEPENDENCY-HEALTH CHECK AND DOES NOT COVER
  ``pyproject.toml`` GENERALLY. It reads FIVE named requirements and ignores
  every other line in the file. A gate over all dependencies would be noise,
  and noise is how a gate earns a blanket waiver inside a release.

  IT THEREFORE OBSERVES:
    * whether each of the five requirements in ``MEASURED_DEPENDENCIES``
      carries a ``<``-bounded specifier, wherever in ``pyproject.toml`` it is
      declared -- core ``dependencies`` or any extra;
    * that the five are all actually declared somewhere, so deleting a line
      cannot be how this gate goes quiet.

  IT DOES **NOT** OBSERVE:
    * whether the bound is the RIGHT one. ``<9999`` passes. The bound's value
      is a human judgement recorded in the comment beside it; this gate
      asserts only that a human made one;
    * whether an in-scope release WITHIN the bound changes the output --
      that is ``tests/test_rendered_output_baseline.py``, which is the gate
      that actually caught B7. This one narrows the window that gate has to
      watch; it does not replace it;
    * ``streamlit``, ``mkdocs``, ``plotly``, ``jupyter``, ``markdown``,
      ``pytest`` or ``pytest-cov``. Deliberately -- see WHAT IS OUT OF SCOPE;
    * the INSTALLED versions. It reads the declaration, not the environment.
      A developer who pip-installs past the bound by hand is not caught here;
    * ``streamlit_app/requirements.txt``, whose pinning question is a
      different one (see the ruling at the top of that file) and which
      carries none of the five in-scope names.

WHAT IS IN SCOPE, AND WHY THESE FIVE
====================================

The test is narrow and mechanical: DOES THIS LIBRARY DECIDE THE BYTES OF AN
ARTIFACT A CDE FILES, OR THE BYTES THIS REPOSITORY MEASURES ONE BY? Five
libraries answer yes.

  reportlab     RENDERS the PDF. It decides where a glyph lands on the page.
  python-docx   RENDERS the Word document.
  openpyxl      RENDERS the Excel workbook -- and MEASURES it, since the
                rendered baseline's excel projection reads cell values AND
                number formats back through it. Both sides at once.
  matplotlib    RENDERS the readiness chart, and
                tests/test_readiness_chart_geometry.py MEASURES bounding
                boxes matplotlib itself reports. A layout change there moves
                a measured number with no commit.
  pypdf         MEASURES the PDF only -- nothing under nmtcapp/ imports it.
                It renders nothing anyone files, and it is the one that fired.

The list is the renderers plus the tools that read their artifacts back. It is
short on purpose and it is not a proxy for importance.

WHAT IS OUT OF SCOPE, RECORDED RATHER THAN OVERLOOKED
=====================================================

  streamlit >=1.28.0   REAL, OPEN, AND ALREADY WRONG AT THE OTHER END -- that
                       floor sits below ``st.pyplot(..., width="stretch")``,
                       which the app calls. It needs its own decision about
                       what upper bound is safe for a public app that
                       redeploys on merge, and that decision is not this
                       round's. NOT PINNED HERE. Recorded.
  mkdocs >=1.5         REAL AND OPEN against an announced-breaking 2.0 with no
                       migration path published. Same answer: its own round.
                       NOT PINNED HERE. Recorded.
  plotly               Renders the Optimizer and Win Alignment charts, but
                       CLIENT-SIDE in the Streamlit app. Nothing under
                       nmtcapp/ imports it, no filed document contains it, and
                       no gate measures it -- test_readiness_chart_geometry's
                       own scope note says nothing in CI can see those charts.
                       Neither output nor measurement. Out.
  pandas numpy pyyaml  They carry VALUES into the document; they do not decide
                       its bytes. Every number they produce is formatted by
                       this package's own code, and the gates that watch those
                       numbers (invariance, pinned constants) are value gates,
                       not byte gates. This is the list's one genuine judgement
                       call rather than a mechanical exclusion, and it is the
                       first place to look if a fourth instance of this class
                       ever arrives from somewhere unexpected.
  jupyter markdown     Test and docs tooling. They touch neither artifact.
  pytest pytest-cov    The runner. A bound here would pin the thing that
                       reports the failure, which is the wrong end.
"""
from __future__ import annotations

import re

import pytest

from tests.test_output_extra_is_named import _pyproject_text

#: The five. See "WHAT IS IN SCOPE" above; each entry is (name, why).
MEASURED_DEPENDENCIES = (
    ("reportlab", "renders the PDF a CDE files"),
    ("python-docx", "renders the Word document a CDE files"),
    ("openpyxl", "renders the Excel workbook, and measures it back"),
    ("matplotlib", "renders the readiness chart, whose geometry is measured"),
    ("pypdf", "measures the rendered PDF (1.5.5 B7 fired here)"),
)

#: Named here so the gate's own message can point at the recorded decision
#: rather than at a bare name. NOT asserted on -- see the scope limit.
DELIBERATELY_UNBOUNDED = ("streamlit", "mkdocs")


def _requirements() -> dict:
    """``{distribution: [full requirement string, ...]}`` from pyproject.toml.

    Reads core ``dependencies`` AND every extra, so moving an in-scope library
    from one to the other cannot be how it escapes the gate.

    NO TOML PARSER, for the reason ``test_output_extra_is_named._extras``
    records: ``tomllib`` is 3.11+ and ``tomli`` is not in the dev extra, so a
    parser-driven skip would make this file silent on 3.9 and 3.10 -- half the
    supported matrix, and the exact shape this repository refuses.
    """
    text = _pyproject_text()
    found: dict = {}
    # Every double-quoted string inside a dependencies = [...] or an extra's
    # [...] block. Requirement strings are the only quoted values in either.
    blocks = re.findall(r"^\s*(?:dependencies|\w[\w.-]*)\s*=\s*\[(.*?)^\]",
                        text, re.M | re.S)
    assert blocks, (
        "no dependency blocks parsed out of pyproject.toml. Fix the reader, "
        "not the check -- a reader that finds nothing makes this gate vacuous."
    )
    for block in blocks:
        for requirement in re.findall(r'"([^"]+)"', block):
            name = re.split(r"[<>=!~\[; ]", requirement, maxsplit=1)[0].strip()
            found.setdefault(name.lower(), []).append(requirement)
    return found


@pytest.mark.parametrize(
    "name,why", MEASURED_DEPENDENCIES, ids=[n for n, _w in MEASURED_DEPENDENCIES]
)
def test_a_dependency_that_decides_filed_bytes_carries_an_upper_bound(name, why):
    """An open top end lets a third party rewrite the filing, uncommitted."""
    requirements = _requirements()
    declared = requirements.get(name.lower())
    assert declared, (
        f"pyproject.toml declares no requirement for {name!r}, which this gate "
        f"holds in scope because it {why}. Either it moved and this list is "
        "stale, or it was dropped -- fix the list deliberately. A missing "
        "name must not be how this gate goes quiet."
    )
    unbounded = [r for r in declared if "<" not in r]
    assert not unbounded, (
        f"{name} is declared {unbounded} with NO UPPER BOUND, and it {why}.\n\n"
        "An unbounded requirement means a release published by a third party "
        "changes what this package prints -- or what its gates read off what "
        "it prints -- with no commit here and no review by anyone.\n\n"
        "THIS HAS ALREADY HAPPENED. pypdf 6.16.2 landed on 2026-08-23 and "
        "turned main red on all four interpreters against a tree that had "
        "been green eleven hours earlier; the entire diff was two leading "
        "spaces in text extracted from a BYTE-IDENTICAL PDF (1.5.5 B7).\n\n"
        "Add an upper bound and RECORD BESIDE IT what you measured to choose "
        f"it. This gate does not check the bound's value -- {name}<9999 would "
        "pass it -- so the comment is the whole of the argument.\n\n"
        f"If the right answer is that {name} should NOT be bounded, that is a "
        "legitimate ruling: take it out of MEASURED_DEPENDENCIES in this file "
        f"and say why, the way {' and '.join(DELIBERATELY_UNBOUNDED)} are "
        "recorded as out of scope in this module's docstring."
    )
