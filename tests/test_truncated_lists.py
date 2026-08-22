"""A list that is cut must say so, on every surface a CDE reads.

THE DEFECT THIS GATE EXISTS FOR (1.3.1 F1)
==========================================

Four call sites joined the first five items of a list under a sentence that
had already stated the untruncated length::

    f"{len(self.unverified_project_ids)} project(s) could not be "
    "location-verified and remain\\n  UNVERIFIED (no tract assigned): "
    + ", ".join(self.unverified_project_ids[:5])

Executed on an eight-project pipeline with six unverified, the CLI block and
the Streamlit page both read::

    6 project(s) could not be location-verified and remain
    UNVERIFIED (no tract assigned): PRJ-D03, PRJ-D04, PRJ-D05, PRJ-D06, PRJ-D07

No ellipsis, nothing saying the list was partial, and PRJ-D08 absent. The
generated documents name all six. So the screen and the filing disagreed, and
the screen is the one a CDE acts on — the list IS the actionable half, because
it is what says which projects to go and verify.

WHY THIS IS A GATE AND NOT FOUR EDITS
=====================================

The correct pattern was already in this repository, at exactly one call site
(``sections/section_a_business``'s target-states sentence), and four later
call sites did not find it. That is the same shape as the frame constant
1.3.1 G6 unified and the required-field list ``Pipeline.from_csv`` derives:
a rule restated per call site is a rule a call site can forget. It is one
statement now — ``renderers/_disclosure.join_truncated`` — and this file is
what stops the next call site from writing its own.

WHAT IS ASSERTED, AND WHAT IS NOT
=================================

**Asserted.** No source file may slice a list to a literal preview length and
join it, outside the one function that is allowed to. That is a syntactic rule
over the tree, so it covers call sites nobody has run — including ones added
after this file was written.

**Also asserted, behaviourally.** On a pipeline with more unverified projects
than the preview limit, the CLI block, the Streamlit warning and the
eligibility-check warning each say the list is partial.

**Not asserted.** Whether a truncation is *appropriate* — a top-3 strengths
list under no count is fine and is not this defect. The rule is about a cut
list rendered beside its own untruncated length, so the sweep below rules each
site rather than banning slicing.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from nmtcapp.renderers._disclosure import LIST_PREVIEW_LIMIT, join_truncated

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Packages that render to a human — documents, the CLI block, the screens.
_SCANNED = ("nmtcapp", "streamlit_app")

#: The one function allowed to slice a list to the preview length and join it.
#: Every other site must call it.
_AUTHORITY = ("nmtcapp", "renderers", "_disclosure.py")

# ---------------------------------------------------------------------------
# THE SWEEP, RULED SITE BY SITE.
#
# Every `[:N]` in the two scanned packages at 0643296, its surface, and a
# verdict. Sites that ARE this defect were fixed; the rest are recorded here so
# "we looked at two of them" cannot be mistaken for "we looked".
#
#   nmtcapp/sections/section_a_business.py:42   documents   EXEMPLAR — the one
#       call site that already said " and others". Now reads join_truncated so
#       the pattern has one statement rather than one instance.
#   nmtcapp/intelligence/pipeline_analyzer.py:77  CLI block   DEFECT — fixed.
#   streamlit_app/pages/1_Pipeline_Analyzer.py:253  screen    DEFECT — fixed.
#   nmtcapp/validation/eligibility_check.py:43   CLI + screen + docs
#       DEFECT — fixed. "N project(s) lack eligibility data:" then five IDs.
#   nmtcapp/integrations/cdfidata_adapter.py:77  CDE narrative
#       DEFECT — fixed. "deployed across 9 states: IL, OH, MI, IN, WI." reads
#       as a complete list of nine and names five.
#   nmtcapp/validation/readiness_score.py:318/339/376/379  CLI + documents
#       NOT THIS DEFECT. strengths[:3], weaknesses[:3], issues[:1], recs[:5]
#       are rendered under headings ("Top Strengths", "Recommendations") that
#       state no count. A heading that promises nothing cannot be contradicted.
#       They ARE silent truncations and are reported in 1.3.1's user-surface
#       read; making them say "top 3 of 7" is a wording change to a rendered
#       document and belongs in a minor release.
#   nmtcapp/renderers/markdown_builder.py:182   documents
#       NOT THIS DEFECT, same reason — recommendations[:3] under
#       "Recommended Improvements Before Submission:", no count.
#   nmtcapp/integrations/impact_adapter.py:94   internal      NOT RENDERED.
#       Returns the top 3 sectors as data; the caller labels them.
#   nmtcapp/visualization/maps.py:258           chart         NOT THIS DEFECT.
#       A 15-bar chart is a chart, and its axis is visible.
#   nmtcapp/visualization/maps.py:549/551/552   internal      NOT A TRUNCATION.
#       `angles[:1]` closes a radar polygon.
#   nmtcapp/tables/pipeline_table.py:315, nmtcapp/tables/impact_table.py:54,
#   nmtcapp/renderers/pdf_builder.py:242, nmtcapp/sections/section_a_business.py:99
#       CELL/STRING ELISION, ALL FOUR APPEND AN ELLIPSIS. A cut string that
#       shows it was cut is the correct behaviour, not this defect.
#   nmtcapp/core/application.py:62, streamlit_app/pages/1_..._Analyzer.py:287
#       `analyzed_at[:19]` — an ISO timestamp trimmed to seconds. Not a list.
#   nmtcapp/renderers/markdown_builder.py:53    docstring example. Not code.
#   nmtcapp/optimizer/pipeline_optimizer.py:104, nmtcapp/intelligence/
#   benchmarks.py:110   A DIFFERENT AND SHARPER DEFECT, fixed in this round
#       under its own heading: a METHODOLOGY DISCLOSURE cut mid-sentence.
#       benchmarks.py showed 140 of 352 characters with NO ellipsis, dropping
#       "Scores reflect alignment with historical winners, not probability of
#       selection" and "not as a prediction of funding outcomes" — the part
#       that is the disclosure. See test_disclosures_are_not_truncated.
# ---------------------------------------------------------------------------

#: Call sites that slice-and-join and are NOT this defect, each with the reason
#: it was ruled rather than fixed. An exemption is a hole with a reason
#: attached; this is where the reasons live, and adding one is a review event.
# EMPTY SINCE 1.5.2, AND THAT IS A RESULT RATHER THAN AN OVERSIGHT.
#
# The one ruling here was ``markdown_builder``'s ``recommendations[:3]``,
# rendered under "Recommended Improvements Before Submission:" -- a heading
# that stated no count, so a reader could not tell three items from seven. The
# 1.3.1 user-surface read recorded it as a real silent truncation whose fix
# ("top 3 of 7") would change a generated document and therefore belonged in a
# minor release.
#
# 1.5.2 T1 removed the call site instead: the composite's recommendations are
# withdrawn, so markdown joins no sliced list at all and there is nothing left
# to truncate. The exception is retired because the ruling has no subject, NOT
# because the defect was waived -- test_every_ruled_exception_still_exists is
# what forced this edit, which is the gate working.
_RULED_EXCEPTIONS = {}


def _require_source_tree() -> None:
    """Skip where there is no source tree to sweep, and say which one is missing.

    The sdist release job runs the shipped suite from a directory holding only
    the tarball's ``tests/`` and ``streamlit_app/`` — deliberately NOT
    ``nmtcapp/``, because a bare ``nmtcapp/`` in the working directory shadows
    the installed package. Nine of that job's twenty skips are this same class:
    a gate that reads the package SOURCE cannot read it where there is none.

    This is a skip and not a pass. The vacuity floor below is what stops the
    skip becoming the way this gate goes green on a checkout.
    """
    missing = [pkg for pkg in _SCANNED if not os.path.isdir(os.path.join(_ROOT, pkg))]
    if missing:
        pytest.skip(
            f"{', '.join(missing)}/ is not beside tests/ (this is an unpacked "
            "sdist or an installed tree, not a checkout). This sweep reads the "
            "package source; it asks a question about the repository."
        )


def _sources():
    for pkg in _SCANNED:
        for dirpath, dirnames, filenames in os.walk(os.path.join(_ROOT, pkg)):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def _sliced_joins(tree):
    """Yield ``(lineno, source_hint)`` for every ``".".join(<x>[:N])``.

    Parsed rather than grepped, so a docstring example, a comment or a string
    that happens to spell the shape is not a call site. Covers the generator
    form (``join(f(r) for r in xs[:3])``) as well as the direct one.
    """
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "join"):
            continue
        for inner in ast.walk(node):
            if not (isinstance(inner, ast.Subscript)
                    and isinstance(inner.slice, ast.Slice)
                    and inner.slice.upper is not None
                    and isinstance(inner.slice.upper, ast.Constant)
                    and isinstance(inner.slice.upper.value, int)):
                continue
            target = inner.value
            while isinstance(target, ast.Attribute):
                target = target.value
            name = getattr(inner.value, "attr", None) or getattr(target, "id", "?")
            yield node.lineno, name


def test_no_surface_joins_a_sliced_list_of_its_own():
    """Only ``join_truncated`` may cut a list for display."""
    _require_source_tree()
    offenders = []
    scanned = 0
    for path in _sources():
        rel = os.path.relpath(path, _ROOT).replace(os.sep, "/")
        if rel == "/".join(_AUTHORITY):
            continue
        scanned += 1
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=rel)
        for lineno, name in _sliced_joins(tree):
            if (rel, name) in _RULED_EXCEPTIONS:
                continue
            offenders.append(f"{rel}:{lineno}  joins a sliced `{name}`")

    assert scanned > 40, (
        f"only {scanned} source file(s) walked — the sweep is broken and this "
        "gate would pass vacuously"
    )
    assert not offenders, (
        f"{len(offenders)} call site(s) join a list they sliced themselves. A "
        "cut list rendered beside its own untruncated count reads as complete, "
        "and the item that falls off is the one the reader would have acted "
        "on (1.3.1 F1). Call renderers._disclosure.join_truncated instead — it "
        "appends ' and others', which is the wording Section A has rendered "
        "since 1.1.x. If the site is genuinely not this defect, rule it in "
        "_RULED_EXCEPTIONS with the reason.\n  " + "\n  ".join(offenders)
    )


def test_the_sweep_would_see_the_defect_it_was_written_for():
    """SENSITIVITY. The shipped 1.3.0 call site, parsed, must be flagged."""
    shipped = (
        "def summary(self):\n"
        "    return ('  UNVERIFIED (no tract assigned): '\n"
        "            + ', '.join(self.unverified_project_ids[:5]))\n"
    )
    found = list(_sliced_joins(ast.parse(shipped)))
    assert found, "the sweep does not see the exact call site it was written for"
    assert found[0][1] == "unverified_project_ids", found

    generator_form = "x = ', '.join(f'- {r}' for r in score.recommendations[:3])\n"
    assert list(_sliced_joins(ast.parse(generator_form))), (
        "the sweep misses the generator form, which is how two of the five "
        "shipped sites are written"
    )

    fixed = "x = join_truncated(self.unverified_project_ids)\n"
    assert not list(_sliced_joins(ast.parse(fixed))), (
        "the sweep flags the CORRECTED form — it would fail on the fix"
    )


def test_every_ruled_exception_still_exists():
    """A ruling for a call site that is gone is a hole nobody is holding open."""
    _require_source_tree()
    stale = []
    for (rel, name), _reason in _RULED_EXCEPTIONS.items():
        path = os.path.join(_ROOT, *rel.split("/"))
        if not os.path.exists(path):
            stale.append(f"{rel} no longer exists")
            continue
        with open(path, encoding="utf-8") as fh:
            names = {n for _ln, n in _sliced_joins(ast.parse(fh.read()))}
        if name not in names:
            stale.append(f"{rel} no longer joins a sliced `{name}`")
    assert not stale, (
        "ruled exception(s) no longer describe the tree. Remove them so the "
        "list stays a description of what is actually exempt:\n  "
        + "\n  ".join(stale)
    )


def test_join_truncated_says_so_only_when_it_cuts():
    """The helper's own two branches, both exercised."""
    short = [f"P{i}" for i in range(LIST_PREVIEW_LIMIT)]
    assert join_truncated(short) == ", ".join(short)
    assert "and others" not in join_truncated(short)

    long = [f"P{i}" for i in range(LIST_PREVIEW_LIMIT + 1)]
    out = join_truncated(long)
    assert out.endswith(" and others")
    assert long[LIST_PREVIEW_LIMIT] not in out, (
        "the helper showed an item past the preview limit — the limit is not "
        "being applied and this gate would pass on an unbounded list"
    )
    assert join_truncated([]) == ""


