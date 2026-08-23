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

import ast
import json
import pathlib

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


_ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The literal this release removed. One definition, read by both sweeps below,
#: so widening the second cannot leave the two asking different questions.
_DEAD_ROUND = "CY2025"


def _docstring_node_ids(tree: ast.AST) -> set:
    """ids of the string Constants that are docstrings, not live values."""
    ids = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and \
                isinstance(body[0].value, ast.Constant) and \
                isinstance(body[0].value.value, str):
            ids.add(id(body[0].value))
    return ids


def _live_round_literals_in_python(source: str, label, line_offset: int = 0):
    """Live (non-docstring) string constants naming the dead round.

    AST rather than grep, and the distinction is the whole point: a COMMENT or
    DOCSTRING recording the defect is what this release is made of and must
    survive — ``core/application_round``'s header explains it at length, and so
    does this module's. What may not survive is a string the program can emit.

    Example::

        _live_round_literals_in_python('x = "CY2025"', "cell 8")
    """
    tree = ast.parse(source, filename=str(label))
    docstrings = _docstring_node_ids(tree)
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if id(node) in docstrings or _DEAD_ROUND not in node.value:
            continue
        found.append(f"{label}:{node.lineno + line_offset}: {node.value[:90]!r}")
    return found


def _fenced_code_blocks(markdown: str):
    """(first_line_number, body) for every ``` fence in a Markdown file.

    Prose is deliberately NOT swept. Two docs pages explain the defect by
    naming the round — ``reference/api.md`` and ``reference/data-sources.md``
    both say what the field used to default to — and a sweep that reddened on
    those would be a gate that forbids documenting the bug it exists to
    prevent. What a reader COPIES is the fenced block.

    Example::

        list(_fenced_code_blocks("text\n```\ncode\n```\n"))
    """
    blocks, body, start = [], None, 0
    for lineno, line in enumerate(markdown.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            if body is None:
                body, start = [], lineno + 1
            else:
                blocks.append((start, "\n".join(body)))
                body = None
            continue
        if body is not None:
            body.append(line)
    return blocks


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
    offenders = []
    for path in sorted(list((_ROOT / "nmtcapp").rglob("*.py"))
                       + list((_ROOT / "streamlit_app").rglob("*.py"))):
        if "__pycache__" in str(path):
            continue
        offenders += _live_round_literals_in_python(
            path.read_text(), path.relative_to(_ROOT)
        )
    assert not offenders, (
        "live 'CY2025' round literal — the CDFI Fund has never run a round by "
        "that name:\n" + "\n".join(offenders)
    )


#: The trees this sweep reads. MANIFEST.in prunes ``examples``, ``docs`` and
#: ``scripts`` from the sdist TOGETHER, so their joint absence is the tarball
#: and the sweep has nothing to do. Exactly one present is a checkout with a
#: tree deleted, and that must FAIL rather than skip — an absent directory may
#: never be indistinguishable from a clean one. Same marker shape, and the
#: same reason, as ``test_documented_keys.docs_present``.
_SWEPT_TREES = ("examples", "docs", "scripts")
_TREES_PRESENT = [t for t in _SWEPT_TREES if (_ROOT / t).is_dir()]

_swept_trees_present = pytest.mark.skipif(
    not _TREES_PRESENT,
    reason="examples/, docs/ and scripts/ are all pruned from the sdist by "
           "MANIFEST.in; there is nothing here to sweep",
)


@_swept_trees_present
def test_no_live_cy2025_round_literal_in_examples_docs_or_scripts():
    """THE SWEEP MUST COVER THE CHANNEL THE README POINTS AT (1.5.5 audit B1).

    THE DEFECT THIS CLOSES. ``test_no_live_cy2025_round_literal_in_package_or_app``
    walked ``nmtcapp/`` and ``streamlit_app/`` and nothing else, so
    ``examples/01_quickstart.ipynb`` and
    ``examples/02_full_application_walkthrough.ipynb`` both still built the
    Application with ``application_round="CY2025"`` after the release named for
    removing that literal — and notebook 02 goes on to call ``generate()``.
    Executing the notebook's own code produced::

        Application Round: CY2025
        ...requests $65.0MM in New Markets Tax Credit allocation for
        application round CY2025...
        Riverbend Community Capital CDE, LLC targets a CY2025 award.

    The notebooks are pruned from the sdist, so a PyPI user never saw it. But
    ``README.md`` links both as the documented front door, and the repository
    is a shipping channel. A gate scoped to the importable package cannot see
    the surface most readers meet first.

    WHY THE FIX WAS TO OMIT THE ARGUMENT rather than substitute ``"CY 2026"``:
    this release's own ruling, in ``core/application_round``, is that swapping
    the false claim for an unverified one is not a fix. Omitting it makes the
    front-door example DEMONSTRATE the disclosure the release added — and it
    matches what ``README.md`` and every page under ``docs/`` already do, which
    is call ``Application(cde=..., requested_allocation=...)`` with no round.

    HOW EACH TREE IS READ, because they are three different languages:

      * ``examples/*.ipynb`` — the JSON is parsed and every CODE cell's source
        is AST-parsed, exactly as the package sweep reads a module. Not a text
        grep over the JSON: a grep cannot tell a live literal from a comment,
        and this suite's whole discipline is that comments recording the defect
        survive. All nine code cells across the three notebooks parse cleanly.
      * ``docs/**/*.py`` — AST, same helper.
      * ``docs/**/*.md`` and ``README.md`` — FENCED CODE BLOCKS ONLY. See
        ``_fenced_code_blocks`` for why prose is exempt.
      * ``scripts/*`` — non-comment lines.
    """
    assert len(_TREES_PRESENT) == len(_SWEPT_TREES), (
        f"only {_TREES_PRESENT} of {list(_SWEPT_TREES)} are present. The sdist "
        "carries none of them and this test skips there; a checkout missing "
        "one is a deleted tree, and a sweep that returned clean over it would "
        "be reporting silence as absence."
    )

    offenders = []
    swept_files = 0

    for nb_path in sorted((_ROOT / "examples").rglob("*.ipynb")):
        swept_files += 1
        cells = json.loads(nb_path.read_text()).get("cells", [])
        for index, cell in enumerate(cells):
            if cell.get("cell_type") != "code":
                continue
            offenders += _live_round_literals_in_python(
                "".join(cell.get("source", [])),
                f"{nb_path.relative_to(_ROOT)} cell {index}",
            )

    for py_path in sorted((_ROOT / "docs").rglob("*.py")):
        if "__pycache__" in str(py_path):
            continue
        swept_files += 1
        offenders += _live_round_literals_in_python(
            py_path.read_text(), py_path.relative_to(_ROOT)
        )

    md_paths = sorted((_ROOT / "docs").rglob("*.md")) + [_ROOT / "README.md"]
    for md_path in md_paths:
        swept_files += 1
        for start, block in _fenced_code_blocks(md_path.read_text()):
            for offset, line in enumerate(block.splitlines()):
                if _DEAD_ROUND in line:
                    offenders.append(
                        f"{md_path.relative_to(_ROOT)}:{start + offset}: "
                        f"{line.strip()[:90]!r}"
                    )

    for script in sorted((_ROOT / "scripts").rglob("*")):
        if not script.is_file():
            continue
        swept_files += 1
        for lineno, line in enumerate(script.read_text().splitlines(), start=1):
            if _DEAD_ROUND in line and not line.lstrip().startswith("#"):
                offenders.append(
                    f"{script.relative_to(_ROOT)}:{lineno}: {line.strip()[:90]!r}"
                )

    assert swept_files >= 6, (
        f"the sweep only reached {swept_files} files across "
        f"{list(_SWEPT_TREES)}. It is meant to cover three notebooks, the docs "
        "pages, README.md and scripts/; a walk this small is broken and every "
        "assertion below would pass over nothing."
    )
    assert not offenders, (
        "live 'CY2025' round literal outside nmtcapp/ and streamlit_app/ — the "
        "CDFI Fund has never run a round by that name, and these are the files "
        "the README points a reader at:\n" + "\n".join(offenders)
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


class TestExcelStandaloneDisclosure:
    """N2 — the waiver for ``ROUND_UNSPECIFIED_STANDALONE`` claimed cover it lacked.

    ``tests/pinned_constants.txt`` waives a PIN row for this constant on the
    ground that it has "the same waiver and same cover as
    ROUND_UNSPECIFIED_VALUE above". IT DID NOT. ``_VALUE``'s waiver names real
    cover and is honest about it: ``TestRenderedSurfaces`` renders the Markdown
    document and ``ApplicationAnalysis.summary()`` from an Application with no
    round and asserts the string is there. ``_STANDALONE`` had nothing of the
    kind. Nothing in the suite rendered a workbook without a round, so its only
    cover was ``test_disclosure_strings_name_no_round``, which asserts a
    property OF THE CONSTANT ("CY" is not in it) and never renders anything.

    All three constants were correct on the day this was written. The gap was
    REGRESSION cover: delete ``round_label_standalone``'s call from either
    Excel site and the whole suite stayed green. A waiver claiming cover it
    lacks is the "adjudicates nothing while appearing to" class, so the cover
    is added here rather than the claim softened.

    THE TWO SITES ARE BOTH ASSERTED, separately, because they are separate
    calls in separate methods -- ``excel_builder`` line 243 (the cover sheet's
    metadata strip) and line 717 (the pipeline sheet's sub-header) -- and one
    of them going quiet is exactly the regression this covers.

    WORD AND PDF ARE NOT LISTED HERE, and that is a measurement rather than an
    omission: ``round_label_standalone`` is imported by ``excel_builder`` and
    by nothing else. The standalone form has two rendering sites in this
    package, both in the workbook. ``test_the_standalone_form_renders_in_excel_and_nowhere_else``
    holds that, so a third site cannot appear uncovered.
    """

    @staticmethod
    @pytest.fixture(scope="class")
    def unset_workbook():
        pytest.importorskip("openpyxl")
        from nmtcapp.renderers.excel_builder import ExcelApplicationBuilder
        app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
        app.add_pipeline(Pipeline.sample(n=8))
        return ExcelApplicationBuilder(app, app.analyze()).build()

    @staticmethod
    def _all_strings(workbook) -> list:
        return [
            (sheet.title, cell.value)
            for sheet in workbook.worksheets
            for row in sheet.iter_rows()
            for cell in row
            if isinstance(cell.value, str)
        ]

    def test_a_workbook_built_without_a_round_names_no_round(self, unset_workbook):
        offenders = [
            f"{title}: {value[:110]!r}"
            for title, value in self._all_strings(unset_workbook)
            if "CY2025" in value
        ]
        assert not offenders, "workbook names the nonexistent round:\n" + "\n".join(offenders)

    def test_the_cover_sheet_metadata_strip_discloses_the_absent_round(
        self, unset_workbook
    ):
        cover = unset_workbook.worksheets[0]
        assert ROUND_UNSPECIFIED_STANDALONE in str(cover["A3"].value), (
            f"the cover sheet's metadata strip reads {cover['A3'].value!r}; a "
            "workbook generated with no round must say so where the round "
            "would stand, not leave a gap between two pipe characters"
        )

    def test_the_pipeline_sheet_sub_header_discloses_the_absent_round(
        self, unset_workbook
    ):
        hits = [
            title for title, value in self._all_strings(unset_workbook)
            if ROUND_UNSPECIFIED_STANDALONE in value and "Generated " in value
        ]
        assert hits, (
            "no sheet carries the generation sub-header with the round "
            "disclosure in it. excel_builder renders "
            "round_label_standalone() there; if that call was removed, this "
            "is the regression the pinned-constants waiver claimed was "
            "already covered and was not."
        )

    def test_a_supplied_round_still_renders_verbatim_in_the_workbook(self):
        pytest.importorskip("openpyxl")
        from nmtcapp.renderers.excel_builder import ExcelApplicationBuilder
        app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000,
                          application_round="CY 2026")
        app.add_pipeline(Pipeline.sample(n=8))
        strings = self._all_strings(ExcelApplicationBuilder(app, app.analyze()).build())
        assert any("CY 2026" in v for _t, v in strings)
        assert not any(ROUND_UNSPECIFIED_STANDALONE in v for _t, v in strings)

    @pytest.mark.skipif(
        not (_ROOT / "nmtcapp").is_dir(),
        reason="no nmtcapp/ source tree beside tests/ (unpacked sdist); this "
               "assertion walks the package SOURCE to enumerate its importers",
    )
    def test_the_standalone_form_renders_in_excel_and_nowhere_else(self):
        """The scope claim above, asserted rather than described."""
        importers = sorted(
            path.relative_to(_ROOT).as_posix()
            for path in (_ROOT / "nmtcapp").rglob("*.py")
            if "round_label_standalone" in path.read_text()
            and path.name != "application_round.py"
        )
        assert importers == ["nmtcapp/renderers/excel_builder.py"], (
            f"round_label_standalone is now rendered by {importers}. The "
            "waiver in tests/pinned_constants.txt and the cover in this class "
            "both scope to Excel; a new surface needs its own assertion here."
        )
