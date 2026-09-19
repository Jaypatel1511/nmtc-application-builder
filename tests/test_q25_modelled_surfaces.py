"""The docs site and the About page must say what the generated documents say
about WHICH Question 25 area types this package models, and HOW it knows.

THE DEFECT (1.7.0, R1 addendum 2)

``renderers/_question_25`` INTERPOLATES ``Q25_AREA_TYPES_MODELLED`` and
``Q25_DISTINCT_AREA_TYPES`` into the basis note and states each modelled
field's provenance individually. ``docs/reference/methodology.md`` and
``streamlit_app/pages/4_About_and_Methodology.py`` HAND-TYPED both the count
and the enumeration, and nothing compared the two. When 1.4.0 landed
``PipelineProject.is_non_metro`` the renderer moved from five to six and its
"It carries NOTHING for Non-Metropolitan Counties" sentence was corrected --
the module docstring records exactly that -- and the two public surfaces kept
saying "five of the fourteen", "nothing for Non-Metropolitan Counties" and
"tool-unverified ... High Migration Rural Counties" for three releases. R1
edited both lines (fourteen -> fifteen) and left the numerator, so at R1's
first commit the docs disagreed with the generated Word document on how many
routes this tool models. All three discrepancies UNDERSTATE the package, which
is the false-negative direction ``_question_25``'s header ranks worst.

WHAT THIS HOLDS. The About page now reads the two constants; the docs page
cannot (mkdocs interpolates nothing into prose), so it is hand-typed and this
gate holds it. Every surface -- the renderer's own note included, so that the
parser is proven against the authority rather than assumed -- must:

  1. state the ratio ``<modelled> of the <distinct>`` equal to the constants,
     in digits or in words;
  2. list Non-Metropolitan Counties among the MODELLED fields, as tool-verified,
     and NOT in the "nothing for" enumeration;
  3. state High Migration Rural Counties as tool-verified and not in the
     tool-unverified group;
  4. keep the "nothing for" enumeration to Targeted Populations, Homeownership
     Cost Burden and items 6-12 -- the renderer's own list.

FAILS CLOSED: a surface whose paragraph cannot be located, or whose ratio
cannot be parsed, fails rather than passing on an empty match.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STREAMLIT_APP = _REPO_ROOT / "streamlit_app"
for _p in (str(_REPO_ROOT), str(_STREAMLIT_APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nmtcapp.renderers._question_25 import (  # noqa: E402
    Q25_AREA_TYPES_MODELLED, Q25_DISTINCT_AREA_TYPES, q25_basis_note,
)

_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}

_RATIO = re.compile(
    r"per-project field for (\w+) of the (\w+) distinct area types", re.I
)
_PARAGRAPH_START = "per-project field for"
_PARAGRAPH_END = "holding those fields"


def _number(token: str) -> int:
    token = token.lower()
    if token.isdigit():
        return int(token)
    if token in _WORDS:
        return _WORDS[token]
    pytest.fail(f"cannot read {token!r} as a count")


def _normalise(text: str) -> str:
    """Markdown emphasis and line wrapping stripped; case folded."""
    text = text.replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", text).lower()


def _paragraph(surface: str, text: str) -> str:
    low = _normalise(text)
    start = low.find(_PARAGRAPH_START)
    assert start >= 0, f"{surface}: no 'per-project field for' paragraph found"
    end = low.find(_PARAGRAPH_END, start)
    assert end > start, (
        f"{surface}: the modelled-fields paragraph does not end at "
        f"'Holding those fields' -- the surface was restructured; re-read it"
    )
    return low[start:end]


def _split_modelled_and_not(paragraph: str):
    """(modelled part, 'nothing for' part) of the paragraph."""
    i = paragraph.find("nothing for")
    assert i > 0, "no 'nothing for' enumeration in the paragraph"
    return paragraph[:i], paragraph[i:]


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

def _docs_text() -> str:
    path = _REPO_ROOT / "docs" / "reference" / "methodology.md"
    if not path.exists():
        pytest.skip("no docs/ tree -- an unpacked sdist prunes it")
    return path.read_text(encoding="utf-8")


def _about_page_text() -> str:
    """The About page's markdown bodies as Streamlit renders them -- the
    f-string EVALUATED, so an interpolated count is checked as a value."""
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    page = _STREAMLIT_APP / "pages" / "4_About_and_Methodology.py"
    at = AppTest.from_file(str(page), default_timeout=300)
    at.run()
    assert not at.exception, f"About page raised: {at.exception}"
    bodies = [el.value for el in at.markdown if isinstance(el.value, str)]
    assert bodies, "the About page rendered no markdown -- AppTest drove nothing"
    return "\n\n".join(bodies)


SURFACES = {
    "renderer (the authority)": q25_basis_note,
    "docs/reference/methodology.md": _docs_text,
    "streamlit_app/pages/4_About_and_Methodology.py": _about_page_text,
}


@pytest.fixture(scope="module")
def paragraphs() -> dict:
    return {name: _paragraph(name, load()) for name, load in SURFACES.items()}


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def test_the_constants_are_the_ones_the_renderer_interpolates():
    """The authority really does carry both constants, in digits."""
    note = q25_basis_note()
    assert (f"{Q25_AREA_TYPES_MODELLED} of the {Q25_DISTINCT_AREA_TYPES} "
            "distinct area types") in note


@pytest.mark.parametrize("surface", list(SURFACES))
def test_the_ratio_matches_the_constants(surface, paragraphs):
    m = _RATIO.search(paragraphs[surface])
    assert m, f"{surface}: no '<n> of the <m> distinct area types' ratio found"
    got = (_number(m.group(1)), _number(m.group(2)))
    assert got == (Q25_AREA_TYPES_MODELLED, Q25_DISTINCT_AREA_TYPES), (
        f"{surface} says this package models {got[0]} of {got[1]} area types; "
        f"the renderer interpolates {Q25_AREA_TYPES_MODELLED} of "
        f"{Q25_DISTINCT_AREA_TYPES}. A hand-typed count has drifted -- this is "
        "the 1.4.0 -> 1.7.0 'five of the fourteen' defect again."
    )


@pytest.mark.parametrize("surface", list(SURFACES))
def test_non_metropolitan_counties_is_modelled_and_tool_verified(surface, paragraphs):
    modelled, not_carried = _split_modelled_and_not(paragraphs[surface])
    assert "non-metropolitan counties" not in not_carried, (
        f"{surface} lists Non-Metropolitan Counties among the fields this "
        "package does NOT carry. PipelineProject.is_non_metro has existed since "
        "1.4.0 and the renderer states it as TOOL-VERIFIED AND TRI-STATE."
    )
    i = modelled.find("non-metropolitan counties")
    assert i >= 0, f"{surface}: Non-Metropolitan Counties is not listed as a modelled field"
    assert "tool-verified" in modelled[i:i + 120], (
        f"{surface}: Non-Metropolitan Counties is listed but not stated as "
        "tool-verified within its own clause"
    )


@pytest.mark.parametrize("surface", list(SURFACES))
def test_high_migration_rural_is_tool_verified_not_unverified(surface, paragraphs):
    modelled, _ = _split_modelled_and_not(paragraphs[surface])
    i = modelled.find("high migration rural")
    assert i >= 0, f"{surface}: High Migration Rural Counties is not listed as a modelled field"
    clause = modelled[i:i + 120]
    assert "tool-verified" in clause and "unverified" not in clause, (
        f"{surface}: High Migration Rural Counties is not stated as "
        "CDE-declared and tool-verified in its own clause -- the renderer says "
        "enrichment overwrites the CDE's declaration whenever nmtc-mapper "
        f"returns a determination. Clause: {clause!r}"
    )
    # And it must not sit inside the tool-unverified group.
    for m in re.finditer(r"unverified", modelled):
        window = modelled[max(0, m.start() - 160):m.start()]
        assert "high migration rural" not in window.split("verified")[-1], (
            f"{surface}: High Migration Rural Counties is named inside the "
            "tool-unverified group"
        )


@pytest.mark.parametrize("surface", list(SURFACES))
def test_the_nothing_for_list_is_the_renderers(surface, paragraphs):
    _, not_carried = _split_modelled_and_not(paragraphs[surface])
    for required in ("targeted populations", "homeownership cost burden", "items 6-12"):
        assert required in not_carried, (
            f"{surface}: the 'nothing for' enumeration omits {required!r}"
        )
    for forbidden in ("non-metropolitan", "high migration rural", "severe distress",
                      "deep distress", "native areas"):
        assert forbidden not in not_carried, (
            f"{surface}: the 'nothing for' enumeration names {forbidden!r}, "
            "which this package models"
        )