def _pipeline_with_unverified(n_projects: int, n_unverified: int):
    from nmtcapp.core.pipeline import Pipeline, PipelineProject

    projects = []
    for i in range(n_projects):
        p = PipelineProject(
            project_id=f"PRJ-D{i:02d}", project_name=f"Project {i}",
            qalicb_name=f"Project {i} QALICB, LLC", address=f"{100 + i} Main Street",
            city="Cleveland", state="OH", sector="healthcare",
            project_type="real_estate", total_project_cost=10_000_000.0,
            qei_request=7_000_000.0, qlici_amount=7_000_000.0,
            expected_jobs_created=40, expected_jobs_retained=10,
            expected_units_built=0, expected_sq_ft=20_000,
            closing_target_date="2099-01-15", construction_start="2099-01-28",
            operations_start="2100-01-01",
        )
        verified = i < (n_projects - n_unverified)
        p.census_tract = "39035112100" if verified else None
        p.is_nmtc_eligible = True if verified else None
        p.distress_level = "severe" if verified else None
        p.geocode_success = verified
        projects.append(p)
    pipeline = Pipeline(projects)
    pipeline.eligibility_data_status = "ok"
    return pipeline


@pytest.fixture(scope="module")
def partial_result():
    """A pipeline analysis with MORE unverified projects than the preview limit."""
    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile

    n_unverified = LIST_PREVIEW_LIMIT + 1
    pipeline = _pipeline_with_unverified(n_unverified + 2, n_unverified)
    app = Application(cde=CDEProfile.sample(), requested_allocation=50_000_000.0)
    app.add_pipeline(pipeline)
    result = app.analyze().pipeline_result
    # Stated rather than inferred: `analyze()` runs enrichment, which assigns
    # tracts to the very projects this fixture needs to be unverified. What is
    # under test is the RENDERING of a partial list, not the geocoder.
    result.eligibility_data_status = "ok"
    result.unverified_project_ids = [f"PRJ-D{i:02d}" for i in range(n_unverified)]
    assert len(result.unverified_project_ids) > LIST_PREVIEW_LIMIT, (
        "the fixture did not produce more unverified projects than the preview "
        "limit, so nothing here would be truncated and the gate is vacuous"
    )
    return result


