"""FIX-3: the CDFI Fund's distress commitments are measured on QLICIs.

WHAT WENT WRONG

The CY 2024-2025 NMTC Program Review Process, "Targeting Areas of Higher
Distress (Question 25)", states two commitments:

    "at least 85% of its QLICIs in specified areas of severe distress and/or
     areas characterized by multiple indicia of distress"
    "at least 20% of its QLICIs to 'Deep Distress' areas"

Both are shares of QLICIs. Every share this package computes is a share of QEI:
``analyze_distress_concentration`` buckets and divides ``qei_request`` and reads
``qlici_amount`` never. ``qlici_amount`` is a required CSV field that reaches
exactly one rendered figure — the "Total QLICI ($)" column of Appendix A — plus
the QLICI <= QEI consistency rule. It feeds no percentage, no score and no bar.

The arithmetic is inherited from 1.1.5 and is out of scope to change: swapping
the denominator moves every Community Outcomes sub-score and belongs behind a
written methodology (1.2.2). THE CLAIM IS NOT INHERITED. 1.1.5 and 1.2.0 both
rendered "QEI in Deep/Severely Distressed Tracts" — an honest label on an
honest number. 1.2.1's FIX-2 (232df43) rewrote it into a bar assertion without
touching the denominator:

    "QEI in Deep Distress Tracts (the 20% bar's own basis)"
    "<CDE> — measured against the 20% Deep Distress bar:  52.2%"

On a pipeline whose deep-distress projects carry small QLICIs, that files 25.0%
against a bar the CDE misses at 9.5%, in a sentence naming the CDE, on all four
surfaces. It never shipped; it is removed here.

WHY FOUR PASSES MISSED IT

Every fixture in this package sets ``qlici_amount == qei_request`` — both
shipped samples, ``Pipeline.sample()``, the pin fixtures and the rendered
baseline's own fixture. A fixture that collapses two distinct inputs cannot
exercise the distinction, and no gate built on it ever will. ``test_the_two_
denominators_actually_diverge`` below is the first fixture in the package where
they differ, and it exists to keep that true.

THE TWO GATES

1. ``test_section_b_labels_state_their_own_denominator`` and the phrase ban pin
   the corrected text, so it cannot silently revert.

2. ``test_no_rendered_line_compares_a_bar_to_a_share`` is the general rule, and
   it is the one that would have caught FIX-2: a rendered line may state one of
   the Fund's bar percentages only if it also names that bar's denominator on
   the same line. Run against the pre-fix baseline it returns twelve hits, four
   per text format.

   THE SAME RULE OVER SOURCE, because the rendered scan only sees the code
   paths one fixture happens to take. The sweep that produced this commit found
   the identical assertion in four more places, none of them reachable by any
   rendered gate in the package: two recommendation paths that fire on no
   fixture, a validation warning nothing scans, and a Streamlit methodology
   table that needs a Streamlit runtime to render at all.
   ``test_no_source_string_states_a_bar_without_its_denominator`` returns
   thirteen hits across five files on the pre-fix tree. Its limits are stated
   at the test itself and they are real — it is a window scan, and it will not
   replace reading.
"""
from __future__ import annotations

import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.benchmark_thresholds import (
    DEEP_DISTRESS_MIN_PCT, SEVERE_DISTRESS_MIN_PCT,
)
from nmtcapp.intelligence.distress_analysis import analyze_distress_concentration
from nmtcapp.sections.section_b_outcomes import SectionBCommunityOutcomes

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_DIR = os.path.join(_REPO_ROOT, "tests", "rendered_baseline")
FORMATS = ("markdown", "word", "pdf", "excel")


# ---------------------------------------------------------------------------
# Gate 1 — the corrected text, pinned
# ---------------------------------------------------------------------------

#: Substrings that must appear in Section B's distress-commitments table. Each
#: one is a claim the document has to keep making.
REQUIRED_LABEL_TEXT = (
    "QEI in Deep Distress Tracts (a share of QEI, not of QLICIs",
    "QEI in Severely Distressed Tracts, Deep Distress included "
    "(a share of QEI, not of QLICIs",
    "BASIS NOTE — the CDFI Fund's two distress commitments are measured on "
    "QLICIs, not on QEI",
)

