"""B-3: a figure printed in two places in one document must be one figure.

WHAT SHIPPED IN 1.2.0

Section D reported "Total Leverage Loans ($)" from nmtc-calc, which sizes the
leverage loan as the residual of QEI less investor equity. Appendix A reported
"Leverage Loan ($)" as ``qei * _LEVERAGE_RATIO`` — a flat 80% from a
module-local constant in tables/pipeline_table. Reproduced on the shipped
20-project sample before the fix::

    Appendix A  Leverage Loan ($) total     $98,000,000
    Section D   Total Leverage Loans ($)    $82,846,750
    difference                              $15,153,250

in one generated document, and ``check_consistency`` returned passed=True.

check_consistency existed to catch exactly this. Every assertion in it was
about one project's own fields — QLICI vs QEI, cost vs zero, dates in order —
so it could not see a disagreement that spans two surfaces. A cross-field check
that never crosses a surface cannot fail on the defect that spans two.

THESE TESTS PROVE THE NEW CHECK CAN FAIL. Two of them perturb one site and
assert red; without them the check would be the eleventh gate in this package
that passes because it checks nothing.
"""
from __future__ import annotations

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.validation.consistency_check import (
    _EconomicsOnly, _shared_figures, check_consistency,
    check_cross_surface_agreement,
)


def _project(i: int) -> PipelineProject:
    p = PipelineProject(
        project_id=f"XS-{i:02d}", project_name=f"Cross Surface {i}",
        qalicb_name=f"XS {i} QALICB LLC", address=f"{i} Agreement Way",
        city="Columbus", state="OH", sector="healthcare",
        project_type="real_estate",
        total_project_cost=float(9_000_000 + i),
        qei_request=float(6_000_000 + i),
        qlici_amount=float(6_000_000 + i),
        expected_jobs_created=30 + i, expected_jobs_retained=5,
    )
    p.census_tract = "39049003400"
    p.is_nmtc_eligible = True
    p.distress_level = "deep"
    p.geocode_success = True
    return p


@pytest.fixture()
def application() -> Application:
    cde = CDEProfile(
        name="Cross Surface Test CDE, LLC", cde_id="CDE-2021-0909",
        certification_date="2021-02-02", mission="Fixture.",
        target_markets=["Ohio"], prior_awards=[],
        contact={"name": "XS", "email": "xs@example.org"},
        governance={"board_members": 7, "community_representatives": 3},
    )
    pipeline = Pipeline([_project(i) for i in range(4)])
    pipeline.eligibility_data_status = "ok"
    app = Application(cde=cde, requested_allocation=20_000_000.0)
    app.add_pipeline(pipeline)
    return app


# ---------------------------------------------------------------------------
# The check is not vacuous
# ---------------------------------------------------------------------------

def test_shared_figures_is_not_empty(application):
    """Fail closed: nothing to compare means nothing is being checked.

    THIS ASSERT USED TO BE THE ONLY ONE, AND IT LIVED HERE (1.2.1 S-3). In a
    CDE's hands there is no test file: the shipped validator had no non-empty
    guard at all, so an empty shared-figure set produced issues == [] and
    check_consistency.passed == True. The guard is now inside
    check_cross_surface_agreement, and the two tests below assert the SHIPPED
    behaviour rather than re-asserting this one.
    """
    analysis = application.analyze()
    shared = _shared_figures(application, analysis.deal_economics)
    assert shared, (
        "no figure was found to appear on two surfaces. The check would then "
        "pass on every document, which is the failure mode it exists to close."
    )
    for label, surfaces in shared.items():
        assert len(surfaces) >= 2, f"{label} names only one surface"


def test_an_empty_shared_set_makes_the_SHIPPED_validator_fail(application, monkeypatch):
    """The vacuous path must produce a FAIL, with no test file in the room.

    Reproduced against 1.2.1-rc before the fix::

        _shared_figures -> {}
        issues == []
        check_consistency(...).passed is True

    A gate that cannot fail on its own subject, inside the check that exists
    because the previous one could not fail on a $15.15MM contradiction.
    """
    from nmtcapp.validation import consistency_check as module

    monkeypatch.setattr(module, "_shared_figures", lambda app, econ: {})

    issues = module.check_cross_surface_agreement(
        application, application.analyze().deal_economics
    )
    assert issues, "an empty shared-figure set produced no issue"
    assert "declared figure groups" in issues[0]

    result = module.check_consistency(application)
    assert result.passed is False, (
        "check_consistency PASSED with nothing compared. This is the shipped "
        "code path a CDE runs; there is no test file on their machine."
    )


