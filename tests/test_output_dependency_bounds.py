"""A dependency this package MEASURES ITS OWN OUTPUT WITH needs an upper bound.

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

THE FILED DOCUMENT NEVER MOVED. What drifted was THIS REPOSITORY'S
MEASUREMENT of a document that is byte-identical.

WHY THIS GATE COVERS THE MEASURER AND NOT THE RENDERERS (1.5.5 B7c)
==================================================================

An earlier pass of this round held FIVE names — the four renderers as well —
and capped them in ``[pdf]``, ``[word]``, ``[excel]``, ``[viz]``, ``[output]``
and ``[docs]``. THAT SCOPE WAS WITHDRAWN AND THE CAPS WERE REVERTED. The
distinction this file now draws, in one sentence:

  A RENDERER THAT DRIFTS IS CAUGHT BY THE RENDERED-OUTPUT BASELINE;
  A MEASURER THAT DRIFTS DISABLES IT.

reportlab moving a glyph turns ``test_rendered_output_baseline[pdf]`` red and
hands a human A DIFF OF THE DOCUMENT in the pull request. That is the system
working, and it needs no version cap to work. pypdf moving corrupts the
detector itself: it reported four changed lines in a PDF that was
byte-identical, and NOTHING IN THE SUITE COULD SEE THAT, because the gate was
the thing that moved. Only one of those two needs a bound to stay safe.

The second reason is BLAST RADIUS, and it is the one that decided it. pypdf is
declared in ``[dev]`` and nowhere else, so bounding it reaches NO USER and can
conflict with nothing a CDE installs. A cap inside a shipped extra is a
different object: it can produce a RESOLUTION CONFLICT for a user who already
holds that renderer's next major, or for a downstream package requiring it.
That is a USER-FACING decision, and it is deferred WHOLE — the four renderers
join ``streamlit`` and ``mkdocs``, six dependencies in one round, rather than
being half-answered inside a patch whose job was unblocking a red ``main``.

  ⚠️  THE ASYMMETRY ABOVE IS NOT UNIVERSAL, AND THE EXCEPTION IS REAL  ⚠️

  It holds where the renderer and the measurer are DIFFERENT LIBRARIES. For
  the PDF they are: reportlab writes it, pypdf reads it back. FOR WORD AND
  EXCEL THEY ARE THE SAME LIBRARY. ``test_rendered_output_baseline._extract``
  reads the ``.docx`` back through ``python-docx`` and the ``.xlsx`` back
  through ``openpyxl`` — the very libraries that wrote them. There the two
  roles collapse, and a drift that changes BOTH the write and the read can
  cancel out and leave the baseline GREEN over a document that moved.

  THAT GAP IS NOT CLOSED BY A VERSION CAP and it is not closed here. A cap
  narrows the window; it does not give those two formats an independent
  reader, which is the actual remedy. Recorded for the six-dependency round,
  and named here so a green from this file is not read as covering it.

  ⚠️  SCOPE LIMIT -- READ THIS BEFORE TRUSTING A GREEN FROM THIS FILE  ⚠️

  THIS GATE IS NOT A DEPENDENCY-HEALTH CHECK AND DOES NOT COVER
  ``pyproject.toml`` GENERALLY. It reads ONE named requirement and ignores
  every other line in the file. A gate over all dependencies would be noise,
  and noise is how a gate earns a blanket waiver inside a release.

  IT THEREFORE OBSERVES:
    * whether each name in ``MEASUREMENT_DEPENDENCIES`` carries a
      ``<``-bounded specifier, wherever in ``pyproject.toml`` it is declared;
    * that each is actually declared, so deleting a line cannot be how this
      gate goes quiet;
    * that each stays DEV-ONLY. This is the assertion that keeps the
      narrowing honest: the bound above is defensible BECAUSE it reaches no
      user, so a name that acquires a second declaration in a shipped extra
      has silently converted a free dev pin into a user-facing cap, and that
      is the decision this round deferred rather than one to make by edit.

  IT DOES **NOT** OBSERVE:
    * whether the bound is the RIGHT one. ``<9999`` passes. The bound's value
      is a human judgement recorded in the comment beside it; this gate
      asserts only that a human made one;
    * whether an in-scope release WITHIN the bound changes the output --
      that is ``tests/test_rendered_output_baseline.py``, which is the gate
      that actually caught B7. This one narrows the window that gate has to
      watch; it does not replace it;
    * THE FOUR RENDERERS -- ``reportlab``, ``python-docx``, ``openpyxl``,
      ``matplotlib``. Deliberately, and NOT because they are safe: their
      bound is a user-facing decision deferred to its own round, and this
      gate is not the place to make it. See above;
    * ``streamlit`` or ``mkdocs``, for the same reason and by the same
      ruling; nor ``plotly``, ``jupyter``, ``markdown``, ``pytest``,
      ``pytest-cov``;
    * the INSTALLED versions. It reads the declaration, not the environment.
      A developer who pip-installs past the bound by hand is not caught here;
    * ``streamlit_app/requirements.txt``, whose pinning question is a
      different one (see the ruling at the top of that file) and which does
      not carry the in-scope name.

WHAT IS IN SCOPE, AND WHY IT IS CURRENTLY ONE NAME
==================================================

The test is narrow and mechanical, and it is deliberately NOT "does this
library decide the bytes of a filed artifact" — that question is the
renderers', and it is answered by the baseline. It is:

  DOES A DRIFT IN THIS LIBRARY CORRUPT THIS PACKAGE'S ABILITY TO DETECT A
  CHANGE IN ITS OWN OUTPUT -- AND IS BOUNDING IT FREE, i.e. does it reach no
  user?

  pypdf   MEASURES the filed PDF for ``test_rendered_output_baseline`` and for
          ``test_render_frame_geometry``. Nothing under ``nmtcapp/`` imports
          it; it renders nothing anyone files. Declared in ``[dev]`` alone, so
          the bound is free. It is the one that fired.

THE OTHER MEASURERS IN ``tests/``, ENUMERATED SO THE LIST IS NOT MISTAKEN FOR
THE WHOLE SET. ``python-docx`` and ``openpyxl`` also read filed artifacts back
(``_extract`` above), and ``matplotlib`` reports the bounding boxes
``tests/test_readiness_chart_geometry.py`` measures. All three ARE measurement
surfaces. They are out of scope here on the SECOND half of the test -- each is
declared in shipped extras, so bounding it is not free -- and they are named
in the deferred round rather than dropped.

  DOES THIS GATE EARN ITS PLACE AT ONE NAME? Stated because the answer is not
  obviously yes, and this package has twice refused a gate that adjudicates a
  single line. It earns it on the dev-only assertion, which is not a
  restatement of the pin: it fails on a plausible future edit -- adding pypdf
  to ``[pdf]`` because it is "the PDF library" -- that no other gate in the
  suite would catch, and that would quietly recreate the user-facing cap this
  round removed. The bound assertion earns it on B7's own history: an
  unbounded top end is how the detector broke, and a later "tidy up the pins"
  pass would reopen it with CI green until a third party published.

  IF THE SIX-DEPENDENCY ROUND RULES THAT NO BOUND IS WARRANTED ANYWHERE,
  DELETE THIS FILE rather than leaving it asserting one line out of habit.
  That is the condition under which it stops earning its place, and it is
  written down so the judgement is somebody's rather than nobody's.
"""
from __future__ import annotations