#: Clauses the basis note must carry: the denominator mismatch, the numerator
#: mismatch, and the instruction not to present any of it as an answer.
#:
#: 1.3.0 S1 — TWO CLAUSES WERE RETIRED AND FIVE ADDED. "Every share in this
#: table" and "no figure above" were written when the note rendered only inside
#: Section B's two-column table; the workbook now renders the same string with
#: nothing above it and no table around it, so both were re-worded to name the
#: DOCUMENT. That is a wording change. The five additions are the substantive
#: half of this round: the note used to describe the Fund's Question 25 from a
#: seven-page summary of it, and the summary omitted that the 20% is a rung on
#: a ladder and that Question 25(b) has four area types — omissions which
#: instructed a CDE to understate its own qualifying share.
REQUIRED_NOTE_CLAUSES = (
    "both are measured on QLICIs",
    "Every distress share in this document is a share of QEI",
    "computes neither QLICI-denominated figure",
    "no figure in this document answers either commitment",
    "computes no multi-indicia measure at all",
    "The CDE must compute both QLICI-denominated shares",
    # The four corrections, each pinned by the phrase that carries it.
    "in terms of aggregate dollar amounts",
    "at least TWO of items 6-12",
    "selectable commitment level",
    "FOUR qualifying area types",
    "automatically meet the commitment made in Question 25(a)",
    # And the honest half of "say what the tool can see": the list of visible
    # fields may never stand without the sentence that denies it is an answer.
    "is not a partial answer to Question 25",
)

#: Phrases removed by FIX-3. Each asserted, or instructed the reader to make,
#: a comparison between a QEI share and a QLICI bar. None may come back.
BANNED_PHRASES = (
    "bar's own basis",
    "measured against the",
    "Read each against its own row",
    "CDFI Fund threshold for full credit",
    "full-credit threshold",
)

def _scanned_trees():
    """Source trees whose rendered strings reach a CDE.

    ``nmtcapp`` is resolved through the IMPORTED package rather than through
    the repository, so this pin runs identically in a checkout and inside
    release.yml's sdist job, which deliberately has no source tree in its
    working directory. ``streamlit_app`` is included because the 1.2.0 cycle
    found the same sentence live in a second file after it had been deleted
    from the first; the sdist job copies it out of the tarball, so it is
    present there too.

    FAILS CLOSED: a tree that cannot be found is an error, not a skip. A pin
    that quietly scans nothing is the vacuity this package keeps producing.
    """
    import nmtcapp
    trees = [os.path.dirname(os.path.abspath(nmtcapp.__file__))]
    trees.append(os.path.join(_REPO_ROOT, "streamlit_app"))
    for t in trees:
        assert os.path.isdir(t), (
            f"{t} is not a directory — this pin would scan nothing and pass "
            "vacuously"
        )
    return trees


def _application() -> Application:
    cde = CDEProfile(
        name="Basis Test CDE, LLC",
        cde_id="CDE-2018-0311",
        certification_date="2018-03-11",
        mission=(
            "Deploy New Markets Tax Credit capital into distressed census "
            "tracts in western Pennsylvania."
        ),
        target_markets=["Pennsylvania"],
        prior_awards=[
            {"year": 2021, "amount": 40_000_000,
             "deployment_status": "fully_deployed"},
        ],
        contact={
            "name": "R. Alvarez",
            "email": "ralvarez@basistest.example.org",
            "phone": "412-555-0110",
            "title": "Chief Lending Officer",
        },
        governance={
            "board_members": 9,
            "community_representatives": 4,
            "advisory_board_members": 7,
        },
    )
    app = Application(cde=cde, requested_allocation=80_000_000.0,
                      application_round="CY2025")
    app.add_pipeline(_divergent_pipeline())
    return app


