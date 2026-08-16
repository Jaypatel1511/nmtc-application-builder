"""THE REGRESSION GATE: a rendered line may not change without being reviewed.

WHY THIS EXISTS

Every other gate in this package asks whether a rendered line is ENTITLED to be
there. The invariance gate asks whether a line was derived from the input. The
constant gate asks whether a published value prints as pinned. The attribution
gate asks whether a claim carries a citation. The cross-surface check asks
whether two surfaces agree.

None of them asks WHAT CHANGED.

That is not a theoretical gap. Two consecutive rounds each shipped a defect
created by the round's own fix, in the renderers, and every gate stayed green:

    1.2.1 B-5's fix (splitting the 85%/20% distress bars onto their own rows)
        created a filing that stated 0.0% severe distress in Section B and
        flagged the same projects "Yes" in Appendix B — because the row it
        added read the EXCLUSIVE severe bucket under an INCLUSIVE label.

    1.2.1 B-1's fix (unifying cell formatting across the four renderers)
        created prior-award years rendering as 2,019 on markdown, Word and PDF
        — because the plain-number arm of the new formatter ends in
        ``f"{value:,}"`` and a year is not a quantity.

Both were found by a human reading the output. A byte-diff of all four formats
between v1.2.0 and the branch head, from one fixed fixture, showed both in
ninety seconds. Nobody had ever diffed this package's output against its own
last release.

READING DOES NOT SCALE. This is that diff, kept.

THE METHOD

One fixed, fully-populated fixture — NOT Pipeline.sample(), whose rows changed
between releases, which would report input edits as output changes and bury
everything else. Render all four formats. Project each artifact to text,
INCLUDING the parts that are not text: Excel number formats are extracted
alongside cell values, because the year defect is a number-format defect and
the cell value 2019 is correct either way.

Normalise only what is genuinely non-deterministic — timestamps, temp paths,
today's date. Diff every remaining line against a committed baseline.

A changed line fails. The fix is to read the diff and, if the change is
intended, update the baseline in the same commit — which puts every rendered
change in front of a reviewer in the pull request, as a diff of the DOCUMENT
rather than of the code that produces it.

This is the invariant allowlist's shape applied to CHANGE rather than to
INVARIANCE, and for the same reason: a new line fails by default and has to be
argued past a human.

FAILS CLOSED. A missing format, an empty extraction, a baseline that is absent
or suspiciously short, or a fixture that stops populating a field all ERROR
rather than pass.
"""
from __future__ import annotations

import datetime
import difflib
import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject

FORMATS = ("markdown", "word", "excel", "pdf")

BASELINE_DIR = os.path.join(os.path.dirname(__file__), "rendered_baseline")

# Below this, the baseline is not describing a whole application and the diff
# would pass on a document that had mostly stopped rendering.
_MIN_BASELINE_LINES = {
    "markdown": 300,
    "word": 180,
    "excel": 500,
    "pdf": 700,
}


# ---------------------------------------------------------------------------
# THE FIXTURE. Written once, here, and deliberately not Pipeline.sample().
#
# Every optional field is populated on at least one project, and the rows vary
# in the dimensions the two known regressions lived in:
#
#   distress  deep AND severe both present, so the subset relation is visible
#   units     PRJ-D03 supplies a genuine 0; PRJ-D01/02/05/07/08 supply nothing;
#             the rest supply a positive count — all three states in one table
#   tract     11-digit GEOIDs, which must never acquire a thousands separator
#   awards    three prior awards, whose YEARS are the identifier column that
#             regressed
# ---------------------------------------------------------------------------

