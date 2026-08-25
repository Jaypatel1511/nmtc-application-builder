"""T2 (1.6.0): where the readiness claim and its disclosure live, GATED RENDERED.

THE RULING, AND IT REJECTS THE ROUND'S LEADING OPTION.

    A CLAIM AND ITS DISCLOSURE TRAVEL TOGETHER. Wherever the readiness grade
    is asserted, a proportionate disclosure is asserted beside it.

The leading option was to remove the readiness grade and composite from the
generated documents entirely, on the argument that the composite has no CDFI
Fund referent and that a document's reader is a Fund reviewer who has no use
for it. THAT ARGUMENT RESTS ON A PREMISE THAT MEASUREMENT DOES NOT SUPPORT.

MEASURED, NOT ARGUED. Only ``markdown_builder`` renders
``narrative_withdrawal_note()``. ``word_builder``, ``pdf_builder`` and
``excel_builder`` render the grade and ``readiness_weights_note()`` (or its
spreadsheet variant) and nothing else -- verified by grep across all four and
by the rendered projections this file builds. So:

  * the four "same" documents ALREADY DISAGREE, and have since 1.5.2 -- one
    carries ~700 words of disclosure the other three do not. That is a defect
    on its own terms, whichever way placement is ruled; and
  * THREE OF THE FOUR ARE ALREADY AT THE FALLBACK: grade plus one paragraph.

THE 700 WORDS ARE NOT THE GRADE'S DISCLOSURE. The grade's disclosure is
``readiness_weights_note()`` -- the weights, the HOUSE attribution, and the
not-a-Fund-evaluation sentence -- and it is one paragraph.
``narrative_withdrawal_note()`` discloses a DIFFERENT claim: "this tool
declines to advise you, and here is what it nevertheless deducted." That claim
answers a question a CDE asks while deciding what to change. A Fund reviewer
never asks it. Applying the principle EXACTLY, rather than approximately, puts
each disclosure where its own claim is -- which is the fallback, not removal.

AND REMOVAL WOULD DELETE A CLAIM TO AVOID DISCLOSING IT. The fallback hides
nothing: the grade stays, its disclosure stays beside it on all four surfaces,
and what leaves is an account of a decision the document does not make. The
docking table is not lost -- ``1_Pipeline_Analyzer.py`` already renders it in
full through ``wrap_note``, beside the grade and the six-component chart, on
the surface where a CDE decides whether to trust the number. ``nmtcapp
analyze`` prints it too. Nothing moves; one surface stops repeating it.

WITHDRAWN, NOT SILENTLY EMPTIED -- this package's own precedent, twice (1.5.1,
1.5.2): "an absent recommendation and a withdrawn one read differently to a
CDE who ran the tool last week". So the markdown block is replaced by a
POINTER, read from one place like the note it replaces, and not deleted.

WHAT LEAVES UNCONDITIONALLY, AND IT IS ROUGHLY HALF THE BLOCK: internal
version numbers, the recital of what earlier releases withdrew and why, and
``Application.recommendations()``. Those are changelog and developer
documentation. They disclose nothing the document asserts, and a Python API
call has no business in a federal filing draft.

OUT OF SCOPE AND UNTOUCHED: what the composite COMPUTES. No weight, band,
threshold or ``overall_score`` moves in this round.
"""
from __future__ import annotations

import re

import pytest

from tests.test_rendered_output_baseline import FORMATS, _render_projections


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict:
    return _render_projections(str(tmp_path_factory.mktemp("placement")))


def _weights_note() -> str:
    from nmtcapp.renderers._methodology import readiness_weights_note
    return readiness_weights_note()


def _norm(text: str) -> str:
    """Collapse whitespace: PDF and Word reflow, the words do not change."""
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# The claim, and its disclosure beside it, on every rendered surface
# ---------------------------------------------------------------------------

class TestTheClaimKeepsItsDisclosure:
    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_grade_is_still_asserted(self, rendered, fmt):
        assert re.search(r"Grade\s+[A-F]\b", _norm(rendered[fmt])), (
            f"{fmt} no longer asserts a readiness grade. This round rules "
            "PLACEMENT, not removal; if the grade is withdrawn that is a "
            "different ruling and this gate should be rewritten, not deleted."
        )

    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_disclosure_travels_with_it(self, rendered, fmt):
        text = _norm(rendered[fmt])
        assert "UNSOURCED HOUSE HEURISTIC" in text.upper(), (
            f"{fmt} asserts a readiness grade with no statement of whose "
            "weighting it is. The claim and its disclosure travel together."
        )

    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_disclosure_says_the_fund_publishes_no_such_thing(
        self, rendered, fmt
    ):
        text = _norm(rendered[fmt]).lower()
        assert "publishes no such weighting" in text or (
            "not a cdfi fund evaluation" in text
        ), (
            f"{fmt} carries the weighting without the sentence that denies a "
            "federal referent."
        )


# ---------------------------------------------------------------------------
# What is NEITHER claim NOR disclosure, and leaves every surface
# ---------------------------------------------------------------------------

#: Version strings of THIS package. A CDE's filing draft is not a changelog.
_INTERNAL_VERSION = re.compile(r"\b1\.[0-9]+\.[0-9]+\b")

#: Python the reader is told to call.
_PYTHON_POINTERS = (
    "Application.recommendations()",
    "intelligence.RecommendationEngine",
)


