"""1.3.0 S3: the QLICI figure the CDE never supplied.

WHAT WENT WRONG

``core/upload_handler.load_uploaded_pipeline`` ended with three lines of
column synthesis::

    if "qlici_amount" not in df.columns and "qei_request" in df.columns:
        df["qlici_amount"] = df["qei_request"]

Silently. No flag, no warning, nothing downstream that could tell the copied
value from a supplied one. That value then rendered as **"Total QLICI ($)"** in
Appendix A — the CDE's own answer to the CDFI Fund's Table A5 row (h) — on
markdown, Word, PDF *and* Excel, and satisfied ``validation/consistency_check``'s
QLICI <= QEI rule by being exactly equal to the QEI it was copied from. A check
that cannot fail is worse than no check, because it is also a green tick.

WHY FOUR PASSES MISSED IT

Every fixture in this package sets ``qlici_amount == qei_request``: both shipped
sample CSVs, ``Pipeline.sample()``, ``tests/test_rendered_output_baseline``'s
fixture, and the pin fixtures. A fixture that collapses two distinct inputs
cannot exercise the distinction. (``tests/test_qlici_basis._divergent_pipeline``
is the one exception, added by 1.2.1's FIX-3 — it diverges the two amounts but
constructs ``PipelineProject`` objects directly, so it never crosses the upload
path where the defaulting happens and never renders a document.)

WHAT THIS FILE ADDS, AND WHY EACH ONE IS NEEDED

  ``_upload_divergent``  an UPLOAD whose qlici_amount differs from its
                         qei_request. Proves the supplied path still renders the
                         CDE's own figure, and proves the not-supplied rendering
                         is not simply firing on everything.
  ``_upload_no_column``  an upload with NO qlici_amount column at all. The
                         fixture the defect needed and the package did not have.

Converting the remaining collapsed fixtures is 1.3.1; these two are what S3
needs.

THE PROVENANCE IS CARRIED, NOT INFERRED

``test_provenance_is_not_inferred_from_equality`` is the gate that matters most.
The cheap check — ``qlici_amount == qei_request`` — is true of every fixture
this package ships and of plenty of real pipelines, so a CDE whose figures
legitimately match would have its own supplied number replaced with
"not supplied". The flag rides the temp CSV that
``load_uploaded_pipeline`` writes between itself and ``Pipeline.from_csv``,
which is a real serialization boundary and is why the flag is a COLUMN rather
than an attribute set on the way past.
"""
from __future__ import annotations

import logging
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.upload_handler import load_uploaded_pipeline
from nmtcapp.renderers._cell_format import NOT_SUPPLIED_INPUT
from nmtcapp.tables.pipeline_table import build_pipeline_table
from nmtcapp.validation.consistency_check import check_consistency
from tests.test_rendered_output_baseline import FORMATS, _extract

# ---------------------------------------------------------------------------
# Fixtures — the two S3 needs, and neither of them collapses the two amounts
# ---------------------------------------------------------------------------

_COLS_WITH = (
    "project_id,project_name,qalicb_name,address,city,state,sector,"
    "project_type,total_project_cost,qei_request,qlici_amount,"
    "expected_jobs_created,expected_jobs_retained,census_tract,"
    "distress_level,native_area,high_migration_rural"
)
_COLS_WITHOUT = _COLS_WITH.replace(",qlici_amount", "")

#: (id, name, cost, qei, qlici). The QLICIs are deliberately NOT the QEIs and
#: are not a fixed fraction of them either — a constant ratio is its own kind of
#: collapsed fixture.
_ROWS = (
    ("PRJ-S01", "Riverbend Clinic",   9_000_000, 6_000_000, 5_100_000),
    ("PRJ-S02", "Fairview Grocery",   7_500_000, 5_000_000, 2_250_000),
    ("PRJ-S03", "Northgate Workshop", 4_400_000, 3_000_000, 2_940_000),
)