def test_the_cli_block_says_its_unverified_list_is_partial(partial_result):
    """The block ``nmtcapp analyze`` prints, on the pipeline that truncates."""
    block = partial_result.summary()
    _assert_partial(block, partial_result, "the `nmtcapp analyze` block")


def test_the_eligibility_warning_says_its_list_is_partial():
    """The validation warning, which reaches the CLI, the screens and the docs."""
    from nmtcapp.validation.eligibility_check import check_eligibility

    n = LIST_PREVIEW_LIMIT + 1
    pipeline = _pipeline_with_unverified(n, n)
    result = check_eligibility(pipeline)
    warnings = [w for w in result.warnings if "lack eligibility data" in w]
    assert warnings, (
        "no 'lack eligibility data' warning was produced on a pipeline where "
        "nothing is enriched — the fixture stopped reaching the code path"
    )
    text = warnings[0]
    assert "and others" in text, (
        "the eligibility warning names a count and then a cut list with "
        "nothing saying it is cut:\n  " + text
    )


def _assert_partial(text: str, result, what: str) -> None:
    ids = list(result.unverified_project_ids)
    assert str(len(ids)) in text, f"{what} does not state the count at all"
    shown = [i for i in ids if i in text]
    assert shown, f"{what} names none of the unverified projects"
    if len(shown) < len(ids):
        assert "and others" in text, (
            f"{what} states {len(ids)} unverified project(s) and then names "
            f"{len(shown)} of them, with nothing saying the list is partial. "
            "The project that falls off reads as verified (1.3.1 F1).\n\n"
            + text[:800]
        )