import re

import pytest

from tests.test_output_extra_is_named import _pyproject_text

#: The measurement layer. See "WHAT IS IN SCOPE" above; each entry is
#: (name, why). The four renderers are NOT here, deliberately -- see the
#: scope limit. This tuple is expected to GROW at the six-dependency round,
#: or to take this file with it if that round rules bounds unwarranted.
MEASUREMENT_DEPENDENCIES = (
    ("pypdf", "measures the rendered PDF (1.5.5 B7 fired here)"),
)

#: The extra an in-scope name may be declared in, and the only one. A second
#: declaration anywhere else makes the bound user-facing.
DEV_EXTRA = "dev"

#: Named so the gate's message can point at the recorded decision rather than
#: at a bare name. NOT asserted on -- see the scope limit.
DEFERRED_TO_THEIR_OWN_ROUND = (
    "reportlab", "python-docx", "openpyxl", "matplotlib", "streamlit", "mkdocs",
)


def _requirement_blocks() -> dict:
    """``{block: {distribution: [requirement, ...]}}`` from pyproject.toml.

    ``block`` is ``"dependencies"`` for the core list and the extra's own name
    for everything under ``[project.optional-dependencies]``. Keyed by block
    rather than flattened BECAUSE THE DEV-ONLY ASSERTION NEEDS TO KNOW WHERE a
    requirement was declared, not merely that it was.

    NO TOML PARSER, for the reason ``test_output_extra_is_named._extras``
    records: ``tomllib`` is 3.11+ and ``tomli`` is not in the dev extra, so a
    parser-driven skip would make this file silent on 3.9 and 3.10 -- half the
    supported matrix, and the exact shape this repository refuses.
    """
    text = _pyproject_text()
    blocks: dict = {}
    for name, body in re.findall(r"^\s*(dependencies|\w[\w.-]*)\s*=\s*\[(.*?)^\]",
                                 text, re.M | re.S):
        found: dict = {}
        for requirement in re.findall(r'"([^"]+)"', body):
            dist = re.split(r"[<>=!~\[; ]", requirement, maxsplit=1)[0].strip()
            found.setdefault(dist.lower(), []).append(requirement)
        if found:
            blocks.setdefault(name, {}).update(found)
    assert blocks, (
        "no dependency blocks parsed out of pyproject.toml. Fix the reader, "
        "not the check -- a reader that finds nothing makes this gate vacuous."
    )
    return blocks