def _cde() -> CDEProfile:
    return CDEProfile(
        name="Great Lakes Regional Capital CDE, LLC",
        cde_id="CDE-2016-0777",
        certification_date="2016-04-11",
        mission=(
            "Deploy New Markets Tax Credit capital into severely distressed "
            "census tracts across the eastern Great Lakes, with a standing "
            "preference for operating businesses that hire locally."
        ),
        target_markets=["Michigan", "Ohio", "Pennsylvania", "New York"],
        prior_awards=[
            {"year": 2019, "amount": 45_000_000, "deployment_status": "fully_deployed"},
            {"year": 2021, "amount": 60_000_000, "deployment_status": "fully_deployed"},
            {"year": 2023, "amount": 55_000_000, "deployment_status": "partially_deployed"},
        ],
        contact={
            "name": "Dana Okonkwo",
            "email": "dokonkwo@greatlakesregional.example.org",
            "phone": "216-555-0142",
            "title": "Chief Lending Officer",
        },
        governance={
            "board_members": 11,
            "community_representatives": 5,
            "advisory_board_members": 9,
            "board_meeting_frequency": "Bi-monthly",
        },
        website="https://greatlakesregional.example.org",
        extra={
            "years_operating": 9,
            "prior_award_count": 3,
            "has_prior_reporting_issues": False,
            "cde_type": "nonprofit_controlled",
        },
    )


# id, name, city, state, sector, ptype, cost, qei, jobs, retained,
# units, sqft, tract, distress, eligible
_SPEC = [
    ("PRJ-D01", "Erie Shoreline Health Pavilion", "Erie", "PA",
     "healthcare", "real_estate", 18_400_000, 13_000_000, 96, 34,
     None, 74_500.0, "42049000300", "deep", True),
    ("PRJ-D02", "Toledo Advanced Components Plant", "Toledo", "OH",
     "small_business", "operating_business", 24_750_000, 17_500_000, 143, 61,
     None, 210_000.0, "39095002400", "severe", True),
    ("PRJ-D03", "Buffalo East Side Grocery Anchor", "Buffalo", "NY",
     "other", "operating_business", 9_300_000, 6_600_000, 52, 18,
     0, 31_200.0, "36029006702", "severe", True),
    ("PRJ-D04", "Flint Riverfront Mixed-Income Lofts", "Flint", "MI",
     "affordable_housing", "real_estate", 31_200_000, 22_000_000, 27, 6,
     118, 165_000.0, "26049000900", "deep", True),
    ("PRJ-D05", "Youngstown Workforce Training Institute", "Youngstown", "OH",
     "education", "real_estate", 12_650_000, 8_900_000, 41, 15,
     None, 44_800.0, "39099810900", "lic", True),
    ("PRJ-D06", "Saginaw Community Wellness Center", "Saginaw", "MI",
     "community_facility", "real_estate", 7_450_000, 5_200_000, 33, 11,
     24, 28_300.0, "26145000200", "severe", True),
    ("PRJ-D07", "Scranton Solar Manufacturing Line", "Scranton", "PA",
     "clean_energy", "operating_business", 15_900_000, 11_200_000, 78, 29,
     None, 96_400.0, "42069100900", "deep", True),
    ("PRJ-D08", "Rochester Main Street Small Business Fund", "Rochester", "NY",
     "small_business", "operating_business", 5_800_000, 4_100_000, 62, 24,
     None, 12_700.0, "36055004400", "lic", True),
]


def _pipeline() -> Pipeline:
    projects = []
    for i, row in enumerate(_SPEC):
        (pid, name, city, state, sector, ptype, cost, qei, jobs, retained,
         units, sqft, tract, distress, eligible) = row
        p = PipelineProject(
            project_id=pid,
            project_name=name,
            qalicb_name=f"{name} QALICB, LLC",
            address=f"{1100 + 25 * i} Commerce Street",
            city=city,
            state=state,
            sector=sector,
            project_type=ptype,
            total_project_cost=float(cost),
            qei_request=float(qei),
            qlici_amount=float(qei),
            expected_jobs_created=jobs,
            expected_jobs_retained=retained,
            expected_units_built=units,
            expected_sq_ft=sqft,
            # Fixed, not derived from today — a date that moves would make
            # every run a diff.
            closing_target_date=f"2026-{(i % 12) + 1:02d}-15",
            construction_start=f"2026-{(i % 12) + 1:02d}-28",
            operations_start=f"2027-{(i % 12) + 1:02d}-01",
        )
        p.census_tract = tract
        p.is_nmtc_eligible = eligible
        p.distress_level = distress
        p.is_native_area = (i == 5)
        p.is_high_migration_rural = (i == 6)
        p.is_opportunity_zone = (i % 3 == 0)
        p.is_us_territory = False
        p.is_persistent_poverty = (i % 4 == 0)
        p.is_below_market_rate = (i % 2 == 0)
        p.is_unrelated_entity = True
        p.geocode_success = True
        projects.append(p)
    pipeline = Pipeline(projects)
    # Same reasoning as tests/test_invariant_output.py: these rows carry
    # verified-shaped data on purpose, so the adapter's pre-enriched branch
    # must not route the whole document into the degraded banner and make the
    # baseline a picture of the failure mode instead of the document.
    pipeline.eligibility_data_status = "ok"
    return pipeline


