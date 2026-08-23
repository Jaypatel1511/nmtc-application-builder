"""THE TOOL MUST NOT NAME A ROUND THE CDFI FUND HAS NEVER RUN (1.5.5 T1).

WHAT SHIPPED THROUGH 1.5.4

``Application.__init__`` carried ``application_round: str = "CY2025"`` as a
DEFAULT, and ``WinProbabilityModel.score`` carried the same literal. Every
surface that names a round read it: four renderers, the Streamlit home page
and Pipeline Analyzer, ``ApplicationAnalysis.summary()`` and Section A's
deployment-strategy narrative. A CDE who never touched the field got
documents asserting "Application Round: CY2025" and "New Markets Tax Credit
allocation for CY2025".

**THERE IS NO CY2025 ROUND.** The instrument this package encodes is the
**CY 2024-2025** Allocation Application -- opened 19 Nov 2024, closed
29 Jan 2025, awarded 23 Dec 2025 at $10 billion. The upcoming round is
**CY 2026**, announced 12 Aug 2026 at $5 billion and not yet open. "CY2025"
is neither, and ``data/historical_awards.NMTC_AWARD_ROUNDS`` -- this
package's own list of rounds that happened -- does not contain it. The tool
was printing a round name onto a federal application document that no
CDFI Fund publication has ever used.

THE TWO CONCEPTS THAT WERE CONFLATED

  1. THE ROUND THE APPLICANT IS TARGETING. Read off the code rather than
     assumed: ``sections/section_a_business`` renders "targets a {round}
     award", the renderers render "allocation for {round}", and
     ``core/upload_handler`` maps a user-supplied "Application Round" column
     onto it. It is unambiguously the round the CDE is filing INTO, which is
     **the user's fact about their own submission**. A library cannot know
     it, so it must not default to one.

  2. THE ROUND THE TOOL ENCODES. Already handled, correctly and separately,
     by ``renderers/_round_provenance`` on four renderers and three
     Streamlit pages. Nothing here touches it.

THE RULING, AND WHAT A DOCUMENT GENERATED WITHOUT THE FIELD NOW SAYS

The default becomes ``None`` and every surface DISCLOSES the absence instead
of inventing a round:

  * labelled fields ("Application Round:") render
    ``ROUND_UNSPECIFIED_VALUE`` -- which names who owns the fact rather than
    leaving a blank a reader would take for a formatting bug;
  * bare metadata strips render ``ROUND_UNSPECIFIED_STANDALONE``;
  * narrative sentences DROP the clause: "requests $65.0 million in New
    Markets Tax Credit allocation. Our 20-project pipeline spans ..." -- a
    true sentence with nothing missing;
  * running headers and footers drop the round token: "NMTC Application |
    CONFIDENTIAL".

WHY NOT THE OTHER TWO OPTIONS

  * REQUIRE IT (raise when omitted). ``Application(cde, allocation)`` is the
    two-argument form used in this package's own class docstring, in
    ``docs/reference/api.md``, in the README and in dozens of tests.
    Requiring the round is a BREAKING API CHANGE and belongs with the 2.0.0
    removals, not in a patch.
  * DEFAULT TO "CY 2026". This is the round a CDE using the tool today is in
    fact preparing for -- and that is exactly why the tool may not assert it.
    It would replace a false claim with an UNVERIFIED one about the user's
    own submission, and a CDE preparing a CY 2027 filing, or modelling a
    closed round retrospectively, would get a document naming the wrong
    round with no indication the tool had guessed. 1.5.2's precedent is that
    REMOVING a false claim ships as a patch; ADDING an assertion does not.

WHY THIS CANNOT MOVE A SCORE

``WinProbabilityModel.score`` accepts ``application_round`` and never reads
it -- its own docstring says "(informational)", and the parameter appears
nowhere in the method body. The claim in ``docs/reference/api.md`` that the
field feeds an "acceptance rate lookup" is FALSE and is corrected in this
release: ``get_overall_acceptance_rate(rounds=4)`` takes a COUNT of recent
rounds, not a round label. Verified empirically as well --
``tests/test_score_consistency.py`` and the A/B in this round's CHANGELOG
show every sub-score, both aggregates, the tier, the readiness composite and
all six of its components identical with the round set and unset.
"""
from __future__ import annotations

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.application_round import (
    ROUND_UNSPECIFIED_STANDALONE,
    ROUND_UNSPECIFIED_VALUE,
    allocation_round_clause,
    is_round_specified,
    nmtc_round_phrase,
    round_label,
    round_label_standalone,
)
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.data.historical_awards import NMTC_AWARD_ROUNDS
from nmtcapp.intelligence.win_probability import WinProbabilityModel