def _declarations(name: str) -> dict:
    """``{block: [requirement, ...]}`` for one distribution."""
    return {
        block: reqs[name.lower()]
        for block, reqs in _requirement_blocks().items()
        if name.lower() in reqs
    }


@pytest.mark.parametrize(
    "name,why", MEASUREMENT_DEPENDENCIES,
    ids=[n for n, _w in MEASUREMENT_DEPENDENCIES],
)
def test_a_dependency_this_package_measures_its_output_with_carries_an_upper_bound(
    name, why
):
    """An open top end lets a third party disable the detector, uncommitted."""
    declared = _declarations(name)
    assert declared, (
        f"pyproject.toml declares no requirement for {name!r}, which this gate "
        f"holds in scope because it {why}. Either it moved and this list is "
        "stale, or it was dropped -- fix the list deliberately. A missing "
        "name must not be how this gate goes quiet."
    )
    unbounded = sorted(
        r for reqs in declared.values() for r in reqs if "<" not in r
    )
    assert not unbounded, (
        f"{name} is declared {unbounded} with NO UPPER BOUND, and it {why}.\n\n"
        "This package MEASURES ITS OWN FILED OUTPUT with this library. An "
        "unbounded requirement means a release published by a third party "
        "changes WHAT THE GATES READ off a document that did not move, with "
        "no commit here and no review by anyone -- and unlike a renderer "
        "drifting, NOTHING CATCHES IT, because the thing that moved is the "
        "detector.\n\n"
        "THIS HAS ALREADY HAPPENED. pypdf 6.16.2 landed on 2026-08-23 and "
        "turned main red on all four interpreters against a tree that had "
        "been green eleven hours earlier; the entire diff was two leading "
        "spaces in text extracted from a BYTE-IDENTICAL PDF (1.5.5 B7).\n\n"
        "Add an upper bound and RECORD BESIDE IT what you measured to choose "
        f"it. This gate does not check the bound's value -- {name}<9999 would "
        "pass it -- so the comment is the whole of the argument.\n\n"
        f"If the right answer is that {name} should NOT be bounded, that is a "
        "legitimate ruling: take it out of MEASUREMENT_DEPENDENCIES in this "
        "file and say why, the way the four renderers are recorded as "
        "deferred in this module's docstring."
    )


@pytest.mark.parametrize(
    "name,why", MEASUREMENT_DEPENDENCIES,
    ids=[n for n, _w in MEASUREMENT_DEPENDENCIES],
)
def test_a_bounded_measurement_dependency_stays_dev_only(name, why):
    """The bound above is defensible BECAUSE it reaches no user (1.5.5 B7c).

    THIS IS THE ASSERTION THAT KEEPS THE NARROWING HONEST. 1.5.5 removed upper
    bounds from ``reportlab``, ``python-docx``, ``openpyxl`` and ``matplotlib``
    precisely because a cap inside ``[pdf]``/``[word]``/``[excel]``/``[viz]``/
    ``[output]``/``[docs]`` reaches users and can produce a resolution
    conflict. ``pypdf`` keeps its cap on the ground that it is test tooling.

    So the ground has to stay true. Adding ``pypdf`` to ``[pdf]`` -- an easy,
    plausible edit, since it IS a PDF library -- would silently recreate the
    user-facing cap this round deliberately removed, and no other gate in the
    suite would notice.
    """
    declared = _declarations(name)
    assert declared, f"pyproject.toml declares no requirement for {name!r}"
    shipped = sorted(block for block in declared if block != DEV_EXTRA)
    assert not shipped, (
        f"{name} is now declared in {shipped} as well as {DEV_EXTRA!r}, and it "
        f"carries an UPPER BOUND because it {why}.\n\n"
        f"That bound was accepted on the explicit ground that {name} is "
        f"declared in [{DEV_EXTRA}] AND NOWHERE ELSE, so it reaches no user "
        "and can conflict with nothing a CDE installs. A declaration in a "
        "SHIPPED extra breaks that ground: the cap becomes user-facing, and a "
        "user who already holds a newer release -- or a downstream package "
        "requiring one -- now gets a RESOLUTION CONFLICT from this package.\n\n"
        "1.5.5 removed exactly such caps from "
        f"{', '.join(DEFERRED_TO_THEIR_OWN_ROUND[:4])} rather than keep them, "
        "and deferred the question of what upper bound is safe for a "
        "user-facing dependency to its own round.\n\n"
        "So this is not an edit to make in passing. EITHER drop the new "
        f"declaration, OR take {name} out of MEASUREMENT_DEPENDENCIES and drop "
        "its bound with it, and record which and why."
    )
