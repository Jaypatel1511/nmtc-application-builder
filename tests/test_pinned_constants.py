"""THE CONSTANT GATE: every published constant, asserted as the string it prints.

WHAT THIS CLOSES

tests/test_invariant_output.py is the fabrication gate and it works, but it
collapses every digit run to "N" before intersecting::

    _NUMBER_RE = re.compile(r"\\d[\\d,]*(?:\\.\\d+)?")
    masked = _NUMBER_RE.sub("N", masked)

THE MASK IS CORRECT AND MUST NOT BE WEAKENED. Without it, every dollar figure
varies per scenario, nothing is invariant, and the gate cannot run at all. But
digit masking necessarily erases every constant the document prints, so that
gate is structurally blind to all of them. Measured on the 1.2.0 tree by
mutating the rendered 85%/20% commitment to 55%/5%::

    [baseline 85%/20%]  invariant=207  UNALLOWED=0  DEAD=0
    [mutated  55%/ 5%]  invariant=207  UNALLOWED=0  DEAD=0

Identical. The round-nine swapped distress thresholds mask to the same string
as the correct legend. So do IRC §45D -> §42D, the 7-year compliance period,
$0.83, the ACS vintage, the impact bands and the readiness weights. The
attribution gate normalises digits the same way and its own header concedes
that citations are "recorded, not verified".

So: a separate gate, over values instead of clauses.

THE METHOD

tests/pinned_constants.txt lists, for each published constant that reaches a
rendered surface, the exact literal string that constant must print, the
surfaces it must print on, and its source. This module renders the surfaces and
asserts each string is present.

FOUR RULES, each of which this package has previously violated somewhere:

  1. ASSERT AGAINST THE RENDERED ARTIFACT. Never against the constant. A test
     that reads SEVERE_DISTRESS_MIN_PCT and compares it to itself cannot fail —
     that is the shape of the version guard that read installed metadata, the
     ast.parse().body scan, the ``|| true`` grep swallow and the test doubles
     that defined a dropped dependency field. Every expected string in the pin
     file is a literal, typed by hand, and nothing in this module imports the
     constants it pins.

  2. FAIL CLOSED. An empty pin set errors. A pin whose string no longer renders
     errors (a stale pin is a pin that stopped guarding). A pin with no source
     errors. A HOUSE pin whose disclosure does not co-render errors.

  3. EVERY ENTRY CARRIES A SOURCE, and where one cannot be given the entry says
     HOUSE and the RENDERED TEXT must say so too. That is the attribution
     allowlist's policy, applied to values.

  4. THE LIST IS DERIVED, NOT INHERITED. test_every_consumed_constant_is_pinned
     sweeps nmtcapp/data/{schema,benchmark_thresholds}.py for every module-level
     constant, finds the ones any module outside nmtcapp/data/ references, and
     requires each to be either pinned or explicitly waived with a reason. A
     constant added tomorrow fails this test until somebody adjudicates it.

WHAT A PIN CANNOT DO. A pin proves the string renders. It does not prove the
constant produced it. Where a renderer duplicated a constant as a display
literal, the pin would have passed over a mutated constant — so 1.2.1 removed
the duplications it found rather than pinning around them: win_probability's
"40-point minimum"/"85-point minimum" and excel_builder's weight_map, both of
which printed one value while the package gated on another. If you add a pin,
check the call site interpolates.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject

PIN_PATH = os.path.join(os.path.dirname(__file__), "pinned_constants.txt")

DOCUMENT_SURFACES = ("markdown", "word", "excel", "pdf")
TEXT_SURFACES = ("cli_summary", "win_score")
ALL_SURFACES = DOCUMENT_SURFACES + TEXT_SURFACES

DATA_MODULES = {
    "schema": os.path.join("nmtcapp", "data", "schema.py"),
    "benchmark_thresholds": os.path.join("nmtcapp", "data", "benchmark_thresholds.py"),
}

# A HOUSE pin must render its own disclaimer on the same surface. These are the
# phrases that count; a HOUSE pin whose surface carries none of them fails.
_DISCLOSURE_PHRASES = (
    "not a cdfi fund parameter",
    "this tool's own",
    "unsourced house heuristic",
    "the cdfi fund publishes no",
    "not a cdfi fund threshold",
    "not a federal figure",
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class Pin:
    __slots__ = ("constant", "surfaces", "source", "expected", "lineno")

    def __init__(self, constant, surfaces, source, expected, lineno):
        self.constant = constant
        self.surfaces = surfaces
        self.source = source
        self.expected = expected
        self.lineno = lineno

    @property
    def is_house(self) -> bool:
        return self.source.startswith("HOUSE:")

    def __repr__(self) -> str:
        return f"<Pin {self.constant} @{self.lineno}>"


def _load_registry():
    """Parse tests/pinned_constants.txt into (pins, waivers)."""
    pins, waivers = [], {}
    with open(PIN_PATH, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split(" | ")
            if parts[0].strip() == "WAIVE":
                assert len(parts) == 3, (
                    f"{PIN_PATH}:{lineno}: a WAIVE row is "
                    f"'WAIVE | CONSTANT | reason', got {len(parts)} fields"
                )
                waivers[parts[1].strip()] = parts[2].strip()
                continue
            assert len(parts) == 4, (
                f"{PIN_PATH}:{lineno}: a pin row is "
                f"'CONSTANT | SURFACES | SOURCE | expected', got {len(parts)} fields"
            )
            constant, surfaces, source, expected = (p.strip() for p in parts)
            pins.append(Pin(
                constant=constant,
                surfaces=tuple(s.strip() for s in surfaces.split(",")),
                source=source,
                expected=expected,
                lineno=lineno,
            ))
    return pins, waivers


PINS, WAIVERS = _load_registry()


# ---------------------------------------------------------------------------
# Fixture: one fully-verified application, rendered to every surface.
#
# Deliberately NOT the four disjoint scenarios from test_invariant_output. That
# gate needs disjointness; this one needs the non-degraded path, because half
# the constants below are suppressed when eligibility data is missing or a
# project is unverified — and a gate that silently ran on the degraded path
# would pass while pinning nothing.
# ---------------------------------------------------------------------------

def _fixture_application() -> Application:
    cde = CDEProfile(
        name="Pinned Constants Test CDE, LLC",
        cde_id="CDE-2019-0777",
        certification_date="2019-06-14",
        mission="Fixture profile for the constant-pinning gate.",
        target_markets=["Ohio", "Kentucky", "West Virginia"],
        prior_awards=[{"year": 2019, "amount": 40_000_000,
                       "deployment_status": "fully_deployed"}],
        contact={"name": "Pin Fixture", "email": "pins@example.org"},
        governance={"board_members": 9, "community_representatives": 4},
    )
    projects = []
    for i, (state, tract, level) in enumerate((
        ("OH", "39035103200", "deep"),
        ("KY", "21111010100", "severe"),
        ("WV", "54039000200", "lic"),
        ("OH", "39049003400", "deep"),
    )):
        p = PipelineProject(
            project_id=f"PIN-{i:02d}",
            project_name=f"Pin Fixture Project {i}",
            qalicb_name=f"Pin Fixture {i} QALICB LLC",
            address=f"{100 + i} Pin Street",
            city="Fixtureville",
            state=state,
            sector="healthcare",
            project_type="real_estate",
            total_project_cost=float(9_000_000 + i),
            qei_request=float(6_000_000 + i),
            qlici_amount=float(6_000_000 + i),
            expected_jobs_created=40 + i,
            expected_jobs_retained=10 + i,
            expected_units_built=None,
            expected_sq_ft=float(15_000 + i),
        )
        p.census_tract = tract
        p.is_nmtc_eligible = True
        p.distress_level = level
        p.is_native_area = i == 0
        p.is_high_migration_rural = False
        p.is_opportunity_zone = False
        p.is_us_territory = False
        p.is_persistent_poverty = True
        p.is_below_market_rate = True
        p.is_unrelated_entity = True
        p.geocode_success = True
        projects.append(p)
    pipeline = Pipeline(projects)
    pipeline.eligibility_data_status = "ok"

    app = Application(cde=cde, requested_allocation=24_000_000.0)
    app.add_pipeline(pipeline)
    return app


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


def _normalise(text: str) -> str:
    """Collapse whitespace so a pin survives PDF line wrapping and cell padding.

    Word puts the whole methodology block in one paragraph, ReportLab wraps it
    at the column width, and pypdf reintroduces the wrap as newlines. Comparing
    raw text would make every pin a test of the page width.
    """
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def rendered() -> dict:
    """{surface: normalised text} for all six surfaces."""
    import tempfile
    out = tempfile.mkdtemp(prefix="nmtcapp-pins-")
    app = _fixture_application()
    paths = app.generate(out, formats=list(DOCUMENT_SURFACES))

    assert set(paths) == set(DOCUMENT_SURFACES), (
        f"rendered {sorted(paths)}, expected all of {sorted(DOCUMENT_SURFACES)} — "
        "a format that silently does not render is a format this gate is not "
        "checking, which is exactly how the docs sample-output hook shipped two "
        "of four formats under a --strict build"
    )

    surfaces = {}
    for fmt, path in paths.items():
        text = _extract(fmt, path)
        assert text.strip(), f"{fmt} extracted as empty — the gate would pin nothing"
        surfaces[fmt] = _normalise(text)

    analysis = app.analyze()
    surfaces["cli_summary"] = _normalise(
        analysis.pipeline_result.summary() + "\n" + analysis.readiness_score.summary()
    )
    surfaces["win_score"] = _normalise(app.score_win_probability().summary())

    for name in TEXT_SURFACES:
        assert surfaces[name].strip(), f"{name} rendered empty"
    return surfaces


# ---------------------------------------------------------------------------
# Fail-closed structural checks
# ---------------------------------------------------------------------------

def test_registry_is_not_empty():
    """An empty pin set must ERROR, not pass.

    This is the property every gate in this package has failed at least once:
    the check runs, finds nothing to check, and reports success.
    """
    assert PINS, (
        f"{os.path.basename(PIN_PATH)} contains no pins. An empty registry "
        "would make this gate vacuous — every constant in the package could "
        "change and nothing would turn red."
    )
    assert len(PINS) >= 10, (
        f"only {len(PINS)} pins. The sweep in "
        "test_every_consumed_constant_is_pinned found more constants than that "
        "reaching a rendered surface; a registry this small means rows were "
        "deleted rather than adjudicated."
    )


def test_every_pin_names_a_surface_and_a_source():
    for pin in PINS:
        assert pin.surfaces, f"{pin} names no surface"
        for surface in pin.surfaces:
            assert surface in ALL_SURFACES, (
                f"{pin}: unknown surface {surface!r}; known: {ALL_SURFACES}"
            )
        assert pin.expected, f"{pin} pins an empty string"
        assert len(pin.source) >= 20, (
            f"{pin}: source is {pin.source!r}. Every pin carries a real source "
            "or says HOUSE and explains what the rendered text must admit."
        )
        if pin.is_house:
            assert len(pin.source) > len("HOUSE:") + 20, (
                f"{pin}: a HOUSE pin must state what the rendered text says"
            )
        else:
            assert re.search(r"\d", pin.source), (
                f"{pin}: a cited source must carry a digit — a year, section, "
                f"question or column. 'CDFI Fund guidance' is not a citation. "
                f"Got: {pin.source!r}"
            )


def test_waivers_carry_reasons():
    assert WAIVERS, "no waivers recorded; the sweep found consumed constants"
    for constant, reason in WAIVERS.items():
        assert len(reason) >= 30, (
            f"waiver for {constant} has no real reason: {reason!r}"
        )


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def test_pinned_constants_render_verbatim(rendered):
    """Every pinned constant must appear, as its literal string, on its surface.

    A failure here means one of two things and both are release-blocking:
    the constant changed and the pin was not re-adjudicated, or the constant
    changed and the DOCUMENT is now wrong.
    """
    failures = []
    for pin in PINS:
        for surface in pin.surfaces:
            if pin.expected not in rendered[surface]:
                failures.append(
                    f"  {PIN_PATH}:{pin.lineno}  {pin.constant}\n"
                    f"    surface : {surface}\n"
                    f"    expected: {pin.expected!r}\n"
                    f"    source  : {pin.source[:110]}"
                )
    assert not failures, (
        f"{len(failures)} pinned constant(s) do not render as pinned.\n\n"
        "Either a published constant changed value and the document is now "
        "wrong, or the rendered wording changed and the pin is stale. Both "
        "require a human to look at the source column before touching this "
        "file.\n\n" + "\n".join(failures)
    )


def test_house_pins_carry_their_disclaimer(rendered):
    """A HOUSE value must be disclosed as one, on the surface that prints it.

    Same policy as the attribution allowlist: an entry claiming HOUSE while the
    document reads as a federal figure is the defect, not the fix. 1.1.5
    printed this package's own 50%/75% bands under the labels "CDFI Fund
    Competitive Minimum" and "CDFI Fund Target".
    """
    failures = []
    for pin in PINS:
        if not pin.is_house:
            continue
        for surface in pin.surfaces:
            haystack = rendered[surface].lower()
            if not any(phrase in haystack for phrase in _DISCLOSURE_PHRASES):
                failures.append(
                    f"  {pin.constant} on {surface}: HOUSE value with no "
                    f"disclosure anywhere on that surface"
                )
    assert not failures, (
        "HOUSE-sourced constants render without saying so:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Derivation: the list must not be a list somebody once wrote down
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _module_constants() -> dict:
    """{qualified_name: module} for every module-level UPPER_CASE assignment."""
    found = {}
    root = _repo_root()
    for mod, rel in DATA_MODULES.items():
        path = os.path.join(root, rel)
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in tree.body:
            targets = (
                node.targets if isinstance(node, ast.Assign)
                else [node.target] if isinstance(node, ast.AnnAssign)
                else []
            )
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    found[f"{mod}.{t.id}"] = mod
    return found


def _consumed(constant_name: str) -> list:
    """Modules outside nmtcapp/data/ that reference this constant by name."""
    root = _repo_root()
    bare = constant_name.split(".", 1)[1]
    pattern = re.compile(rf"\b{re.escape(bare)}\b")
    hits = []
    for dirpath, _dirs, files in os.walk(os.path.join(root, "nmtcapp")):
        if os.path.join("nmtcapp", "data") in dirpath:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dirpath, f)
            with open(p, encoding="utf-8") as fh:
                if pattern.search(fh.read()):
                    hits.append(os.path.relpath(p, root))
    return sorted(hits)


def test_every_consumed_constant_is_pinned_or_waived():
    """Sweep the data modules; every consumed constant must be adjudicated.

    THIS IS THE PART THAT KEEPS THE LIST HONEST. The starting list for 1.2.1
    came from the 1.2.0 audit, and an inherited list goes stale the first time
    somebody adds a constant. This test walks nmtcapp/data/ and requires that
    every constant any other module reads is either pinned to a rendered string
    or waived with a stated reason.
    """
    pinned_roots = {p.constant.split("[", 1)[0] for p in PINS}
    pinned_exact = {p.constant for p in PINS}
    waived_roots = {w.split("[", 1)[0] for w in WAIVERS}

    unadjudicated = []
    for name in sorted(_module_constants()):
        if name in pinned_exact or name in pinned_roots or name in WAIVERS:
            continue
        if name in waived_roots:
            continue
        consumers = _consumed(name)
        if consumers:
            unadjudicated.append(f"  {name}  read by: {', '.join(consumers)}")

    assert not unadjudicated, (
        f"{len(unadjudicated)} constant(s) in nmtcapp/data/ are read by other "
        "modules and are neither pinned to a rendered string nor waived with a "
        f"reason in {os.path.basename(PIN_PATH)}.\n\n"
        "Add a pin (with the literal string it prints and its source) or a "
        "WAIVE row saying why it reaches no rendered surface. Do not delete "
        "this test to make it pass.\n\n" + "\n".join(unadjudicated)
    )


def test_no_waiver_shadows_a_live_pin():
    """A constant cannot be both pinned and waived — one of them is a lie."""
    both = sorted({p.constant.split("[", 1)[0] for p in PINS} & set(WAIVERS))
    assert not both, (
        "these constants are both pinned and waived; the waiver claims they "
        f"reach no rendered surface while the pin asserts they do: {both}"
    )