def _csv(with_qlici: bool) -> bytes:
    header = _COLS_WITH if with_qlici else _COLS_WITHOUT
    lines = [header]
    for i, (pid, name, cost, qei, qlici) in enumerate(_ROWS):
        money = f"{cost},{qei},{qlici}" if with_qlici else f"{cost},{qei}"
        lines.append(
            f'{pid},"{name}","{name} QALICB, LLC","{200 + i} River Road",'
            f"Toledo,OH,healthcare,real_estate,{money},"
            f"{30 + i},{8 + i},3909500{i:04d},severe,N,N"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _upload_divergent():
    pipeline, _ = load_uploaded_pipeline(_csv(True), "divergent.csv")
    pipeline.eligibility_data_status = "ok"
    return pipeline


def _upload_no_column():
    pipeline, _ = load_uploaded_pipeline(_csv(False), "no_qlici_column.csv")
    pipeline.eligibility_data_status = "ok"
    return pipeline


def _cde() -> CDEProfile:
    return CDEProfile(
        name="Maumee Valley Community Capital, LLC",
        cde_id="CDE-2019-0742",
        certification_date="2019-07-42".replace("42", "12"),
        mission=(
            "Provide New Markets Tax Credit financing to health and food-access "
            "projects in northwest Ohio."
        ),
        target_markets=["Ohio"],
        prior_awards=[
            {"year": 2022, "amount": 35_000_000,
             "deployment_status": "fully_deployed"},
        ],
        contact={"name": "T. Okonkwo", "email": "tokonkwo@mvcc.example.org",
                 "phone": "419-555-0142", "title": "President"},
        governance={"board_members": 11, "community_representatives": 5,
                    "advisory_board_members": 6},
    )


def _application(pipeline) -> Application:
    app = Application(cde=_cde(), requested_allocation=30_000_000.0,
                      application_round="CY2025")
    app.add_pipeline(pipeline)
    return app


# ---------------------------------------------------------------------------
# The fixtures must not collapse — every gate below is vacuous if they do
# ---------------------------------------------------------------------------

def test_the_divergent_upload_actually_diverges():
    """FAILS CLOSED. This is the property the whole file rests on."""
    projects = list(_upload_divergent())
    assert len(projects) == len(_ROWS)
    assert all(p.qlici_amount != p.qei_request for p in projects), (
        "the divergent fixture collapsed — every project must carry a QLICI "
        "that differs from its QEI, which is the distinction four passes over "
        "this package could not exercise"
    )
    ratios = {round(p.qlici_amount / p.qei_request, 4) for p in projects}
    assert len(ratios) == len(projects), (
        "the QLICI/QEI ratios are not all distinct — a fixed ratio is its own "
        "collapsed fixture and would hide a proportional-scaling defect"
    )


def test_the_no_column_upload_really_has_no_column():
    assert b"qlici_amount" not in _csv(False), (
        "the no-column fixture grew a qlici_amount column; it exists to be the "
        "input the defect needed"
    )
    assert b"qlici_amount" in _csv(True)


# ---------------------------------------------------------------------------
# Provenance: carried, and carried ACROSS THE SERIALIZATION BOUNDARY
# ---------------------------------------------------------------------------

def test_supplied_amounts_are_marked_supplied():
    assert all(p.qlici_amount_supplied for p in _upload_divergent())


def test_absent_column_is_marked_not_supplied():
    projects = list(_upload_no_column())
    assert projects, "fixture loaded nothing"
    assert not any(p.qlici_amount_supplied for p in projects)
    # The value is still there — the pipeline has to load — it is just no
    # longer presented as the CDE's.
    assert all(p.qlici_amount == p.qei_request for p in projects)


def test_provenance_is_not_inferred_from_equality():
    """THE GATE THAT MATTERS MOST.

    A CDE whose QLICI legitimately equals its QEI must keep its own figure. If
    this ever fails, someone has replaced the carried flag with the cheap check
    — and the cheap check is true of both shipped samples, of Pipeline.sample(),
    of the pin fixtures and of the rendered baseline fixture.
    """
    header = _COLS_WITH
    row = ('PRJ-EQ1,"Equal Amounts Project","Equal Amounts QALICB, LLC",'
           "1 Same Street,Toledo,OH,healthcare,real_estate,"
           "7000000,5000000,5000000,20,4,39095000001,severe,N,N")
    pipeline, _ = load_uploaded_pipeline(
        (header + "\n" + row + "\n").encode("utf-8"), "equal.csv")
    p = list(pipeline)[0]
    assert p.qlici_amount == p.qei_request, "fixture setup"
    assert p.qlici_amount_supplied, (
        "a supplied QLICI that happens to equal its QEI was reported as not "
        "supplied. The provenance is being inferred from equality instead of "
        "carried, and this CDE's own figure has been replaced in its filing."
    )
    df = build_pipeline_table(pipeline, _cde())
    assert NOT_SUPPLIED_INPUT not in df["Total QLICI ($)"].astype(str).tolist()


def test_the_flag_survives_the_temp_csv_boundary():
    """load_uploaded_pipeline writes a temp CSV and re-reads it via from_csv.

    Stated as a test because it is the reason the flag is a COLUMN. An
    attribute set on the DataFrame, or on the Pipeline before ``from_csv``
    returns, does not exist on the far side.
    """
    from nmtcapp.core.pipeline import Pipeline
    import inspect
    src = inspect.getsource(Pipeline.from_csv)
    assert "qlici_amount_supplied" in src, (
        "Pipeline.from_csv no longer reads the provenance column. Whatever "
        "upload_handler writes now dies at the temp-CSV boundary and every "
        "not-supplied rendering below is silently back to a defaulted number."
    )


# ---------------------------------------------------------------------------
# Warned at upload time — the silent default is what hid this for four passes
# ---------------------------------------------------------------------------

def test_upload_warns_when_the_column_is_absent(caplog):
    with caplog.at_level(logging.WARNING, logger="nmtcapp.core.upload_handler"):
        load_uploaded_pipeline(_csv(False), "no_qlici_column.csv")
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "qlici_amount" in text and "not" in text.lower(), (
        "an upload missing qlici_amount produced no warning. The silent "
        f"default is the reason this survived four passes. Got: {text!r}"
    )


def test_upload_does_not_warn_when_the_column_is_present(caplog):
    with caplog.at_level(logging.WARNING, logger="nmtcapp.core.upload_handler"):
        load_uploaded_pipeline(_csv(True), "divergent.csv")
    assert not [r for r in caplog.records if "qlici_amount" in r.getMessage()], (
        "a warning fired on an upload that supplied the column — this gate "
        "would then pass on anything"
    )


# ---------------------------------------------------------------------------
# consistency_check: NOT-CHECKABLE, REPORTED. Not skipped.
# ---------------------------------------------------------------------------

def test_qlici_le_qei_is_reported_as_not_checked_when_defaulted():
    """The ruling, as a test.

    REJECTED ALTERNATIVE — skip the comparison silently. ``passed`` stays True
    either way, so a reader of the validation report cannot tell "checked and
    passed" from "not checked at all", and the check would have gone from
    trivially-passing to invisibly-absent. This module already refuses that
    shape: ``CrossSurfaceCheckError`` is RAISED rather than returned for
    exactly the same reason.
    """
    result = check_consistency(_application(_upload_no_column()))
    hits = [w for w in result.warnings if "NOT CHECKED" in w]
    assert len(hits) == len(_ROWS), (
        "the QLICI <= QEI check did not report itself as unaskable on a "
        f"pipeline where no QLICI was supplied. Warnings: {result.warnings!r}"
    )
    for w in hits:
        assert "QLICI <= QEI" in w and "qlici_amount" in w


def test_qlici_le_qei_still_runs_when_the_value_was_supplied():
    """FAILS CLOSED: the not-checkable branch must not swallow the real rule."""
    pipeline = _upload_divergent()
    # Push one project's QLICI above its QEI. It was supplied, so the rule
    # applies and must fire.
    list(pipeline)[0].qlici_amount = list(pipeline)[0].qei_request * 1.5
    result = check_consistency(_application(pipeline))
    assert any("exceeds" in i and "QLICI" in i for i in result.issues), (
        "the QLICI <= QEI rule stopped firing on a supplied, over-limit "
        f"amount. Issues: {result.issues!r}"
    )
    assert not [w for w in result.warnings if "NOT CHECKED" in w]


# ---------------------------------------------------------------------------
# END TO END — the rendering, on all four surfaces
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rendered_without_column(tmp_path_factory):
    out = tmp_path_factory.mktemp("no_qlici")
    app = _application(_upload_no_column())
    paths = app.generate(str(out), formats=list(FORMATS))
    assert set(paths) == set(FORMATS), (
        f"only {sorted(paths)} rendered; a format that does not render is a "
        "format this gate is not checking"
    )
    return {fmt: _extract(fmt, path) for fmt, path in paths.items()}


@pytest.fixture(scope="module")
def rendered_with_column(tmp_path_factory):
    out = tmp_path_factory.mktemp("with_qlici")
    app = _application(_upload_divergent())
    paths = app.generate(str(out), formats=list(FORMATS))
    return {fmt: _extract(fmt, path) for fmt, path in paths.items()}


#: WHICH SURFACES CARRY THE CELL, MEASURED RATHER THAN ASSUMED.
#:
#: "Total QLICI ($)" is a column of ``tables/pipeline_table.build_pipeline_table``,
#: and only TWO renderers publish that table: markdown writes it whole, Excel
#: writes it to the Pipeline Detail sheet. Word and PDF print the six-column
#: ``build_pipeline_summary_table`` in portrait, and Word's landscape
#: continuation names twelve columns of which QLICI is not one. Verified on the
#: committed baseline: ``grep -c "Total QLICI"`` returns 1, 0, 0, 1 for
#: markdown, word, pdf, excel.
#:
#: So the defaulted figure never reached Word or PDF, and inventing a QLICI
#: column for them to hold a marker would change the shape of a federal
#: attachment in order to make a test pass. What those two surfaces get instead
#: is the disclosure sentence — because a CDE reading only the filed document
#: must still learn that a column it never supplied was defaulted.
_CELL_SURFACES = ("markdown", "excel")
_SENTENCE_SURFACES = ("word", "pdf")


@pytest.mark.parametrize("fmt", FORMATS)
def test_absent_qlici_is_disclosed_on_every_surface(rendered_without_column, fmt):
    """All four surfaces say it. Two say it in a cell, two say it in a sentence."""
    text = rendered_without_column[fmt]
    assert len(text) > 2000, f"{fmt} extracted {len(text)} chars — too short"
    if fmt in _CELL_SURFACES:
        assert NOT_SUPPLIED_INPUT in text, (
            f"{fmt} does not carry {NOT_SUPPLIED_INPUT!r}. A QLICI amount the "
            "tool defaulted from the QEI is being presented as the CDE's own "
            "answer to the CDFI Fund's Table A5 row (h)."
        )
    else:
        assert "NO QLICI AMOUNT WAS SUPPLIED" in text, (
            f"{fmt} prints no QLICI column and now carries no disclosure "
            "either, so a CDE reading only this artifact would never learn "
            "that the figure was defaulted."
        )
    # Every surface names the projects, whichever way it says it.
    for pid, *_ in _ROWS:
        assert pid in text


@pytest.mark.parametrize("fmt", _CELL_SURFACES)
def test_the_defaulted_figure_is_replaced_in_every_qlici_cell(
    rendered_without_column, fmt
):
    """The marker must fill the column, not annotate one row of it.

    Every project's defaulted QLICI equals its QEI, and the QEI is legitimately
    printed elsewhere in the same document — so this cannot assert the digits
    are missing from the page. It asserts the count instead.
    """
    text = rendered_without_column[fmt]
    # One occurrence per project, plus the TOTALS row, which also refuses to
    # sum around a value nobody supplied.
    assert text.count(NOT_SUPPLIED_INPUT) >= len(_ROWS) + 1, (
        f"{fmt} carries {text.count(NOT_SUPPLIED_INPUT)} not-supplied cells; "
        f"expected at least {len(_ROWS) + 1} (one per project plus the TOTALS "
        "row, which must not sum around a figure the CDE never gave)"
    )


def test_the_surface_split_is_still_what_it_was_measured_to_be(
    rendered_with_column,
):
    """FAILS CLOSED on the premise of the split above.

    If a renderer starts or stops publishing the QLICI column, ``_CELL_SURFACES``
    is stale and the test above silently stops checking a surface that now
    prints the figure.
    """
    for fmt in _CELL_SURFACES:
        assert "Total QLICI" in rendered_with_column[fmt], (
            f"{fmt} no longer publishes the Total QLICI column; move it out of "
            "_CELL_SURFACES and check what it prints instead"
        )
    for fmt in _SENTENCE_SURFACES:
        assert "Total QLICI" not in rendered_with_column[fmt], (
            f"{fmt} has started publishing a Total QLICI column. It now needs "
            "the cell treatment, not only the disclosure sentence."
        )


@pytest.mark.parametrize("fmt", FORMATS)
def test_a_supplied_qlici_triggers_neither_disclosure(rendered_with_column, fmt):
    """FAILS CLOSED. Without this the fix could be "never print the column"."""
    text = rendered_with_column[fmt]
    assert NOT_SUPPLIED_INPUT not in text, (
        f"{fmt} printed the not-supplied marker on a pipeline that supplied "
        "every QLICI amount"
    )
    assert "NO QLICI AMOUNT WAS SUPPLIED" not in text


def test_the_totals_row_refuses_to_sum_around_a_missing_input():
    df = build_pipeline_table(_upload_no_column(), _cde())
    totals = df.iloc[-1]
    assert str(totals["Project ID"]) == "TOTALS", "fixture shape changed"
    assert totals["Total QLICI ($)"] == NOT_SUPPLIED_INPUT, (
        "the TOTALS row summed a column containing values the CDE never "
        "supplied, filing a partial figure under the word TOTALS with nothing "
        "on the page saying it is partial"
    )
    # The columns that WERE supplied still total. A not-supplied cell poisons
    # its own column and no other.
    assert isinstance(totals["QEI Request ($)"], (int, float))
    assert totals["QEI Request ($)"] == sum(r[3] for r in _ROWS)