def test_a_dropped_pair_makes_the_shipped_validator_fail(application, monkeypatch):
    """Losing ONE of the declared groups must fail, not shrink the set.

    The old guard was `len(shared) >= 4` against five pairs, so one could drop
    silently even in CI. The guard is now set equality against the declared
    groups, which has no slack by construction.
    """
    from nmtcapp.validation import consistency_check as module

    real = module._shared_figures

    def _minus_one(app, econ):
        shared = dict(real(app, econ))
        shared.pop("Total leverage loans")
        return shared

    monkeypatch.setattr(module, "_shared_figures", _minus_one)
    issues = module.check_cross_surface_agreement(
        application, application.analyze().deal_economics
    )
    assert issues and "Total leverage loans" in issues[0], issues


def test_a_renamed_column_raises_rather_than_continuing(application, monkeypatch):
    """A missing column means the document changed shape. Say so loudly.

    The 1.2.1-rc code hit a ``continue`` here, quietly dropping the pair out of
    the comparison — the same fail-silent filter that dropped the Native Area
    column out of Word's Appendix A without a word (1.2.1 L-1).
    """
    from nmtcapp.validation import consistency_check as module

    monkeypatch.setattr(
        module, "_APPENDIX_A_TO_SECTION_D",
        dict(module._APPENDIX_A_TO_SECTION_D,
             **{"Total leverage loans": ("Leverage Loan (USD)", "Total Leverage Loans ($)")}),
    )
    issues = module.check_cross_surface_agreement(
        application, application.analyze().deal_economics
    )
    assert issues, "a renamed Appendix A column produced no issue"
    assert "could not run" in issues[0] and "Leverage Loan (USD)" in issues[0], issues


def test_every_money_column_is_paired_or_excused(application):
    """The COVERAGE is derived, even though the pairing is hand-written.

    _assert_pairs_cover_every_money_column requires every currency column
    pipeline_table publishes and every dollar row Section D renders to be
    either compared or listed in _UNPAIRED with a reason. Adding one without
    adjudicating it fails here.
    """
    from nmtcapp.tables.pipeline_table import CURRENCY_COLUMNS
    from nmtcapp.validation.consistency_check import (
        _APPENDIX_A_TO_SECTION_D, _UNPAIRED, _assert_pairs_cover_every_money_column,
    )
    from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy

    assert CURRENCY_COLUMNS, "the pipeline table declares no currency columns"
    analysis = application.analyze()
    economics = SectionDCapitalizationStrategy().generate_content(
        application, _EconomicsOnly(analysis.deal_economics)
    )["subsections"][0]["body"]

    from nmtcapp.tables.pipeline_table import build_pipeline_table
    columns = build_pipeline_table(application.pipeline, application.cde).columns
    _assert_pairs_cover_every_money_column(columns, economics)     # must not raise

    # And it must be able to fail: an unadjudicated money row does.
    import pytest as _pytest
    from nmtcapp.validation.consistency_check import CrossSurfaceCheckError
    with _pytest.raises(CrossSurfaceCheckError, match="neither compares them"):
        _assert_pairs_cover_every_money_column(
            columns, dict(economics, **{"Brand New Money Row ($)": "$1,000,000"})
        )
    assert _UNPAIRED, "no single-surface money figures recorded"
    assert _APPENDIX_A_TO_SECTION_D, "no pairs declared"


def test_the_cross_appendix_totals_are_compared(application):
    """Total QEI in three appendices, Jobs Created in two — none was compared.

    The docstring promised "any figure this document prints in more than one
    place" and the implementation looked at Appendix A against Section D only.
    """
    analysis = application.analyze()
    shared = _shared_figures(application, analysis.deal_economics)
    qei = shared["Total pipeline QEI (across appendices)"]
    assert set(qei) == {
        "Appendix A (pipeline detail)",
        "Appendix C (geographic targeting)",
        "Appendix D (impact projections)",
    }, sorted(qei)
    assert len(set(qei.values())) == 1, f"three appendices, {len(set(qei.values()))} totals: {qei}"

    jobs = shared["Jobs created (across appendices)"]
    assert len(jobs) == 2 and len(set(jobs.values())) == 1, jobs


