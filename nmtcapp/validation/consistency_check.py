"""Cross-field consistency validation for NMTC applications."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from nmtcapp.data.schema import ValidationResult

if TYPE_CHECKING:
    from nmtcapp.core.application import Application

logger = logging.getLogger(__name__)

# Rough cost-per-sq-ft bounds by project type for sanity checking
_COST_PER_SQFT_BOUNDS = {
    "real_estate":        (50,   600),   # $50–$600/sq ft
    "operating_business": (0,    100),   # lower capital intensity
    "mixed_use":          (100,  600),
}

# QEI as fraction of total project cost — typical NMTC range
_QEI_COVERAGE_BOUNDS = (0.30, 0.95)


def check_consistency(application: "Application",
                      deal_economics: dict = None) -> ValidationResult:
    """Validate cross-field consistency within and across projects.

    Checks:
    - QLICI amount ≤ QEI for each project (hard NMTC program rule)
    - Total project cost > 0 for all projects
    - Expected jobs ≥ 0
    - QEI as fraction of total cost within reasonable bounds
    - Construction start before operations start (when both provided)
    - Total pipeline QEI vs requested allocation
    - CROSS-SURFACE AGREEMENT: any figure this document prints in more than one
      place must be one figure (see check_cross_surface_agreement)

    ``deal_economics`` is passed by Application.analyze(), which holds it before
    the ApplicationAnalysis exists. Omit it and the cross-surface check will
    run analyze() itself.

    Example::

        result = check_consistency(application)
        print(result.summary())
    """
    issues: list = []
    warnings: list = []

    projects = list(application.pipeline) if application.pipeline else []
    if not projects:
        warnings.append("No projects to validate — add pipeline projects")
        return ValidationResult("consistency_check", True, issues, warnings)

    for p in projects:
        pid = p.project_id

        # QLICI must not exceed QEI — CDFI Fund hard rule.
        #
        # RULED: NOT-CHECKABLE, REPORTED. NOT SKIPPED (1.3.0 S3).
        #
        # When core/upload_handler defaulted qlici_amount to qei_request this
        # comparison was `x > x` — a check that could not fail, on an input
        # nobody had supplied. Two remedies were available and only one of them
        # is consistent with the rest of this file.
        #
        # REJECTED — skip it silently. It turns a trivially-passing check into
        # an invisibly-absent one, which is the same defect one level down and
        # strictly harder to see: ValidationResult.passed stays True either
        # way, and a reader of the validation report cannot tell "checked and
        # passed" from "not checked at all". This module already refuses that
        # shape twice over — CrossSurfaceCheckError is RAISED rather than
        # returned precisely so a comparison that cannot ask its question stops
        # being mistaken for one that asked and got yes, and the pin in
        # tests/test_qlici_basis.py carries the rule in one line: a gate that
        # cannot fail is worse than no gate, because it is also a green tick.
        # Fourteen instances of it are on record in this package.
        #
        # CHOSEN — say so, as a warning, naming the project. The check is a
        # WARNING and not an ISSUE because nothing is known to be wrong: the
        # CDE has not failed the Fund's rule, the CDE has not been asked. It
        # reads on the same surface as the result it replaces, which is the
        # only place the absence is legible.
        if not p.qlici_amount_supplied:
            warnings.append(
                f"Project {pid}: QLICI <= QEI NOT CHECKED — no qlici_amount was "
                f"supplied for this project, so the tool has nothing to compare "
                f"against its QEI of ${p.qei_request:,.0f}. Supply a "
                f"qlici_amount column and re-run before filing."
            )
        elif p.qlici_amount > p.qei_request:
            issues.append(
                f"Project {pid}: QLICI amount (${p.qlici_amount:,.0f}) exceeds "
                f"QEI (${p.qei_request:,.0f}) — not permitted"
            )

        # QEI as fraction of total cost
        if p.total_project_cost > 0:
            coverage = p.qei_request / p.total_project_cost
            lo, hi = _QEI_COVERAGE_BOUNDS
            if coverage < lo:
                warnings.append(
                    f"Project {pid}: QEI ({coverage:.0%} of project cost) seems low — "
                    f"typical NMTC deals are {lo:.0%}–{hi:.0%}"
                )
            elif coverage > hi:
                warnings.append(
                    f"Project {pid}: QEI ({coverage:.0%} of project cost) is very high — "
                    f"review leverage structure"
                )
        else:
            issues.append(f"Project {pid}: total_project_cost must be > 0")

        # Jobs must be non-negative
        if p.expected_jobs_created < 0:
            issues.append(f"Project {pid}: expected_jobs_created must be ≥ 0")
        if p.expected_jobs_retained < 0:
            issues.append(f"Project {pid}: expected_jobs_retained must be ≥ 0")

        # Date consistency
        if p.construction_start and p.operations_start:
            if p.construction_start > p.operations_start:
                warnings.append(
                    f"Project {pid}: construction_start ({p.construction_start}) "
                    f"is after operations_start ({p.operations_start})"
                )

        # Geographic claim consistency — if enriched and state doesn't match
        if p.census_tract and len(p.census_tract) >= 2:
            # FIPS prefix: first 2 digits of tract = state FIPS
            # We do a basic state FIPS check for a few states
            state_fips = _STATE_FIPS.get(p.state.upper())
            if state_fips and not p.census_tract.startswith(state_fips):
                warnings.append(
                    f"Project {pid}: census tract {p.census_tract} may not match "
                    f"state {p.state} (expected FIPS prefix {state_fips})"
                )

    # Pipeline QEI sum vs allocation
    total_qei = sum(p.qei_request for p in projects)
    requested = application.requested_allocation
    if requested > 0 and total_qei > 0:
        ratio = total_qei / requested
        if ratio < 1.0:
            warnings.append(
                f"Total pipeline QEI (${total_qei:,.0f}) is below the requested "
                f"allocation (${requested:,.0f}) — pipeline undersized"
            )

    issues.extend(check_cross_surface_agreement(application, deal_economics))

    passed = len(issues) == 0
    return ValidationResult("consistency_check", passed, issues, warnings)


# ---------------------------------------------------------------------------
# Cross-surface arithmetic
# ---------------------------------------------------------------------------

# Tolerance in dollars. The renderers round to whole dollars at several points
# and the per-project sum in Appendix A rounds differently from the pipeline
# total in Section D, so exact equality would fail on float noise alone. One
# dollar per project is the largest divergence rounding can produce; anything
# above it is a different formula, not a different rounding.
_AGREEMENT_TOLERANCE_PER_PROJECT = 1.0
_AGREEMENT_TOLERANCE_FLOOR = 1.0

# RATES ARE NOT DOLLARS (FIX-2 G-3). The two constants above are a per-project
# rounding allowance in DOLLARS. A credit price is ~0.83 and a fee rate ~2.5,
# so a $1 tolerance is larger than the whole quantity and any disagreement
# whatsoever passes: $0.83 against $0.95 differs by 0.12 and clears nothing.
# Rates must match to the precision the document prints them at — two decimal
# places for the credit price, one for the fee — so the allowance is half a
# unit in the last printed place of the coarser of the two.
_RATE_AGREEMENT_TOLERANCE = 0.005


class _EconomicsOnly:
    """The slice of ApplicationAnalysis that Section D reads.

    check_consistency runs INSIDE Application.analyze(), before the
    ApplicationAnalysis object exists, so this check cannot call analyze() —
    that recurses forever. Section D's generate_content touches exactly one
    attribute of the analysis (``deal_economics``); everything else it needs is
    on the Application. tests/validation/test_consistency_check.py asserts that
    remains true, so a future Section D that reads another attribute fails a
    test rather than an AttributeError in a validator.
    """

    __slots__ = ("deal_economics",)

    def __init__(self, deal_economics: dict) -> None:
        self.deal_economics = deal_economics


class CrossSurfaceCheckError(RuntimeError):
    """The cross-surface check could not ask its question.

    Raised — not returned, not logged — when a column or row the check is
    supposed to compare has gone missing from the renderer that produces it.
    A missing column means the DOCUMENT CHANGED SHAPE, and a shape change is
    precisely when two surfaces are most likely to have stopped agreeing.
    """


# Appendix A column -> Section D row label, for the figures both print.
#
# HAND-WRITTEN, AND SAID SO. Through 1.2.1-rc the docstring above this map read
# "DERIVED FROM THE RENDERERS, NOT HAND-LISTED", which was true of the VALUES
# and false of the map: the values are read out of the two renderers by calling
# them, the pairing was typed here. A false claim about a gate, inside the
# gate, is the thing this release exists to stop, so the claim is corrected
# rather than the map quietly left.
#
# What CANNOT be derived is the pairing itself: "QEI Request ($)" and "Total
# Pipeline QEI ($)" are the same figure under two names a human chose, and no
# string comparison recovers that. What CAN be derived, and now is, is the
# COVERAGE: _assert_pairs_cover_every_money_column below requires every
# currency column pipeline_table publishes and every dollar row Section D
# renders to be either paired here or listed in _UNPAIRED with a reason. A new
# money column therefore fails this check on the day it is added, instead of
# being silently uncompared — which is what the original claim was reaching for.
_APPENDIX_A_TO_SECTION_D = {
    "Total pipeline QEI": ("QEI Request ($)", "Total Pipeline QEI ($)"),
    "Total NMTCs generated": ("Total NMTCs ($)", "Total NMTCs Generated ($)"),
    "Estimated investor equity": (
        "Estimated Investor Equity ($)", "Estimated Investor Equity ($)"),
    "CDE fee income": ("CDE Fee ($)", "CDE Fee Income ($)"),
    "Total leverage loans": ("Leverage Loan ($)", "Total Leverage Loans ($)"),
}

# Money figures that genuinely appear on ONE surface only, with the reason.
# Listed rather than omitted: an unexplained omission and an oversight look
# identical six months later.
_UNPAIRED = {
    "Total Project Cost ($)":
        "the QALICB's total development cost, which Section D does not restate "
        "— Section D is about the NMTC capital stack, not the project budget",
    "Total QLICI ($)":
        "the CDE's QLICI total, printed whole in Appendix A since 1.2.1 WHEN "
        "THE CDE SUPPLIED IT and as 'not supplied [CDE TO COMPLETE]' when it "
        "did not (1.3.0 S3 — this reason said 'own supplied' while an upload "
        "missing the column silently got its QEI copied in). Section D reports "
        "the QEI and its uses, not the QLICI",
    "Allocation Requested ($)":
        "the cover-page ask. It is deliberately NOT the pipeline QEI — the two "
        "were rendered under one label through 1.2.0 and are now separate rows "
        "— so pairing it with an Appendix A total would re-assert the defect "
        "that separation fixed",
    "QEI Less CDE Fees ($)":
        "a Section D-only derivation (QEI minus the CDE fee). Appendix A prints "
        "both inputs and never their difference",
}

# ---------------------------------------------------------------------------
# RATES, WHICH _UNPAIRED USED TO EXCUSE (FIX-2 G-3)
#
# "Assumed Credit Price ($/NMTC)" sat in _UNPAIRED above with the reason "a
# per-credit rate, not a pipeline total; it is a model assumption and carries
# its own disclaimer in the cell". Every clause of that is true and none of it
# is a reason not to compare it. A rate is not a pipeline total, so it does
# not belong in the Appendix-A-to-Section-D map — but it IS printed twice, in
# Section D's economics table and again in the methodology appendix every
# renderer emits, and those two are what have to agree.
#
# Measured on the branch head (probe N1): setting renderers/_methodology's
# credit price to a literal 0.95 produced ONE FILING SAYING $0.83 IN SECTION D
# AND $0.95 IN THE METHODOLOGY APPENDIX, with the whole suite green — the
# registry pin passed because it asks only whether "$0.83" appears somewhere
# on the surface, and this check passed because the figure was excused here.
#
# The registry states the correct rule and applied it to all nine distress
# rows: a pin must be anchored, not merely present. This is that rule applied
# to the rates.
#
# (label, Section D row, regex over the methodology text)
_SECTION_D_TO_METHODOLOGY = {
    "Assumed credit price": (
        "Assumed Credit Price ($/NMTC)",
        r"credit price \$([\d.]+)/credit",
    ),
    "Assumed CDE fee rate": (
        "Assumed CDE Fee Rate",
        r"CDE fee ([\d.]+)% of QEI",
    ),
}

# Figures printed in more than one APPENDIX, which the 1.2.1-rc check did not
# look at at all: its docstring promised "any figure this document prints in
# more than one place" and its map covered Appendix A against Section D only.
# Total QEI is printed in three appendices and Section D; Jobs Created in two.
#
# (table builder, totals-row selector, column) per surface.
_APPENDIX_TOTALS = {
    "Total pipeline QEI (across appendices)": (
        ("Appendix A (pipeline detail)", "pipeline", "QEI Request ($)"),
        ("Appendix C (geographic targeting)", "geographic", "QEI ($)"),
        ("Appendix D (impact projections)", "impact", "QEI ($)"),
    ),
    "Jobs created (across appendices)": (
        ("Appendix A (pipeline detail)", "pipeline", "Jobs Created"),
        ("Appendix D (impact projections)", "impact", "Jobs Created"),
    ),
}


def _assert_pairs_cover_every_money_column(appendix_a_columns, section_d_rows) -> None:
    """Every dollar figure on either surface is paired here or excused here.

    THIS IS WHAT MAKES THE MAP ABOVE HONEST. Without it, adding a money column
    to Appendix A or a dollar row to Section D adds a figure the document
    prints and this check does not look at, and nothing says so.
    """
    from nmtcapp.tables.pipeline_table import CURRENCY_COLUMNS

    paired_a = {a for a, _d in _APPENDIX_A_TO_SECTION_D.values()}
    paired_d = {d for _a, d in _APPENDIX_A_TO_SECTION_D.values()}

    # CURRENCY_COLUMNS is the pipeline table's own declaration of which of its
    # columns hold money. It was declared in 1.2.1 with the comment "Named here
    # rather than retyped there so a column rename cannot silently drop a
    # figure out of the check" — and then imported by nobody, while this module
    # retyped the same names. Reading it is what that comment described.
    missing_a = [
        c for c in CURRENCY_COLUMNS
        if c not in paired_a and c not in _UNPAIRED
    ]
    missing_d = [
        r for r in section_d_rows
        if r.endswith("($)") and r not in paired_d and r not in _UNPAIRED
    ]
    stale_a = [c for c in paired_a if c not in appendix_a_columns]
    stale_d = [r for r in paired_d if r not in section_d_rows]

    problems = []
    if missing_a:
        problems.append(
            f"Appendix A publishes {missing_a} as money columns "
            "(pipeline_table.CURRENCY_COLUMNS) and this check neither compares "
            "them nor excuses them in _UNPAIRED"
        )
    if missing_d:
        problems.append(
            f"Section D renders {missing_d} as dollar rows and this check "
            "neither compares them nor excuses them in _UNPAIRED"
        )
    if stale_a:
        problems.append(
            f"this check pairs Appendix A column(s) {stale_a}, which the "
            "pipeline table no longer produces"
        )
    if stale_d:
        problems.append(
            f"this check pairs Section D row(s) {stale_d}, which the section "
            "generator no longer produces"
        )
    if problems:
        raise CrossSurfaceCheckError(
            "the cross-surface agreement check has drifted out of step with "
            "the renderers it checks: " + "; ".join(problems) + ". A figure "
            "this document prints in two places and this check does not "
            "compare is exactly the gap that let $98,000,000 and $82,846,750 "
            "ship as one pipeline's leverage total."
        )


def _totals_row(kind: str, application):
    """The TOTALS row of one appendix, by calling the table builder itself."""
    if kind == "pipeline":
        from nmtcapp.tables.pipeline_table import build_pipeline_table
        df = build_pipeline_table(application.pipeline, application.cde)
    elif kind == "geographic":
        from nmtcapp.tables.geographic_table import build_geographic_table
        df = build_geographic_table(application.pipeline)
    elif kind == "impact":
        from nmtcapp.tables.impact_table import build_impact_summary_table
        df = build_impact_summary_table(application.pipeline)
    else:                                              # pragma: no cover
        raise CrossSurfaceCheckError(f"unknown appendix {kind!r}")
    if df.empty:
        raise CrossSurfaceCheckError(
            f"the {kind} appendix rendered empty for a pipeline with projects"
        )
    return df.iloc[-1], df.columns


def _shared_figures(application: "Application", deal_economics: dict) -> dict:
    """{label: {surface: value}} for every figure printed in more than one place.

    THE VALUES ARE READ OUT OF THE RENDERERS, BY CALLING THEM. The Section D
    column comes from the section generator's own economics table, parsed out
    of the rendered cell; each appendix column comes from that appendix's own
    TOTALS row. Nothing here recomputes a figure — a check that recomputed
    would agree with itself and not with the document.

    THE PAIRING IS HAND-WRITTEN and _APPENDIX_A_TO_SECTION_D says so. The
    COVERAGE is derived: see _assert_pairs_cover_every_money_column.

    RAISES rather than skipping. A pair whose column or row is missing used to
    hit a ``continue``, which quietly shrank the comparison set — the same
    fail-silent shape that dropped the Native Area column out of Word's
    Appendix A without a word (1.2.1 L-1). If the document has changed shape,
    this check cannot answer its question and must say so.
    """
    from nmtcapp.sections.section_d_capitalization import SectionDCapitalizationStrategy

    analysis = _EconomicsOnly(deal_economics)
    totals, appendix_a_columns = _totals_row("pipeline", application)

    section_d = SectionDCapitalizationStrategy().generate_content(application, analysis)
    economics = section_d["subsections"][0]["body"]

    _assert_pairs_cover_every_money_column(appendix_a_columns, economics)

    def _money(text) -> float:
        """Pull the leading dollar figure out of a rendered Section D cell."""
        match = re.search(r"\$([\d,]+(?:\.\d+)?)", str(text))
        if match is None:
            raise CrossSurfaceCheckError(
                f"Section D cell {text!r} carries no dollar figure to compare"
            )
        return float(match.group(1).replace(",", ""))

    shared = {}
    for label, (a_col, d_row) in _APPENDIX_A_TO_SECTION_D.items():
        shared[label] = {
            "Appendix A (per-project total)": float(totals[a_col]),
            "Section D (deal economics)": _money(economics[d_row]),
        }

    # The same figure across appendices. Built here rather than in a second
    # function so one non-empty guard covers both kinds of agreement.
    cache = {"pipeline": (totals, appendix_a_columns)}
    for label, surfaces in _APPENDIX_TOTALS.items():
        values = {}
        for surface_name, kind, column in surfaces:
            if kind not in cache:
                cache[kind] = _totals_row(kind, application)
            row, columns = cache[kind]
            if column not in columns:
                raise CrossSurfaceCheckError(
                    f"{surface_name} no longer has a {column!r} column, so "
                    f"{label!r} cannot be checked for agreement"
                )
            values[surface_name] = float(row[column])
        shared[label] = values

    # THE RATES, COMPARED RATHER THAN EXCUSED (FIX-2 G-3). Both are printed
    # twice per filing — once in Section D's economics table, once in the
    # methodology appendix every renderer emits — and until now nothing looked
    # at the pair. Read from the two renderers, not recomputed: a check that
    # recomputed would agree with itself and not with the document.
    from nmtcapp.renderers._methodology import deal_economics_note

    methodology = deal_economics_note()
    for label, (d_row, pattern) in _SECTION_D_TO_METHODOLOGY.items():
        if d_row not in economics:
            raise CrossSurfaceCheckError(
                f"Section D no longer has a {d_row!r} row, so {label!r} "
                "cannot be checked against the methodology appendix"
            )
        d_match = re.search(r"([\d.]+)", str(economics[d_row]))
        m_match = re.search(pattern, methodology)
        if d_match is None or m_match is None:
            raise CrossSurfaceCheckError(
                f"{label!r} could not be read from both surfaces "
                f"(Section D: {economics[d_row]!r}; methodology matched: "
                f"{m_match is not None}). The check cannot answer its question "
                "and must not report clean."
            )
        shared[label] = {
            "Section D (deal economics)": float(d_match.group(1)),
            "Methodology appendix": float(m_match.group(1)),
        }

    return shared


def check_cross_surface_agreement(application: "Application",
                                  deal_economics: dict = None) -> list:
    """Every figure this check DECLARES as shared must agree across its surfaces.

    THE CLAIM IS NARROWED TO WHAT THE CODE DOES, and what the code does is now
    wider (1.2.1 S-3). Through 1.2.1-rc the docstring said "any figure this
    document prints in more than one place must be one figure" while the
    implementation compared five dollar figures between Appendix A and Section
    D and nothing else. Total QEI is printed in Appendices A, C and D as well
    as Section D, and Jobs Created in Appendices A and D; none of those was
    ever compared. Both groups are compared now, and the claim above says
    "declares" rather than "any" because the two are not the same sentence and
    only one of them is checkable.

    WHAT IS STILL NOT COVERED, so nobody has to re-derive it: figures that
    appear in prose rather than in a table cell (Section B's distress shares
    against Appendix B's rows), and any figure a renderer computes for itself
    rather than reading from a table builder. Widening to those means giving
    this validator a rendered document to parse, which is
    tests/test_invariant_output.py's shape, not a validator's.

    THIS IS THE CHECK THAT DID NOT EXIST, and its absence is why a $10.2MM
    contradiction shipped. Section D reported leverage loans as the residual of
    QEI less investor equity, taken from nmtc-calc; Appendix A sized the same
    loans at a flat 80% of QEI from a module-local constant. Reproduced on the
    shipped 20-project sample before the fix: Appendix A $98,000,000 against
    Section D $82,846,750, in one generated document, with
    ``check_consistency`` passing.

    check_consistency existed to catch exactly this and could not, because
    every assertion in it was about one project's own fields. A cross-field
    check that never crosses a surface cannot fail on the defect that spans
    two surfaces — the tenth instance in this package of a gate that cannot
    fail on its own subject.

    ``deal_economics`` is the ``deal_economics_summary`` dict Section D renders
    from. Application.analyze() passes it in because this runs before the
    ApplicationAnalysis exists; a direct caller may omit it and pay for an
    analyze().

    Returns a list of issue strings; empty when every shared figure agrees.
    """
    if deal_economics is None:
        deal_economics = application.analyze().deal_economics
    try:
        shared = _shared_figures(application, deal_economics)
    except Exception as exc:
        # A check that cannot run must SAY SO as an issue, not return clean.
        return [
            f"Cross-surface agreement check could not run ({exc}); the "
            "document's shared figures are unverified"
        ]

    # THE NON-EMPTY GUARD, IN THE SHIPPED VALIDATOR (1.2.1 S-3).
    #
    # It used to live only in tests/validation/test_consistency_check.py, as
    # `len(shared) >= 4`. In a CDE's hands there is no test: forcing
    # _shared_figures to return {} produced issues == [] and
    # check_consistency.passed == True — a gate reporting success having
    # compared nothing, inside the check that was built because the previous
    # one could not fail on a $15.15MM contradiction.
    #
    # NOT A NUMERIC FLOOR, and deliberately. A floor of 4 against 5 declared
    # pairs lets one drop silently, and re-deriving the number from today's
    # count is how a floor stops being evidence. The invariant that does exist
    # is structural: EVERY DECLARED COMPARISON MUST HAVE BEEN MADE. The
    # declared set is itself derived — _assert_pairs_cover_every_money_column
    # requires it to cover every money column the renderers publish — so there
    # is no hand-chosen number anywhere in the chain.
    expected = (set(_APPENDIX_A_TO_SECTION_D) | set(_APPENDIX_TOTALS)
                | set(_SECTION_D_TO_METHODOLOGY))
    if set(shared) != expected:
        missing = sorted(expected - set(shared))
        extra = sorted(set(shared) - expected)
        return [
            "Cross-surface agreement check compared "
            f"{len(shared)} of {len(expected)} declared figure groups"
            + (f"; never compared: {missing}" if missing else "")
            + (f"; compared undeclared: {extra}" if extra else "")
            + ". Every figure this document prints in more than one place must "
            "be compared, and a check that silently compares fewer is a check "
            "that passes on a document nobody looked at."
        ]

    project_count = len(list(application.pipeline)) if application.pipeline else 0
    tolerance = max(
        _AGREEMENT_TOLERANCE_FLOOR,
        _AGREEMENT_TOLERANCE_PER_PROJECT * project_count,
    )

    issues = []
    for label, surfaces in shared.items():
        values = list(surfaces.values())
        if any(v != v for v in values):            # NaN: a cell did not parse
            issues.append(
                f"{label}: a figure could not be read back out of a rendered "
                f"surface ({surfaces}) — it cannot be checked for agreement"
            )
            continue
        # A DOLLAR TOLERANCE APPLIED TO A RATE COMPARES NOTHING (FIX-2 G-3).
        # The tolerance above is a per-project ROUNDING allowance measured in
        # dollars; against a credit price it is roughly a thousand times the
        # whole quantity, so $0.83 and $0.95 differ by 0.12 and sail under it.
        # Rates are compared exactly, to the precision each surface prints.
        is_rate = label in _SECTION_D_TO_METHODOLOGY
        limit = _RATE_AGREEMENT_TOLERANCE if is_rate else tolerance
        spread = max(values) - min(values)
        if spread > limit:
            if is_rate:
                detail = "; ".join(f"{name} {value:g}" for name, value in surfaces.items())
                issues.append(
                    f"{label} disagrees between surfaces of the same document: "
                    f"{detail} (difference {spread:g}). A rate printed in two "
                    "places must be one rate — Section D's capital stack and "
                    "the methodology appendix describe the same transaction."
                )
            else:
                detail = "; ".join(f"{name} ${value:,.0f}" for name, value in surfaces.items())
                issues.append(
                    f"{label} disagrees between surfaces of the same document: "
                    f"{detail} (difference ${spread:,.0f}). "
                    "A figure printed in two places must be one figure."
                )
    return issues


# State abbreviation → FIPS code prefix (2-digit)
_STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11",
}