class TestChangelogAndDeveloperContentLeavesTheDocument:
    @pytest.mark.parametrize("fmt", FORMATS)
    def test_no_internal_version_number_is_rendered(self, rendered, fmt):
        text = rendered[fmt]
        # The Methodology Note's "Generated by nmtc-application-builder vX.Y.Z"
        # is a PROVENANCE stamp -- it names the artifact's own builder and a
        # reader needs it to reproduce the run. Every OTHER version string is a
        # pointer into this package's release history.
        stamped = re.sub(r"nmtc-application-builder\*{0,2}\s*v?\s*"
                         r"\*{0,2}[0-9.]+", "", text)
        stamped = re.sub(r"(?i)version[:\s|]+[0-9.]+", "", stamped)
        found = sorted(set(_INTERNAL_VERSION.findall(stamped)))
        assert not found, (
            f"{fmt} renders internal release numbers {found} into a federal "
            "filing draft. What 1.5.1 and 1.5.2 withdrew and why is changelog "
            "content: it discloses nothing this document asserts."
        )

    @pytest.mark.parametrize("fmt", FORMATS)
    @pytest.mark.parametrize("pointer", _PYTHON_POINTERS)
    def test_no_python_api_pointer_is_rendered(self, rendered, fmt, pointer):
        assert pointer not in _norm(rendered[fmt]), (
            f"{fmt} tells the reader of a federal filing draft to call "
            f"{pointer!r}. A Python API pointer is developer documentation."
        )

    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_docking_table_is_not_repeated_here(self, rendered, fmt):
        text = _norm(rendered[fmt])
        for phrase in ("TOTAL DEDUCTION",
                       "ROWS THAT ARE HOUSE BOOKKEEPING END TO END",
                       "YOU WERE NEVERTHELESS DOCKED"):
            assert phrase not in text, (
                f"{fmt} repeats the deduction arithmetic. It is not removed "
                "from the tool -- the Pipeline Analyzer page and `nmtcapp "
                "analyze` both print it in full, where a CDE reads it while "
                f"deciding. This surface points at it. Found: {phrase!r}"
            )


# ---------------------------------------------------------------------------
# Withdrawn, not silently emptied
# ---------------------------------------------------------------------------

class TestTheWithdrawalIsAnnouncedNotSilent:
    @pytest.mark.parametrize("fmt", FORMATS)
    def test_every_surface_says_the_narrative_is_withdrawn(self, rendered, fmt):
        from nmtcapp.renderers._methodology import readiness_narrative_pointer

        anchor = _norm(readiness_narrative_pointer())[:60]
        assert anchor in _norm(rendered[fmt]), (
            f"{fmt} carries a readiness grade and no statement that the "
            "readiness narrative is withdrawn. A CDE who ran 1.5.7 last week "
            "sees a shorter document and is told nothing -- which is the "
            "failure 1.5.1's own rule names."
        )

    def test_the_pointer_is_read_from_one_place_not_restated(self):
        """markdown_builder:198's property, extended to this note.

        Four near-identical copies of one disclosure is the shape that
        produced the 1.2.1 defect where a sentence was deleted from one file
        and stayed live in a second.
        """
        import inspect

        from nmtcapp.renderers import (
            excel_builder, markdown_builder, pdf_builder, word_builder,
        )

        for module in (markdown_builder, word_builder, pdf_builder, excel_builder):
            src = inspect.getsource(module)
            assert "readiness_narrative_pointer()" in src, (
                f"{module.__name__} does not call readiness_narrative_pointer(); "
                "either it stopped carrying the statement or it restated it."
            )

    def test_the_pointer_carries_no_version_number_or_python_call(self):
        from nmtcapp.renderers._methodology import readiness_narrative_pointer

        note = readiness_narrative_pointer()
        assert not _INTERNAL_VERSION.search(note)
        for pointer in _PYTHON_POINTERS:
            assert pointer not in note


# ---------------------------------------------------------------------------
# The four documents must AGREE
# ---------------------------------------------------------------------------

def test_all_four_surfaces_disclose_the_same_SUBSTANCE(rendered):
    """The defect this ruling also closes: they did not.

    Through 1.5.7 markdown carried ~700 words the other three did not, so the
    same tool produced four documents with materially different disclosure of
    the same number and nothing noticed.

    ASSERTED ON SUBSTANCE, NOT ON A SHARED STRING, and the difference is
    deliberate. ``readiness_weights_sheet_note()`` is the same disclosure
    sized for a spreadsheet cell -- it exists because a workbook cell is not a
    paragraph -- so demanding one byte-identical anchor would fail Excel for
    being correctly formatted. What must agree is every FACT: all six weights,
    that the weighting is this tool's own, that the Fund publishes none, and
    that the score predicts nothing.
    """
    from nmtcapp.data.schema import READINESS_SCORING_WEIGHTS

    weights = [f"{value:.0%}" for value in READINESS_SCORING_WEIGHTS.values()]
    gaps = {}
    for fmt in FORMATS:
        text = _norm(rendered[fmt]).lower()
        missing = [w for w in weights if w not in text]
        for phrase in ("this tool's own", "publishes no such weighting",
                       "does not predict an award outcome"):
            if phrase not in text:
                missing.append(phrase)
        if missing:
            gaps[fmt] = missing
    assert not gaps, (
        "the four documents disclose the same number differently:\n"
        + "\n".join(f"  {fmt}: missing {items}" for fmt, items in gaps.items())
    )