#: Rounds the CDFI Fund has actually run or announced. "CY2025" is not among
#: them and never was.
def test_cy2025_is_not_a_round_this_package_knows_about():
    """The premise. If this ever fails, the defect statement above is wrong."""
    assert "CY2025" not in NMTC_AWARD_ROUNDS
    assert "CY2024-2025" in NMTC_AWARD_ROUNDS


def test_application_does_not_default_to_any_round():
    """No default may invent the user's fact — least of all a nonexistent round."""
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    assert app.application_round is None, (
        f"Application defaulted application_round to {app.application_round!r}. "
        "The round a CDE files into is the CDE's fact; the tool may not supply one."
    )


def test_win_probability_does_not_default_to_any_round():
    import inspect
    sig = inspect.signature(WinProbabilityModel.score)
    default = sig.parameters["application_round"].default
    assert default is None, (
        f"WinProbabilityModel.score defaults application_round to {default!r}"
    )


def test_no_live_cy2025_round_literal_in_package_or_app():
    """The literal is gone from LIVE code, not just from one default.

    Deliberately AST-based rather than grep-based. Comments and docstrings
    that RECORD the defect are the point of this release and must survive —
    ``core/application_round``'s header explains it at length. What may not
    survive is a string the program can actually emit.
    """
    import ast
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    offenders = []
    for path in sorted(list((root / "nmtcapp").rglob("*.py"))
                       + list((root / "streamlit_app").rglob("*.py"))):
        if "__pycache__" in str(path):
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                body = getattr(node, "body", None)
                if body and isinstance(body[0], ast.Expr) and \
                        isinstance(body[0].value, ast.Constant) and \
                        isinstance(body[0].value.value, str):
                    docstrings.add(id(body[0].value))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in docstrings or "CY2025" not in node.value:
                continue
            offenders.append(f"{path.relative_to(root)}:{node.lineno}: {node.value[:90]!r}")
    assert not offenders, (
        "live 'CY2025' round literal — the CDFI Fund has never run a round by "
        "that name:\n" + "\n".join(offenders)
    )


class TestHelpers:
    def test_specified_round_passes_through_every_shape(self):
        assert is_round_specified("CY 2026")
        assert round_label("CY 2026") == "CY 2026"
        assert round_label_standalone("CY 2026") == "CY 2026"
        assert allocation_round_clause("CY 2026") == " for CY 2026"
        assert nmtc_round_phrase("CY 2026") == "NMTC CY 2026"

    @pytest.mark.parametrize("blank", [None, "", "   ", "\t"])
    def test_absent_round_discloses_and_never_names_one(self, blank):
        assert not is_round_specified(blank)
        assert round_label(blank) == ROUND_UNSPECIFIED_VALUE
        assert round_label_standalone(blank) == ROUND_UNSPECIFIED_STANDALONE
        assert allocation_round_clause(blank) == "", (
            "the narrative clause must DISAPPEAR, not render an empty round"
        )
        assert nmtc_round_phrase(blank) == "NMTC"

    def test_disclosure_strings_name_no_round(self):
        for text in (ROUND_UNSPECIFIED_VALUE, ROUND_UNSPECIFIED_STANDALONE):
            assert "CY" not in text, f"{text!r} names a round"
            assert "not specified" in text.lower()

    def test_surrounding_whitespace_is_not_a_round(self):
        assert round_label("  CY 2026  ") == "CY 2026"


class TestRenderedSurfaces:
    """A document generated WITHOUT the field must not name a round anywhere."""

    @staticmethod
    @pytest.fixture(scope="class")
    def unset_app():
        app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
        app.add_pipeline(Pipeline.sample(n=8))
        return app

    def test_markdown_document_names_no_round(self, unset_app):
        from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
        text = MarkdownApplicationBuilder(unset_app, unset_app.analyze()).build()
        assert "CY2025" not in text
        assert ROUND_UNSPECIFIED_VALUE in text, (
            "a document generated without the round must SAY so, not leave a blank"
        )
        assert "allocation for application round ." not in text
        assert "allocation for application round  ." not in text

    def test_analysis_summary_names_no_round(self, unset_app, capsys):
        unset_app.analyze().summary()
        out = capsys.readouterr().out
        assert "CY2025" not in out
        assert ROUND_UNSPECIFIED_VALUE in out

    def test_specified_round_still_renders_verbatim(self):
        from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
        app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000,
                          application_round="CY 2026")
        app.add_pipeline(Pipeline.sample(n=8))
        text = MarkdownApplicationBuilder(app, app.analyze()).build()
        assert "Application Round: CY 2026" in text
        assert "allocation for application round CY 2026." in text
        assert ROUND_UNSPECIFIED_VALUE not in text