REQUESTED_ALLOCATION = 70_000_000.0
APPLICATION_ROUND = "CY2025"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _extract(fmt: str, path: str) -> str:
    if fmt == "markdown":
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    if fmt == "word":
        from docx import Document
        doc = Document(path)
        parts = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(f"P|{p.style.name}|{p.text}")
        for t_i, table in enumerate(doc.tables):
            for r_i, row in enumerate(table.rows):
                cells = [c.text.replace("\n", "\\n") for c in row.cells]
                parts.append(f"T{t_i}|R{r_i}|" + "|".join(cells))
        for section in doc.sections:
            for p in section.header.paragraphs:
                if p.text.strip():
                    parts.append(f"HDR|{p.text}")
            for p in section.footer.paragraphs:
                if p.text.strip():
                    parts.append(f"FTR|{p.text}")
        return "\n".join(parts)

    if fmt == "excel":
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        parts = []
        for ws in wb.worksheets:
            parts.append(f"@@SHEET {ws.title}")
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is None:
                        continue
                    # THE NUMBER FORMAT IS PART OF THE OUTPUT. openpyxl's value
                    # read returns 2019 whether the cell displays "2019" or
                    # "2,019", so a value-only projection could not see B-3 at
                    # all — the defect that motivated this file.
                    parts.append(
                        f"{ws.title}!{cell.coordinate}|"
                        f"{type(cell.value).__name__}|"
                        f"fmt={cell.number_format}|{cell.value}"
                    )
        return "\n".join(parts)

    if fmt == "pdf":
        from pypdf import PdfReader
        pages = []
        for i, page in enumerate(PdfReader(path).pages):
            pages.append(f"@@PAGE {i + 1}")
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    raise AssertionError(f"unknown format {fmt}")


_ISO_TS = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?")
_DATE_LONG = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December) \d{1,2}, \d{4}\b"
)


def _normalise(text: str, outdir: str) -> str:
    """Erase ONLY what is genuinely non-deterministic.

    Deliberately narrow. Every normalisation is a line this gate stops
    watching, so the list is timestamps, temp paths and today's date — and
    nothing else. The fixture's own dates (certification_date, closing target,
    construction start) are fixed values and must survive: they are output.
    """
    text = text.replace(outdir, "<OUTDIR>")
    text = re.sub(r"/(?:private/)?(?:tmp|var)/[^\s\"']*", "<TMPPATH>", text)
    text = _ISO_TS.sub("<TIMESTAMP>", text)
    text = _DATE_LONG.sub("<DATE>", text)
    text = text.replace(datetime.date.today().isoformat(), "<TODAY>")
    return text


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict:
    """{format: normalised text projection} for the one fixed fixture."""
    out = str(tmp_path_factory.mktemp("baseline"))
    app = Application(
        cde=_cde(),
        requested_allocation=REQUESTED_ALLOCATION,
        application_round=APPLICATION_ROUND,
    )
    app.add_pipeline(_pipeline())
    paths = app.generate(out, formats=list(FORMATS))

    assert set(paths) == set(FORMATS), (
        f"rendered {sorted(paths)}, expected all of {sorted(FORMATS)}. A "
        "format that silently does not render is a format this gate is not "
        "watching, and the missing one is where the next regression lands."
    )

    projected = {}
    for fmt in FORMATS:
        assert os.path.exists(paths[fmt]), f"{fmt} was not written"
        text = _normalise(_extract(fmt, paths[fmt]), out)
        assert text.strip(), (
            f"{fmt} extracted as empty text. The diff would then be empty and "
            "this gate would report no change on a document that renders "
            "nothing."
        )
        projected[fmt] = text.rstrip("\n") + "\n"
    return projected


