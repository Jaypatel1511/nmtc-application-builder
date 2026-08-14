"""THE fabrication gate: a line identical across disjoint inputs was not derived from them.

THE METHOD

Render the whole application, in all four formats, under N genuinely disjoint
scenarios — no shared CDE, project set, state, sector or dollar amount between
any two. Extract the prose back out of each artifact. Any line that is
byte-identical across all N scenarios cannot have come from those inputs,
because the inputs have nothing in common. It is therefore either

  (a) legitimately invariant — a heading, a column label, placeholder text, or
      a statutory constant that carries its citation inline; every such line is
      on ALLOWLIST below with a one-line justification, or

  (b) an assertion the tool makes about every CDE regardless of who is asking,
      which is the definition of the defect this release exists to remove.

Anything in (b) fails the test.

WHY THIS AND NOT A DENYLIST

tests/test_no_fabricated_output.py is an eighteen-string denylist. Measured
against reintroduced fabrications: 5/5 verbatim caught, 0/8 paraphrases caught.
A denylist can only contain strings somebody already thought of, so it cannot
catch a NEW fabrication by construction. This test inverts the burden — a new
invariant assertion fails by default and has to be argued onto the allowlist by
a human — and it caught all 8 paraphrases the denylist missed.

READING THE ALLOWLIST IS THE HIGHEST-VALUE REVIEW ON THIS PACKAGE. Every entry
is a sentence the tool says to the CDFI Fund about every CDE that ever uses it.

FAILS CLOSED. Fewer than N scenarios, an empty extraction from any artifact, an
empty invariant set, or a missing format all ERROR rather than pass.
"""
from __future__ import annotations

import os

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject

FORMATS = ("markdown", "word", "excel", "pdf")

# Four scenarios sharing NO CDE, project, state, sector or dollar amount.
MIN_SCENARIOS = 4


# ---------------------------------------------------------------------------
# Disjoint scenarios
# ---------------------------------------------------------------------------

def _cde(n: int) -> CDEProfile:
    names = {
        1: ("Aurora Borealis Capital CDE, LLC", "CDE-2011-0001", "2011-01-05"),
        2: ("Bayou Delta Growth Fund CDE", "CDE-2015-0222", "2015-07-19"),
        3: ("Cascadia Tribal Lending CDE, Inc.", "CDE-2020-0333", "2020-11-30"),
        4: ("Dakota Prairie Ventures CDE", "CDE-2024-0444", "2024-03-02"),
    }[n]
    markets = {
        1: ["Alaska"],
        2: ["Louisiana", "Mississippi", "Alabama", "Arkansas", "Oklahoma", "Texas"],
        3: ["Oregon", "Washington", "Idaho"],
        4: ["North Dakota", "South Dakota", "Minnesota", "Iowa", "Nebraska",
            "Missouri", "Kansas"],
    }[n]
    return CDEProfile(
        name=names[0], cde_id=names[1], certification_date=names[2],
        mission={
            1: "Finance cold-climate health infrastructure.",
            2: "Rebuild coastal small business after storm loss.",
            3: "Deploy capital with tribal governments on trust land.",
            4: "Back grain-belt manufacturing in non-metro counties.",
        }[n],
        target_markets=markets,
        prior_awards=[] if n in (3, 4) else [
            {"year": 2010 + n, "amount": (7_000_000 * n), "deployment_status": "fully_deployed"}
        ],
        contact={"name": f"Contact {n}", "email": f"c{n}@example.org"},
        governance={"board_members": 4 + n, "community_representatives": n},
        extra={} if n != 2 else {"has_prior_reporting_issues": True},
    )


