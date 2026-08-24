""".xlsx IS ZIPPED XML, AND EVERY TEXT SWEEP THIS PACKAGE RUNS WALKS PAST IT.

WHY THIS FILE EXISTS (1.5.7 T5)

``tests/test_application_round.py`` sweeps for the dead ``CY2025`` literal
across ``nmtcapp/``, ``streamlit_app/``, ``docs/``, ``README.md``, the
notebooks and ``scripts/``. It is a careful gate and it is not broken. It
reads those trees AS TEXT.

The two workbooks this package SHIPS are not text::

    grep -c "CY2025" pipeline_sample.xlsx        ->  0   (exit 1)
    unzip -p ...; grep -rl "CY2025" .            ->  xl/worksheets/sheet1.xml
                                                     xl/worksheets/sheet4.xml

So in the release AFTER the one whose entire thesis was removing a round the
CDFI Fund has never run, BOTH shipped workbooks still offered ``CY2025`` in
the ``Valid Values`` sheet's "App Round" column -- including
``pipeline_template.xlsx``, which the app serves as "Download blank template
(Excel)" -- and ``pipeline_sample.xlsx`` still STATED it in its own
"Application Round" cell.

AND ONE OF THE THREE SITES IS INVISIBLE TO openpyxl'S CELL ITERATION TOO.
Both workbooks carried a data-validation DROPDOWN on the CDE Profile sheet
whose inline list was ``<formula1>"CY2025,CY2026"</formula1>`` -- not a cell
value, so a gate that walks ``ws.iter_rows()`` sees nothing, while the user
picking from that dropdown is offered the dead round first. That is why this
gate reads the RAW XML of every zip member rather than the parsed workbook:
the parsed view is a strictly smaller surface than the shipped file.

THE GATE IS THE GENERAL FIX; THE WORKBOOK EDITS ARE THE INSTANCE.

  !!  SCOPE LIMIT  !!
  This reads the workbooks as bytes. It observes text present anywhere in any
  XML part -- cell values, inline strings, shared strings, data validations,
  headers, footers, defined names. It does NOT observe what Excel RENDERS
  (merge geometry is checked structurally below, not visually), does not open
  Excel, and says nothing about the .docx/.pdf renderers.
"""
from __future__ import annotations

import os
import re
import sys
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tests.conftest import templates_dir

#: The round the CDFI Fund has never run. Read from the gate that owns the
#: claim rather than retyped, so the two cannot drift apart.
from tests.test_application_round import _DEAD_ROUND

#: Both shipped workbooks, resolved from the INSTALLED package so the sdist
#: job asks about the files that are actually distributed.
_WORKBOOKS = ("pipeline_sample.xlsx", "pipeline_template.xlsx")


def _members(name: str) -> dict:
    path = Path(templates_dir()) / name
    assert path.exists(), f"shipped workbook missing: {path}"
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


@pytest.fixture(scope="module", params=_WORKBOOKS)
def workbook(request):
    return request.param, _members(request.param)


class TestNoDeadRoundSurvivesAnywhereInTheZip:
    def test_the_dead_round_appears_in_no_xml_part(self, workbook):
        name, members = workbook
        needle = _DEAD_ROUND.encode()
        offenders = sorted(part for part, data in members.items() if needle in data)
        assert not offenders, (
            f"{name} still carries the dead round {_DEAD_ROUND!r} in "
            f"{offenders}. A text grep over the repository CANNOT see this -- "
            ".xlsx is zipped XML -- which is how it survived the release that "
            "removed the literal from every .py file."
        )

    def test_the_app_round_dropdown_offers_no_dead_round(self, workbook):
        """The dropdown is a ``<formula1>`` inline list, NOT a cell value."""
        name, members = workbook
        sheet = members["xl/worksheets/sheet1.xml"].decode("utf8")
        lists = re.findall(r"<formula1>([^<]*)</formula1>", sheet)
        round_lists = [v for v in lists if "CY" in v]
        assert round_lists, (
            f"{name}'s CDE Profile sheet has no round dropdown at all; this "
            "gate's premise is gone and it is asserting nothing."
        )
        offenders = [v for v in round_lists if _DEAD_ROUND in v]
        assert not offenders, (
            f"{name} offers the dead round in a data-validation dropdown: "
            f"{offenders}. openpyxl's cell iteration cannot see this."
        )


class TestTheIdentityBannerDoesNotClaimTheRequestColumns:
    """THE ORIGIN OF 1.5.5's B6, FIXED AT THE SOURCE (1.5.7 T5.3).

    The CDE Profile sheet's row-2 section banner spanned ``A2:K2`` -- columns
    1 through 11 -- and columns 10 and 11 are ``Requested Allocation ($M)``
    and ``Application Round``. Neither is identity: one is a REQUEST and the
    other is the round that request is filed into. ``_IDENTITY_KEYS`` in
    ``streamlit_app/utils.py`` faithfully mirrored a mislabelled banner, and
    the two defects that followed -- a stated round discarded, then a stated
    allocation replaced by \\$65,000,000 -- both trace to that mirror.

    Fixing the code and leaving the banner would leave the next reader the
    same wrong instruction the last one followed.
    """

    #: 1-indexed columns of the two cells that are NOT identity.
    _REQUEST_COLUMNS = (10, 11)

    @staticmethod
    def _col_index(ref: str) -> int:
        letters = re.match(r"([A-Z]+)", ref).group(1)
        n = 0
        for ch in letters:
            n = n * 26 + (ord(ch) - 64)
        return n

    def test_the_identity_banner_stops_before_the_request_columns(self, workbook):
        name, members = workbook
        sheet = members["xl/worksheets/sheet1.xml"].decode("utf8")
        merges = re.findall(r'<mergeCell ref="([A-Z]+\d+):([A-Z]+\d+)"/>', sheet)
        row2 = [(a, b) for a, b in merges if a.endswith("2") and b.endswith("2")]
        assert row2, f"{name} has no row-2 section banners; premise gone."

        # Which banner covers column 1 (CDE Name)? That is the Identity band.
        identity = [
            (a, b) for a, b in row2
            if self._col_index(a) <= 1 <= self._col_index(b)
        ]
        assert len(identity) == 1, (
            f"{name}: expected exactly one row-2 banner over column A, "
            f"found {identity}"
        )
        start, end = identity[0]
        last = self._col_index(end)
        claimed = [c for c in self._REQUEST_COLUMNS if c <= last]
        assert not claimed, (
            f"{name}'s Identity banner spans {start}:{end}, which covers "
            f"column(s) {claimed} -- 'Requested Allocation ($M)' and/or "
            "'Application Round'. Neither is identity, and labelling them so "
            "is the origin of the two defects 1.5.5 and 1.5.7 had to fix in "
            "the code that mirrored this banner."
        )

    def test_the_request_columns_carry_a_banner_of_their_own(self, workbook):
        name, members = workbook
        sheet = members["xl/worksheets/sheet1.xml"].decode("utf8")
        merges = re.findall(r'<mergeCell ref="([A-Z]+\d+):([A-Z]+\d+)"/>', sheet)
        covering = [
            (a, b) for a, b in merges
            if a.endswith("2") and b.endswith("2")
            and self._col_index(a) <= 10 <= self._col_index(b)
        ]
        assert covering, (
            f"{name}: columns 10-11 sit under NO row-2 banner at all. They "
            "are not identity, but an unlabelled band is its own defect -- "
            "the reader is owed a heading that says what they are."
        )