def _divergent_pipeline() -> Pipeline:
    """A pipeline whose QLICI shares differ from its QEI shares.

    THE ONLY FIXTURE IN THE PACKAGE WHERE THEY DIVERGE. Equal QEI across eight
    projects; the two deep-distress projects carry QLICIs of 30% of their QEI
    while everything else carries 95%. The QEI deep share clears the Fund's
    20% figure; the QLICI deep share is less than half of it.
    """
    spec = [
        ("PRJ-01", "deep", 10_000_000, 3_000_000),
        ("PRJ-02", "deep", 10_000_000, 3_000_000),
        ("PRJ-03", "severe", 10_000_000, 9_500_000),
        ("PRJ-04", "severe", 10_000_000, 9_500_000),
        ("PRJ-05", "severe", 10_000_000, 9_500_000),
        ("PRJ-06", "severe", 10_000_000, 9_500_000),
        ("PRJ-07", "lic", 10_000_000, 9_500_000),
        ("PRJ-08", "lic", 10_000_000, 9_500_000),
    ]
    pipeline = Pipeline()
    for i, (pid, level, qei, qlici) in enumerate(spec):
        p = PipelineProject(
            project_id=pid,
            project_name=f"Basis Test Project {i + 1}",
            qalicb_name=f"Basis Test Project {i + 1} QALICB, LLC",
            address=f"{100 + i} Main Street",
            city="Erie",
            state="PA",
            sector="healthcare",
            project_type="real_estate",
            total_project_cost=float(qei) * 1.4,
            qei_request=float(qei),
            qlici_amount=float(qlici),
            expected_jobs_created=40 + i,
            expected_jobs_retained=10 + i,
            expected_units_built=0,
            expected_sq_ft=25_000.0,
            closing_target_date=f"2099-{(i % 12) + 1:02d}-15",
            construction_start=f"2099-{(i % 12) + 1:02d}-28",
            operations_start=f"2100-{(i % 12) + 1:02d}-01",
        )
        p.census_tract = f"4204900{i:04d}"
        p.is_nmtc_eligible = True
        p.distress_level = level
        p.is_native_area = False
        p.is_high_migration_rural = False
        p.is_opportunity_zone = False
        p.is_us_territory = False
        p.is_persistent_poverty = False
        p.is_below_market_rate = False
        p.is_unrelated_entity = True
        p.geocode_success = True
        pipeline.add(p)
    # Same reasoning as tests/test_rendered_output_baseline.py: these rows
    # carry verified-shaped data on purpose, so the adapter's pre-enriched
    # branch must not route everything into the degraded banner — the distress
    # sub-scores would then be None and the recommendations this gate reads
    # would never fire.
    pipeline.eligibility_data_status = "ok"
    return pipeline


def test_the_two_denominators_actually_diverge():
    """FAILS CLOSED. If this fixture ever collapses, every gate below is vacuous.

    A fixture that sets qlici_amount == qei_request cannot exercise the
    distinction between the two bases, which is precisely why four consecutive
    passes over this package did not see the defect.
    """
    pipeline = _divergent_pipeline()
    projects = list(pipeline)
    total_qei = sum(p.qei_request for p in projects)
    total_qlici = sum(p.qlici_amount for p in projects)

    assert all(p.qlici_amount != p.qei_request for p in projects), (
        "every project in this fixture must have a QLICI that differs from its "
        "QEI — that is the whole point of it"
    )

    d = analyze_distress_concentration(pipeline)
    deep_qei_share = d["pct_deep"]
    deep_qlici_share = (
        sum(p.qlici_amount for p in projects if p.distress_level == "deep")
        / total_qlici
    )

    assert deep_qei_share >= DEEP_DISTRESS_MIN_PCT, (
        "the QEI share must clear the Fund's 20% figure, so that a document "
        "comparing it to the bar would read as passing"
    )
    assert deep_qlici_share < DEEP_DISTRESS_MIN_PCT / 2, (
        "the QLICI share must miss the Fund's 20% figure by more than half, so "
        "that the comparison is not merely imprecise but wrong"
    )
    assert total_qlici < total_qei, "sanity: QLICIs cannot exceed QEI here"