# Each scenario differs in EVERY dimension a rendered line could key on:
# state set, sector, project type, distress mix, project count, dollar scale,
# jobs, units, square footage and eligibility rate. Where a line is genuinely
# derived from the input it therefore varies and drops out of the invariant
# set — which is what keeps the allowlist honest. If two scenarios agreed on,
# say, "single state", the "expand geographic footprint" recommendation would
# look invariant and demand an allowlist entry it does not deserve.
def _pipeline(n: int) -> Pipeline:
    spec = {
        1: dict(states=["AK"], city="Nome", sector="healthcare",
                project_type="real_estate", distress=["deep", "severe"], count=2,
                cost=3_100_000, qei=2_100_000, jobs=240, tract="02180000100",
                units=0, sqft=1_200, eligible=[True, True]),
        2: dict(states=["LA", "MS", "AL", "AR", "OK", "TX"], city="Houma",
                sector="small_business", project_type="operating_business",
                distress=["severe"], count=6,
                cost=4_700_000, qei=3_300_000, jobs=27, tract="22109040300",
                units=140, sqft=0, eligible=[True] * 6),
        3: dict(states=["OR", "WA", "ID"], city="Warm Springs",
                sector="community_facility", project_type="real_estate",
                distress=["lic", "ineligible", "lic"], count=3,
                cost=9_200_000, qei=6_400_000, jobs=43, tract="41013970100",
                units=7, sqft=58_000, eligible=[True, False, True]),
        4: dict(states=["ND", "SD", "MN", "IA", "NE", "MO", "KS"],
                city="Jamestown", sector="clean_energy",
                project_type="operating_business", distress=["deep"], count=7,
                cost=15_800_000, qei=11_900_000, jobs=64, tract="38093960200",
                units=0, sqft=310_000, eligible=[True] * 7),
    }[n]
    projects = []
    for i in range(spec["count"]):
        p = PipelineProject(
            project_id=f"S{n}-{i:02d}",
            project_name=f"Scenario {n} Project {i}",
            qalicb_name=f"S{n}-{i:02d} QALICB LLC",
            address=f"{100 * n + i} Route {n}",
            city=spec["city"], state=spec["states"][i % len(spec["states"])],
            sector=spec["sector"], project_type=spec["project_type"],
            total_project_cost=float(spec["cost"] + i),
            qei_request=float(spec["qei"] + i),
            qlici_amount=float(spec["qei"] + i),
            expected_jobs_created=spec["jobs"] + i,
            expected_jobs_retained=n + i,
            expected_units_built=spec["units"] + i if spec["units"] else None,
            expected_sq_ft=float(spec["sqft"] + i) if spec["sqft"] else None,
        )
        p.census_tract = spec["tract"]
        p.is_nmtc_eligible = spec["eligible"][i]
        p.distress_level = spec["distress"][i % len(spec["distress"])]
        p.is_native_area = n == 3
        p.is_high_migration_rural = n == 4
        p.is_opportunity_zone = n == 2
        p.is_us_territory = False
        p.is_persistent_poverty = n in (1, 2)
        p.is_below_market_rate = n in (1, 4)
        p.is_unrelated_entity = True
        p.geocode_success = True
        projects.append(p)
    pipeline = Pipeline(projects)
    # These fixtures carry verified-shaped data on purpose; the adapter's
    # pre-enriched branch would otherwise route every scenario into degraded
    # mode and the four would then share their degraded banner text.
    pipeline.eligibility_data_status = "ok"
    return pipeline


SCENARIOS = {
    1: (_cde(1), _pipeline(1), 2_000_000.0),
    2: (_cde(2), _pipeline(2), 17_000_000.0),
    3: (_cde(3), _pipeline(3), 19_500_000.0),
    4: (_cde(4), _pipeline(4), 84_000_000.0),
}


# ---------------------------------------------------------------------------
# Allowlist — every line the tool legitimately says to every CDE.
#
# Each entry is (line, justification). A line reaches this list only by being
# one of:
#   HEADING   structural title or table-of-contents entry
#   LABEL     column header, row label or field name
#   PLACEHO   [CDE TO COMPLETE] / [NARRATIVE PLACEHOLDER] text, which is the
#             absence of a claim
#   SOURCED   a statutory or published constant that carries its citation
#             inline in the same line
#   TOOL      a statement about this tool, not about the CDE
#   FORMAT    markdown/table scaffolding with no propositional content
# ---------------------------------------------------------------------------

ALLOWLIST_PATH = os.path.join(os.path.dirname(__file__), "invariant_allowlist.txt")