def test_leverage_is_among_the_shared_figures(application):
    """The specific figure that shipped wrong must be one of the compared ones."""
    analysis = application.analyze()
    shared = _shared_figures(application, analysis.deal_economics)
    assert "Total leverage loans" in shared, sorted(shared)


def test_document_agrees_with_itself(application):
    """The shipped arithmetic must now agree across surfaces."""
    analysis = application.analyze()
    assert check_cross_surface_agreement(application, analysis.deal_economics) == []
    result = check_consistency(application, analysis.deal_economics)
    assert result.passed, result.issues


def test_appendix_a_and_section_d_leverage_are_equal(application):
    """The $15.15MM contradiction, asserted closed by value."""
    analysis = application.analyze()
    shared = _shared_figures(application, analysis.deal_economics)
    a, d = shared["Total leverage loans"].values()
    assert abs(a - d) <= len(list(application.pipeline)), (
        f"Appendix A ${a:,.0f} vs Section D ${d:,.0f}"
    )


# ---------------------------------------------------------------------------
# PROVE IT FAILS. Perturb one site; the check must go red.
# ---------------------------------------------------------------------------

def test_check_fails_when_appendix_a_leverage_is_perturbed(application, monkeypatch):
    """Reintroduce the exact 1.2.0 defect — a flat 80% — and demand red.

    This is the mutation that reproduces what shipped: Appendix A sizing the
    leverage loan from a ratio while Section D takes the structural residual.
    """
    import nmtcapp.tables.pipeline_table as pt
    monkeypatch.setattr(pt, "leverage_loan_for", lambda qei: qei * 0.80)

    analysis = application.analyze()
    issues = check_cross_surface_agreement(application, analysis.deal_economics)
    assert issues, (
        "the cross-surface check passed while Appendix A sized leverage at 80% "
        "of QEI and Section D took QEI less equity — the exact defect that "
        "shipped in 1.2.0. The check cannot fail and is therefore worthless."
    )
    assert any("leverage" in issue.lower() for issue in issues), issues
    assert any("disagrees between surfaces" in issue for issue in issues), issues


def test_check_fails_when_section_d_economics_are_perturbed(application):
    """Perturb the OTHER side: a wrong deal_economics dict must also be caught."""
    analysis = application.analyze()
    tampered = dict(analysis.deal_economics)
    tampered["total_cde_fees"] = tampered["total_cde_fees"] + 1_000_000

    issues = check_cross_surface_agreement(application, tampered)
    assert issues, "a $1MM divergence in CDE fees was not caught"
    assert any("CDE fee" in issue for issue in issues), issues


def test_failed_agreement_fails_the_whole_consistency_check(application, monkeypatch):
    """A disagreement must make check_consistency report passed=False.

    Finding the divergence and then returning a passing ValidationResult would
    reproduce the original defect one layer up.
    """
    import nmtcapp.tables.pipeline_table as pt
    monkeypatch.setattr(pt, "leverage_loan_for", lambda qei: qei * 0.80)

    analysis = application.analyze()
    result = check_consistency(application, analysis.deal_economics)
    assert not result.passed
    assert any("disagrees between surfaces" in issue for issue in result.issues)


def test_check_reports_an_issue_when_it_cannot_run(application):
    """A check that errors must SAY so, not return clean.

    Returning [] on an exception is how a gate stops guarding silently.
    """
    issues = check_cross_surface_agreement(application, deal_economics="not a dict")
    assert issues, "an unusable economics input produced no issue at all"
    assert any("could not run" in i or "disagrees" in i or "could not be read" in i
               for i in issues), issues


# ---------------------------------------------------------------------------
# The shim contract
# ---------------------------------------------------------------------------

def test_section_d_reads_only_deal_economics_off_the_analysis(application):
    """_EconomicsOnly is enough for Section D, and must stay enough.

    check_consistency runs inside Application.analyze(), before the
    ApplicationAnalysis exists, so it hands Section D a shim carrying only
    ``deal_economics``. If Section D ever reads another attribute this test
    fails here rather than raising AttributeError inside a validator on a
    CDE's machine.
    """
    from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy

    analysis = application.analyze()
    shim = _EconomicsOnly(analysis.deal_economics)
    content = SectionDCapitalizationStrategy().generate_content(application, shim)
    assert content["section_id"] == "D"
    assert content["subsections"][0]["body"], "Section D produced no economics table"


def test_analyze_does_not_recurse(application):
    """analyze() -> check_consistency -> analyze() would never terminate."""
    analysis = application.analyze()
    assert analysis is application.analyze()