def test_analyze_distress_concentration_never_reads_qlici_amount():
    """The mechanism, stated as a test rather than as a comment.

    Every share is a share of QEI. Changing that is 1.2.2 work behind a written
    methodology; asserting otherwise in a rendered document is the defect.
    """
    pipeline = _divergent_pipeline()
    before = analyze_distress_concentration(pipeline)

    for p in pipeline:
        p.qlici_amount = p.qei_request  # collapse the field entirely
    after = analyze_distress_concentration(pipeline)

    assert before == after, (
        "a distress share moved when only qlici_amount changed. Either the "
        "denominator was switched to QLICIs — in which case every Community "
        "Outcomes sub-score moved with it and this is 1.2.2 work that needs a "
        "written methodology — or something reads the field by accident."
    )


@pytest.fixture(scope="module")
def section_b_content():
    app = _application()
    return SectionBCommunityOutcomes().generate_content(app, app.analyze())


def _distress_table(content) -> dict:
    for sub in content["subsections"]:
        if sub["heading"] == "Distress Level Commitments":
            assert isinstance(sub["body"], dict), (
                "the distress-commitments subsection stopped being a table; "
                "this pin reads its labels"
            )
            return sub["body"]
    raise AssertionError("Section B has no 'Distress Level Commitments' subsection")


@pytest.mark.parametrize("required", REQUIRED_LABEL_TEXT)
def test_section_b_labels_state_their_own_denominator(section_b_content, required):
    table = _distress_table(section_b_content)
    joined = "\n".join(table)
    assert required in joined, (
        f"Section B's distress-commitments table no longer carries {required!r}.\n"
        "A label that merely stops mentioning the bar leaves a CDE to assume "
        "the number answers it. Name the denominator."
    )


@pytest.mark.parametrize("clause", REQUIRED_NOTE_CLAUSES)
def test_basis_note_states_both_mismatches(section_b_content, clause):
    table = _distress_table(section_b_content)
    note = next((v for k, v in table.items() if k.startswith("BASIS NOTE")), None)
    assert note is not None, "the BASIS NOTE row is gone"
    assert clause in note, (
        f"the basis note no longer says {clause!r}. It has to carry BOTH "
        "mismatches — the denominator (QLICIs, not QEI) and the numerator "
        "(severe distress OR multiple indicia, which this package does not "
        "measure) — and it has to say that no figure above answers the bar."
    )