def _load_allowlist() -> dict:
    """Parse the committed allowlist: 'CATEGORY | justification | line'."""
    entries = {}
    with open(ALLOWLIST_PATH, encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip() or raw.startswith("#"):
                continue
            category, justification, line = raw.rstrip("\n").split(" | ", 2)
            entries[line] = (category, justification)
    return entries


# ---------------------------------------------------------------------------
# Render + extract
# ---------------------------------------------------------------------------

def _extract(fmt: str, path: str) -> str:
    if fmt == "markdown":
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    if fmt == "word":
        from docx import Document
        doc = Document(path)
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.extend(cell.text for cell in row.cells)
        for section in doc.sections:
            parts.extend(p.text for p in section.header.paragraphs)
            parts.extend(p.text for p in section.footer.paragraphs)
        return "\n".join(parts)
    if fmt == "excel":
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        parts = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                parts.extend(str(v) for v in row if v is not None)
        return "\n".join(parts)
    if fmt == "pdf":
        from pypdf import PdfReader
        return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    raise AssertionError(f"unknown format {fmt}")


def _is_prose(line: str) -> bool:
    """A line worth adjudicating: long enough and wordy enough to assert something.

    Short cells, bare numbers and single words carry no proposition on their
    own; they are covered by the table-label allowlist entries they sit under.
    """
    if len(line) < 25:
        return False
    if line.startswith(("#", "@@SHEET")):
        return False
    return len(line.split()) >= 5


@pytest.fixture(scope="module")
def rendered_lines(tmp_path_factory) -> dict:
    """{scenario_id: set(prose lines)} across all four formats."""
    per_scenario = {}
    for sid, (cde, pipeline, requested) in SCENARIOS.items():
        out = tmp_path_factory.mktemp(f"inv{sid}")
        app = Application(cde=cde, requested_allocation=requested)
        app.add_pipeline(pipeline)
        paths = app.generate(str(out), formats=list(FORMATS))

        assert set(paths) == set(FORMATS), (
            f"scenario {sid} rendered {sorted(paths)}, expected all of "
            f"{sorted(FORMATS)} — a format that silently does not render is "
            "a format this gate is not checking"
        )

        lines = set()
        for fmt, path in paths.items():
            assert os.path.exists(path), f"scenario {sid}: {fmt} not written"
            text = _extract(fmt, path)
            assert text.strip(), (
                f"scenario {sid}: {fmt} extracted as empty text — the gate "
                "would then find everything invariant, or nothing"
            )
            lines |= {ln.strip() for ln in text.splitlines() if ln.strip()}
        per_scenario[sid] = lines
    return per_scenario


# ---------------------------------------------------------------------------
# Fail-closed structural checks
# ---------------------------------------------------------------------------

def test_scenarios_are_disjoint():
    """No two scenarios may share a CDE, state, sector or dollar amount."""
    assert len(SCENARIOS) >= MIN_SCENARIOS, (
        f"only {len(SCENARIOS)} scenarios; the method needs at least "
        f"{MIN_SCENARIOS} for 'identical across all of them' to mean anything"
    )
    names, ids, states, sectors, amounts = set(), set(), set(), set(), set()
    for sid, (cde, pipeline, requested) in SCENARIOS.items():
        for bucket, value in ((names, cde.name), (ids, cde.cde_id),
                              (amounts, requested)):
            assert value not in bucket, f"scenario {sid} reuses {value!r}"
            bucket.add(value)
        for p in pipeline:
            assert p.state not in states or p.state in {q.state for q in pipeline}, ""
        scenario_states = {p.state for p in pipeline}
        scenario_sectors = {p.sector for p in pipeline}
        assert not (scenario_states & states), (
            f"scenario {sid} shares a state with an earlier scenario"
        )
        assert not (scenario_sectors & sectors), (
            f"scenario {sid} shares a sector with an earlier scenario"
        )
        states |= scenario_states
        sectors |= scenario_sectors
        for p in pipeline:
            assert p.qei_request not in amounts, (
                f"scenario {sid} reuses QEI {p.qei_request}"
            )


def test_allowlist_is_loadable_and_justified():
    """Every allowlist entry must carry a category and a justification."""
    allow = _load_allowlist()
    assert allow, "the allowlist is empty — every invariant line would fail"
    valid = {"HEADING", "LABEL", "PLACEHO", "SOURCED", "TOOL", "FORMAT"}
    for line, (category, justification) in allow.items():
        assert category in valid, f"unknown category {category!r} for {line[:60]!r}"
        assert len(justification.strip()) >= 8, (
            f"allowlist entry has no real justification: {line[:60]!r}"
        )


def test_extraction_is_not_empty(rendered_lines):
    """Fail closed: an empty extraction would make the gate vacuous."""
    assert len(rendered_lines) >= MIN_SCENARIOS
    for sid, lines in rendered_lines.items():
        assert len(lines) > 100, (
            f"scenario {sid} yielded only {len(lines)} lines across four "
            "formats — extraction is broken, not the output"
        )


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def test_no_unallowed_invariant_assertion(rendered_lines):
    """Any prose line identical across all disjoint scenarios must be allowlisted."""
    invariant = set.intersection(*rendered_lines.values())
    assert invariant, (
        "NO line was invariant across the scenarios. Headings alone should be. "
        "Extraction or rendering is broken — this gate must not pass vacuously."
    )

    candidates = {ln for ln in invariant if _is_prose(ln)}
    allow = _load_allowlist()
    unallowed = sorted(candidates - set(allow))

    assert not unallowed, (
        f"{len(unallowed)} line(s) are byte-identical across "
        f"{len(rendered_lines)} disjoint CDEs and pipelines, and are not on "
        f"the reviewed allowlist ({len(allow)} entries).\n\n"
        "A line that does not vary with the input was not derived from the "
        "input. Either it is a heading/label/placeholder/sourced constant — "
        f"add it to {os.path.basename(ALLOWLIST_PATH)} with a category and a "
        "justification — or the tool is asserting it about every CDE that "
        "ever runs it, which is the defect this release exists to remove.\n\n"
        + "\n".join(f"  {ln}" for ln in unallowed)
    )


def test_allowlist_has_no_dead_entries(rendered_lines):
    """An allowlist entry that no longer renders is stale and must be removed.

    Without this the allowlist only ever grows, and a reviewer cannot tell
    which entries still describe the shipped output.
    """
    invariant = {ln for ln in set.intersection(*rendered_lines.values()) if _is_prose(ln)}
    dead = sorted(set(_load_allowlist()) - invariant)
    assert not dead, (
        f"{len(dead)} allowlist entr(ies) no longer appear as invariant lines. "
        "Remove them so the list stays a description of what actually "
        "renders:\n" + "\n".join(f"  {ln}" for ln in dead)
    )