# ---------------------------------------------------------------------------
# A DISCLOSURE MAY NOT BE CUT — a sharper case than F1, found in its sweep
# ---------------------------------------------------------------------------

#: Every module-level disclosure string this package prints to a human, with
#: the clause that must survive to the surface. The clause is the part a
#: truncation drops, because a disclosure puts its credential first and its
#: limitation last, and a prefix cut keeps the credential.
_DISCLOSURES = (
    # Reworded in 1.5.0 S3 with the disclosure itself. The clause still names
    # the LAST thing a prefix cut would drop, and the new wording carries one
    # more denial than the old: the bands are not a percentile either, which is
    # what the deleted percentile_vs_winners used to imply they were.
    ("nmtcapp.intelligence.benchmarks", "_METHODOLOGY",
     "NOT a prediction of any funding outcome"),
    ("nmtcapp.optimizer.pipeline_optimizer", "_METHODOLOGY",
     "Alignment score ≠ win probability"),
)


@pytest.mark.parametrize("module,const,tail", _DISCLOSURES,
                         ids=[m.rsplit(".", 1)[-1] for m, _c, _t in _DISCLOSURES])
def test_a_disclosure_reaches_the_surface_whole(module, const, tail):
    """Wrapping a disclosure is a display decision; cutting it is a claim.

    ``benchmarks.BenchmarkResult.summary`` printed 140 characters of a
    352-character disclosure with no ellipsis, under the heading
    ``Methodology:``. What survived read as a credential — "patterns observed
    in CDFI Fund NMTC award announcements" — and what was cut was every clause
    saying the score is not a forecast. ``OptimizationResult.summary`` cut the
    same class at 120 characters and lost "Alignment score != win probability".

    The tail clause is what this asserts, because the tail is what a prefix cut
    takes.
    """
    import importlib

    from nmtcapp.renderers._disclosure import wrap_disclosure

    text = getattr(importlib.import_module(module), const)
    assert tail in text, (
        f"{module}.{const} no longer contains {tail!r}. If the disclosure was "
        "reworded, reword this pin — do not delete it; the clause it names is "
        "the one a truncation drops."
    )
    rendered = "\n".join(wrap_disclosure(text))
    flat = " ".join(rendered.split())
    assert tail in flat, (
        f"{module}.{const} does not reach the rendered surface whole. The "
        f"clause {tail!r} was lost between the constant and the screen, which "
        "is what a truncated disclosure does."
    )
    assert " ".join(text.split()) == flat, (
        "the rendered disclosure is not the disclosure. Wrapping may change "
        "where the lines break and nothing else."
    )


def test_wrap_disclosure_loses_nothing_at_any_width():
    """SENSITIVITY, inverted: prove the replacement cannot do what it replaced."""
    from nmtcapp.renderers._disclosure import wrap_disclosure

    text = ("Scores reflect alignment with historical winners, not probability "
            "of selection. Use as diagnostic guidance only.")
    for width in (20, 40, 68, 200):
        joined = " ".join(" ".join(wrap_disclosure(text, width=width)).split())
        assert joined == " ".join(text.split()), (
            f"wrap_disclosure lost text at width={width}"
        )
    # And the shape it replaced would have failed this, which is the point.
    assert " ".join(text[:60].split()) != " ".join(text.split())