@pytest.mark.parametrize("phrase", BANNED_PHRASES)
def test_banned_comparison_phrases_are_absent_from_source(phrase):
    """The revert guard, over source rather than over one fixture's output.

    A rendered-output check only sees the code paths the fixture happens to
    take. The recommendation findings that compared a QEI share to a QLICI bar
    were live in ``intelligence/recommendations.py`` and fired on no fixture in
    the package, so no rendered gate had ever seen them.
    """
    hits = []
    scanned = 0
    for root in _scanned_trees():
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                scanned += 1
                with open(path, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        stripped = line.lstrip()
                        if stripped.startswith("#"):
                            continue  # the FIX-3 notes quote what they removed
                        if phrase in line:
                            hits.append(f"{path}:{i}: {line.strip()[:140]}")
    assert scanned > 40, (
        f"only {scanned} source file(s) scanned — the walk is broken and this "
        "pin would pass vacuously"
    )
    assert not hits, (
        f"{phrase!r} is back in a rendered string.\n"
        "FIX-3 removed it because it compares a share of QEI to a bar the CDFI "
        "Fund measures on QLICIs. If the denominator has since been switched to "
        "QLICIs, delete this pin deliberately and say so in the CHANGELOG.\n\n"
        + "\n".join(hits)
    )


# ---------------------------------------------------------------------------
# Gate 2 — the general rule
# ---------------------------------------------------------------------------

#: The Fund's bar percentages as they render. Negative lookbehind so "85.3%"
#: (a computed share that happens to round near a bar) is not mistaken for the
#: bar itself, and a trailing guard so "20%" does not match inside "120%".
_BAR_PCT = re.compile(
    r"(?<![\d.])(?:{})%".format(
        "|".join(sorted({f"{SEVERE_DISTRESS_MIN_PCT:.0%}"[:-1],
                         f"{DEEP_DISTRESS_MIN_PCT:.0%}"[:-1]}))
    )
)

#: A bar percentage alone is not a claim — the fixture's own deep/severe share
#: renders as "85%" on the executive-summary line. It becomes a claim when the
#: line frames it as something to be met.
_BAR_WORDS = ("bar", "threshold", "commitment", "minimum", "full credit",
              "at least", "required", "requirement")

#: The two ways a line earns the right to state a bar: it names the bar's own
#: denominator, or it says on its face that the figure is not a Fund bar at all.
_DENOMINATOR_NAMED = ("qlici",)
_NOT_A_FUND_BAR = ("not a cdfi fund threshold",)

#: THE DISCLAIMER EXEMPTION IS VOID WHEN THE SAME LINE ALSO ASSERTS A FUND BAR,
#: and that is not hypothetical. ``eligibility_check``'s distress warning read
#:
#:     "... is below this tool's internal screening band of 75% (a house
#:      heuristic, not a CDFI Fund threshold — the published CY 2024-2025
#:      severe-distress bar for full credit is 85%)"
#:
#: — an accurate disclaimer about the 75%, and an undenominated Fund bar in the
#: same parenthesis, two clauses after a share of QEI. A line may disclaim one
#: figure and assert another, so the disclaimer alone cannot buy the line out.
_AFFIRMS_A_FUND_BAR = ("published", "for full credit", "required by",
                       "the fund's", "bar is", "commitment is")

#: SOURCE ONLY. Every federal figure in this package is INTERPOLATED rather
#: than typed — that rule is itself a 1.2.1 fix (see the header of
#: intelligence/recommendations.py) — so a source scan keyed on the rendered
#: "85%" sees none of them. `_SEVERE_PCT_TEXT`, `{DEEP_DISTRESS_MIN_PCT:.0%}`
#: and friends are what the bars actually look like in the tree, and three of
#: the five sites FIX-3 found were written that way.
_BAR_TOKENS_IN_SOURCE = (
    "SEVERE_DISTRESS_MIN_PCT", "DEEP_DISTRESS_MIN_PCT",
    "_SEVERE_PCT_TEXT", "_DEEP_PCT_TEXT",
)
#: …but only inside a string. `min(15.0, pct / SEVERE_DISTRESS_MIN_PCT * 15.0)`
#: is arithmetic, not a claim; the scoring proxy is out of FIX-3's scope and is
#: documented in a comment beside itself.
_QUOTE_CHARS = ('"', "'")
_TRIPLE_QUOTES = ('"""', "'''")


def _in_string_literal(line: str, inside_triple: bool) -> bool:
    """Whether ``line``'s text is inside a string literal.

    A quote on the line itself covers the ordinary case. The triple-quote flag
    covers the one that matters most here: the Streamlit pages render whole
    markdown tables out of ``st.markdown(f\"\"\"…\"\"\")``, so the row that states
    a bar carries no quote character of its own. That is where FIX-3 found the
    About & Methodology table.
    """
    return inside_triple or any(q in line for q in _QUOTE_CHARS)


def _toggle_triple(line: str, inside_triple: bool) -> bool:
    for q in _TRIPLE_QUOTES:
        if line.count(q) % 2 == 1:
            return not inside_triple
    return inside_triple


#: Lines the PDF extractor interleaves into a paragraph that are not part of
#: it: the page marker the baseline extractor writes and the running footer
#: ReportLab draws onto the canvas. Neither is prose and neither ends a block.
_PAGE_CHROME = re.compile(r"^(?:@@PAGE \d+|Page \d+|.*\|\s*CONFIDENTIAL)\s*$")


def _context_of(lines, index: int) -> str:
    """The block of consecutive prose lines that ``lines[index]`` sits in.

    THE UNIT OF THIS RULE IS THE PARAGRAPH, NOT THE VISUAL LINE, AND ALWAYS
    HAS BEEN — it was only ever line-scoped by accident. In markdown and Word
    the whole Q25 basis note is ONE line, so "does this line name QLICIs"
    already means "does this paragraph name QLICIs" on three of the four
    surfaces. The PDF matched them until 1.3.0 FIX-2 B1 made its table cells
    wrap; after that the same paragraph arrived as forty short lines and

        25(b)(i) is NOT a 20% bar. It is a selectable

    read as an undenominated bar, with "QLICIs" two lines above it and in the
    reader's eye the whole time. Widening the PDF to the block it was always
    read as does not loosen the rule anywhere: markdown has been block-scoped
    since the note was written.

    WHAT IT DOES NOT DO is join across a blank line. A bar in one paragraph
    cannot be excused by a denominator in the next.

    Example::

        _context_of(["a", "b", "", "c"], 0)   # -> 'a b'
    """
    start = index
    while start > 0 and lines[start - 1].strip() and not _PAGE_CHROME.match(
            lines[start - 1].strip()):
        start -= 1
    end = index
    while end + 1 < len(lines) and lines[end + 1].strip() and not _PAGE_CHROME.match(
            lines[end + 1].strip()):
        end += 1
    return " ".join(lines[start:end + 1])


def _offending_lines(text: str):
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if not _BAR_PCT.search(line):
            continue
        if not any(w in low for w in _BAR_WORDS):
            continue
        context = _context_of(lines, i - 1).lower()
        if any(w in context for w in _DENOMINATOR_NAMED):
            continue
        if (any(w in context for w in _NOT_A_FUND_BAR)
                and not any(w in low for w in _AFFIRMS_A_FUND_BAR)):
            continue
        yield i, line


@pytest.mark.parametrize("fmt", FORMATS)
def test_no_rendered_line_compares_a_bar_to_a_share(fmt):
    """A rendered bar percentage must carry its own denominator.

    THE RULE: a line may state one of the CDFI Fund's distress bars only if the
    same line names what that bar is measured on. Otherwise the reader supplies
    the missing half, and the figure sitting next to it is a share of QEI.

    Run against the baseline at 128436f this returns twelve hits — the four
    Section B rows FIX-2 wrote, in each of the three text formats.
    """
    path = os.path.join(BASELINE_DIR, f"{fmt}.txt")
    assert os.path.exists(path), f"{path} is missing; the baseline gate is broken"
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert len(text.splitlines()) > 100, (
        f"{fmt} baseline is {len(text.splitlines())} lines — too short to be "
        "the real artifact, and this gate would pass vacuously"
    )

    hits = [f"  {fmt}.txt:{i}: {line[:170]}" for i, line in _offending_lines(text)]
    assert not hits, (
        f"{len(hits)} rendered line(s) state a CDFI Fund distress bar without "
        "naming its denominator:\n" + "\n".join(hits) + "\n\n"
        "The Fund's 85% and 20% commitments are shares of QLICIs. Every share "
        "this package computes is a share of QEI. A line that prints the bar "
        "beside a share, or frames a share as meeting one, tells a federal "
        "reader something no figure in this package establishes."
    )


def test_recommendation_findings_state_their_denominator():
    """The surface the rendered baseline cannot reach.

    The baseline fixture scores full credit on both distress sub-scores, so the
    recommendation findings never fire in it. They fired in ``nmtcapp analyze``
    and in ``RecommendationSet.summary()``, and until FIX-3 two of them read
    "Only N% of QEI is ... below the 85% CDFI Fund threshold for full credit"
    and subtracted a QLICI bar from a QEI share to state a gap in percentage
    points.
    """
    app = _application()
    recs = app.recommendations()
    summary = recs.summary()

    # The two distress SUB-SCORE recommendations, keyed on their citations —
    # not on the word "Distress", which also appears in the gating and
    # unassessable-data recommendations whose findings are about something else.
    distress_recs = [
        r for r in recs.recommendations
        if r.citation and r.citation.endswith(
            ("Higher Distress Targeting", "Deep Distress Commitment")
        )
    ]
    assert distress_recs, (
        "no distress recommendation fired on the divergent fixture — this gate "
        "would pass vacuously. Lower the fixture's distress concentration."
    )

    hits = [f"  summary:{i}: {line[:170]}" for i, line in _offending_lines(summary)]
    assert not hits, (
        f"{len(hits)} recommendation line(s) state a CDFI Fund distress bar "
        "without naming its denominator:\n" + "\n".join(hits)
    )

    for r in distress_recs:
        assert "QLICI" in r.finding, (
            "a distress recommendation's finding does not tell the CDE that "
            "the Fund's commitment is measured on QLICIs while this sub-score "
            f"is measured on QEI: {r.finding[:200]!r}"
        )


def test_fallback_recommendations_state_their_denominator():
    """``_pipeline_fallback_recs`` — the path taken when no score is available.

    The surface with the least context around it, and therefore the worst place
    to state a bar wrong. It read "below the CDFI Fund's 85% threshold for full
    Higher Distress Targeting credit" over a share of QEI, and sized the gap by
    subtracting the QLICI bar from that QEI share.
    """
    from nmtcapp.intelligence.recommendations import RecommendationEngine

    result = _application().analyze().pipeline_result
    recs = RecommendationEngine()._pipeline_fallback_recs(result)
    assert recs, (
        "the fallback path produced no recommendations on a fixture that misses "
        "both distress bands — this gate would pass vacuously"
    )
    text = "\n".join(
        f"{r.finding}\n{r.action}\n{r.quantified_improvement}" for r in recs
    )
    hits = [f"  fallback:{i}: {line[:170]}" for i, line in _offending_lines(text)]
    assert not hits, (
        "a fallback recommendation states a CDFI Fund distress bar without "
        "naming its denominator:\n" + "\n".join(hits)
    )


def test_eligibility_check_warning_states_its_denominator():
    """``check_eligibility``'s distress warning, which names the Fund's 85%."""
    from nmtcapp.validation.eligibility_check import check_eligibility

    # The warning fires only BELOW this tool's internal screening band, so the
    # divergent fixture (75% deep-or-severe) does not reach it. Demote the four
    # severe projects to plain LIC to land under the band.
    pipeline = _divergent_pipeline()
    for p in list(pipeline)[2:]:
        p.distress_level = "lic"

    result = check_eligibility(pipeline)
    text = "\n".join(list(result.warnings) + list(result.issues))
    assert "85%" in text, (
        "the eligibility check no longer names the Fund's severe-distress bar "
        "on this fixture — this gate would pass vacuously"
    )
    hits = [f"  eligibility:{i}: {line[:170]}" for i, line in _offending_lines(text)]
    assert not hits, (
        "the eligibility warning states a CDFI Fund distress bar without naming "
        "its denominator:\n" + "\n".join(hits)
    )


def test_no_source_string_states_a_bar_without_its_denominator():
    """The backstop, over source, for surfaces no fixture renders.

    The four sites FIX-3 found outside Section B were each invisible to every
    rendered gate in the package: two recommendation paths that fire on no
    fixture, a validation warning nothing scans, and a Streamlit methodology
    table that needs a Streamlit runtime to render at all.

    THIS IS A WINDOW SCAN AND ITS LIMITS ARE REAL. A rendered sentence is
    usually several source lines of adjacent string literals, so "names its
    denominator" is approximated as "the word QLICI appears within
    ``_WINDOW`` lines". It cannot see across a helper boundary, and it will not
    replace reading. It exists so that a bar written into a new string literal
    has to be argued past a gate rather than noticed by a human four passes
    later.
    """
    _WINDOW = 8
    hits = []
    scanned = 0
    for root in _scanned_trees():
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                scanned += 1
                with open(path, encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
                inside_triple = False
                for i, raw in enumerate(lines):
                    was_inside = inside_triple
                    inside_triple = _toggle_triple(raw, inside_triple)
                    stripped = raw.lstrip()
                    if stripped.startswith("#") and not was_inside:
                        continue  # the FIX-3 notes quote what they removed
                    # The subject is string LITERALS. A trailing comment
                    # annotating a constant is prose about the code, not text
                    # a CDE reads, and matching one produced the only false
                    # positive this scan has had.
                    #
                    # STATED LIMIT: truncating at '#' also truncates a line
                    # that legitimately contains one — a hex colour, or a
                    # markdown heading inside an st.markdown block (which the
                    # leading-'#' rule above already skips outright). Both can
                    # only cause a false NEGATIVE, and neither is a shape this
                    # package states a distress bar in today.
                    line = raw.split("#", 1)[0] if "#" in raw else raw
                    low = line.lower()
                    states_a_bar = bool(_BAR_PCT.search(line)) or (
                        any(t in line for t in _BAR_TOKENS_IN_SOURCE)
                        and _in_string_literal(raw, was_inside)
                    )
                    if not states_a_bar:
                        continue
                    if not any(w in low for w in _BAR_WORDS):
                        continue
                    window = "\n".join(
                        lines[max(0, i - _WINDOW): i + _WINDOW + 1]
                    ).lower()
                    if any(w in window for w in _DENOMINATOR_NAMED):
                        continue
                    if (any(w in window for w in _NOT_A_FUND_BAR)
                            and not any(w in low for w in _AFFIRMS_A_FUND_BAR)):
                        continue
                    hits.append(f"{path}:{i + 1}: {line.strip()[:150]}")
    # THE MISSING HALF. Its sibling above has carried `assert scanned > 40`
    # since 1.2.1; this loop, walking the same two trees for the harder
    # property, had only `assert not hits` — which a walk over zero files
    # satisfies perfectly. A gate that cannot fail is worse than no gate,
    # because it is also a green tick. Fourteen instances of this shape are on
    # record in this package.
    assert scanned > 40, (
        f"only {scanned} source file(s) scanned — the walk is broken and this "
        "pin would pass vacuously"
    )
    assert not hits, (
        f"{len(hits)} source line(s) write a CDFI Fund distress bar into a "
        "string without naming its denominator anywhere nearby:\n"
        + "\n".join(hits) + "\n\n"
        "The Fund's 85% and 20% commitments are shares of QLICIs; every share "
        "this package computes is a share of QEI. Say so on the same surface, "
        "or say that the figure is not a Fund bar at all."
    )


def test_pipeline_analysis_summary_states_its_denominator():
    """The CLI block ``nmtcapp analyze`` prints."""
    app = _application()
    summary = app.analyze().pipeline_result.summary()
    assert "share of pipeline QEI" in summary, (
        "the CLI distress block stopped naming its own denominator"
    )
    hits = [f"  summary:{i}: {line[:170]}" for i, line in _offending_lines(summary)]
    assert not hits, (
        "the CLI summary states a CDFI Fund distress bar without naming its "
        "denominator:\n" + "\n".join(hits)
    )


def test_the_paragraph_widening_cannot_excuse_a_bar_from_the_next_paragraph():
    """The block must stop at a blank line, or the rule stops meaning anything.

    ``_context_of`` was widened in 1.3.0 FIX-2 B1 so a wrapped PDF paragraph is
    read the way markdown has always been read. A widening nobody has seen
    refuse is a widening that could have been "return the whole document".
    """
    same_paragraph = "shares of QLICIs are what is measured\nat least 20% commitment"
    assert not list(_offending_lines(same_paragraph)), (
        "a denominator on the line above did not excuse the bar — the wrapped "
        "paragraph this exists for would still be reported"
    )

    across_a_break = "shares of QLICIs are what is measured\n\nat least 20% commitment"
    assert [ln for _, ln in _offending_lines(across_a_break)] == [
        "at least 20% commitment"
    ], (
        "a denominator in a DIFFERENT paragraph excused a bar. The block must "
        "end at a blank line; otherwise one 'QLICI' anywhere buys the whole "
        "document out and this gate asserts nothing."
    )