# ---------------------------------------------------------------------------
# Fail-closed structural checks
# ---------------------------------------------------------------------------

def test_the_fixture_populates_every_field_the_defects_lived_in():
    """A fixture that stops exercising a field stops guarding it.

    Each assertion here names a defect the baseline exists to catch. If the
    fixture is edited and one of these stops holding, the corresponding class
    goes unwatched while the diff still passes.
    """
    pipeline = _pipeline()
    projects = list(pipeline)

    levels = {p.distress_level for p in projects}
    assert {"deep", "severe"} <= levels, (
        f"the fixture must contain BOTH deep and severe projects (B-1): {levels}"
    )

    units = [p.expected_units_built for p in projects]
    assert None in units, "no project leaves units unsupplied (B-2)"
    assert 0 in units, "no project supplies a genuine zero units (B-2)"
    assert any(u for u in units if u), "no project supplies positive units (B-2)"

    assert _cde().prior_awards, "no prior awards, so no Award Year column (B-3)"
    assert all(len(str(p.census_tract)) == 11 for p in projects), (
        "a census tract is not an 11-digit GEOID; the identifier-column class "
        "would go unexercised (B-3)"
    )


def test_a_baseline_exists_for_every_format():
    """A missing baseline must ERROR, not be created silently on the next run.

    A gate that writes its own expected output the first time it fails is a
    gate that can never fail. Regenerating is a deliberate act — see
    ``test_the_rendered_output_matches_the_reviewed_baseline``'s message.
    """
    assert os.path.isdir(BASELINE_DIR), (
        f"{BASELINE_DIR} does not exist. It is committed on purpose: the "
        "baseline IS the review artifact."
    )
    for fmt in FORMATS:
        path = os.path.join(BASELINE_DIR, f"{fmt}.txt")
        assert os.path.exists(path), f"no committed baseline for {fmt}: {path}"
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        assert len(lines) >= _MIN_BASELINE_LINES[fmt], (
            f"the {fmt} baseline holds {len(lines)} lines, below the "
            f"{_MIN_BASELINE_LINES[fmt]} floor. A truncated baseline is a "
            "diff that compares almost nothing."
        )


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", FORMATS)
def test_the_rendered_output_matches_the_reviewed_baseline(rendered, fmt):
    """Every changed rendered line, in front of a human, in the same commit."""
    path = os.path.join(BASELINE_DIR, f"{fmt}.txt")
    with open(path, encoding="utf-8") as fh:
        expected = fh.read().splitlines()
    actual = rendered[fmt].splitlines()

    diff = list(difflib.unified_diff(
        expected, actual,
        fromfile=f"baseline/{fmt}.txt", tofile=f"rendered/{fmt}.txt",
        lineterm="", n=2,
    ))
    changed = [ln for ln in diff
               if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]

    assert not diff, (
        f"{len(changed)} rendered line(s) changed in the {fmt} output and the "
        "reviewed baseline does not record the change.\n\n"
        "EVERY LINE BELOW IS EITHER AN INTENDED FIX OR A REGRESSION NOBODY "
        "CHOSE. Two consecutive releases shipped a defect created by that "
        "release's own fix — a document stating 0.0% and 40% severe distress, "
        "and prior-award years rendering as 2,019 — and every other gate in "
        "this package stayed green through both, because no gate asks what "
        "CHANGED.\n\n"
        "Read the diff. If the change is intended, regenerate the baseline in "
        "the SAME commit so the rendered change appears in the pull request "
        "as a diff of the document:\n\n"
        "    python -m tests.regen_rendered_baseline\n\n"
        + "\n".join(diff)
    )
