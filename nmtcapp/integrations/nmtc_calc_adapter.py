"""Adapter wrapping nmtc-calc for deal economics computation."""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from nmtcapp.data.schema import NMTC_PROGRAM_CONSTRAINTS

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def compute_pipeline_economics(pipeline: "Pipeline") -> dict:
    """Use nmtc-calc to compute aggregate deal economics for the pipeline.

    For each project, structures a standard NMTC leveraged transaction
    using published CDFI Fund typical parameters. Returns aggregate figures.

    Returns a dict with:
    - ``total_qei`` – sum of all QEI requests
    - ``total_nmtcs`` – total NMTC credits generated (39% of QEI × 7 years)
    - ``total_investor_equity`` – total tax credit equity at $0.83/credit
    - ``total_leverage_loans`` – leverage loan component, the residual of QEI
      less investor equity, so leverage + equity = QEI
    - ``total_cde_fees`` – aggregate CDE fees (2.5% of QEI)
    - ``total_net_subsidy`` – QEI less CDE fees. NOT the QALICB's retained
      benefit: the leverage loan inside the QEI is repaid or refinanced, so
      this figure is ~97.5% of QEI and is renamed "QEI Less CDE Fees ($)"
      wherever it renders. The key keeps its name because it is published
      through ``ApplicationAnalysis.to_dict()`` and 1.2.1 is a patch.
    - ``project_count`` – number of projects modeled
    - ``avg_leverage_ratio`` – leverage loan divided by INVESTOR EQUITY, the
      quantity nmtc-calc computes (a multiple, ~2.09x), not a fraction of QEI

    Example::

        economics = compute_pipeline_economics(pipeline)
        print(f"Total NMTCs: ${economics['total_nmtcs']:,.0f}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_economics()

    # THE BLANKET ``except Exception`` IS GONE (1.7.2). nmtc-calc 0.3.0
    # renamed ``TransactionResult.leverage_ratio``; the AttributeError landed
    # in a handler that caught everything, and every install that resolved
    # 0.3.0 -- including 1.7.1 from PyPI -- silently took the fallback below,
    # with nothing but a log line on stderr to say so. An API break is not a
    # data condition. Two narrow fallbacks remain, each for a reason:
    #
    #   nmtc-calc ABSENT   ModuleNotFoundError whose .name is exactly
    #                "nmtccalc": the package is not installed at all. The
    #                fallback models the same identity, so the analysis still
    #                runs, and the log says why. Any OTHER import failure --
    #                ``nmtccalc.models.transaction`` missing, ``NMTCDeal`` not
    #                importable from ``nmtccalc`` -- is a rename inside the
    #                package and propagates (fix round 1, X7).
    #   INPUT REFUSED      ValueError or ArithmeticError from nmtc-calc's own
    #                construction or arithmetic. ValueError is its documented
    #                contract (NMTCDeal.__post_init__; NegativeTrancheError and
    #                UnbalancedStackError subclass it) -- a row with QEI above
    #                total project cost is refused by every nmtc-calc version
    #                and accepted by PipelineProject. ArithmeticError is the
    #                degenerate-number case: a row of 5e-324 everywhere
    #                underflows investor equity to 0.0 and structure() divides
    #                by it. 1.7.1 fell back there (by accident, through the
    #                blanket handler); the first cut of this fix crashed with
    #                ZeroDivisionError (fix round 1, X6).
    #
    # Everything else -- AttributeError, TypeError, a changed signature --
    # propagates, with the installed nmtc-calc version named.
    try:
        from nmtccalc import NMTCDeal
        import nmtccalc.models.transaction as nmtc_transaction
    except ModuleNotFoundError as exc:
        if exc.name != "nmtccalc":
            raise
        logger.warning(
            "nmtc-calc is not installed (%s). Using manual computation fallback.", exc
        )
        return _compute_fallback(projects)
    #
    # THE INPUT-REFUSED HANDLER WRAPS nmtc-calc's CALLS ONLY (fix round 2).
    # It used to wrap the whole of ``_compute_via_library``, so the adapter's
    # OWN summing and rounding sat inside it: with every row at 1e308 the
    # totals overflow to inf, ``round(inf)`` raises OverflowError, the log
    # blamed nmtc-calc ("nmtc-calc refused a deal's inputs (OverflowError")
    # -- and the fallback then overflowed on the same sum and raised anyway.
    # Now only ``NMTCDeal(...)`` and ``structure()`` for one project are
    # inside it (``_Refused`` carries the cause out), and totals that cannot
    # be represented raise ``PipelineTotalsOverflow`` from either path,
    # naming the adapter's own arithmetic.
    try:
        return _compute_via_library(projects, NMTCDeal, nmtc_transaction)
    except _Refused as refused:
        exc = refused.cause
        logger.warning(
            "nmtc-calc refused the inputs of project %r (%s: %s). Using manual "
            "computation fallback.", refused.project_name, type(exc).__name__, exc
        )
        return _compute_fallback(projects)


class _Refused(Exception):
    """nmtc-calc's own ValueError/ArithmeticError for one project, carried out
    of the loop so that nothing but ``NMTCDeal(...)`` and ``structure()`` is
    ever inside the handler that falls back."""

    def __init__(self, project_name, cause):
        super().__init__(project_name, cause)
        self.project_name = project_name
        self.cause = cause


class PipelineTotalsOverflow(OverflowError):
    """The pipeline's summed figures exceed the float range. Raised by the
    adapter's own arithmetic, from either path -- not an nmtc-calc refusal and
    not a reason to fall back (the fallback sums the same numbers)."""


def _checked_totals(totals: dict) -> dict:
    bad = sorted(k for k, v in totals.items() if not math.isfinite(v))
    if bad:
        raise PipelineTotalsOverflow(
            f"the pipeline's summed {', '.join(bad)} exceed the float range; "
            "the per-project figures are finite but their total is not "
            "representable. This is the adapter's own summation, not nmtc-calc."
        )
    return totals


#: The leverage-loan / investor-equity multiple on ``TransactionResult``, by
#: the name each nmtc-calc line uses. Same definition in both --
#: ``deal.leverage_loan / deal.investor_equity`` in ``structure()``
#: (0.2.1 models/transaction.py:85; 0.3.0 models/transaction.py:127) -- and
#: 0.3.0's own LEVERAGE_RATIO_NOTE says "(0.2.1 called it leverage_ratio.)".
LEVERAGE_TO_EQUITY_FIELDS = (
    "leverage_loan_to_equity_ratio",   # nmtc-calc >= 0.3.0
    "leverage_ratio",                  # nmtc-calc 0.2.x
)


def _nmtc_calc_version() -> str:
    try:
        from importlib.metadata import version
        return version("nmtc-calc")
    except Exception:  # pragma: no cover - metadata absent
        return "unknown"


def leverage_to_equity(result) -> float:
    """The leverage/equity multiple off a ``TransactionResult``, any supported
    nmtc-calc. Raises -- never falls back -- when neither name is present,
    because that is an nmtc-calc API this package has not been checked
    against."""
    for name in LEVERAGE_TO_EQUITY_FIELDS:
        if hasattr(result, name):
            return getattr(result, name)
    raise AttributeError(
        f"nmtc-calc {_nmtc_calc_version()}'s TransactionResult carries none of "
        f"{LEVERAGE_TO_EQUITY_FIELDS}. This package has not been checked "
        "against that nmtc-calc API; see the dependency bound in pyproject.toml."
    )


def _compute_via_library(projects, NMTCDeal, nmtc_transaction) -> dict:
    """Use nmtc-calc library to structure each deal."""
    credit_price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    cde_fee_rate = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]

    totals = {
        "qei": 0.0, "nmtcs": 0.0, "investor_equity": 0.0,
        "leverage_loans": 0.0, "cde_fees": 0.0, "leverage_ratio_sum": 0.0,
    }

    for p in projects:
        try:
            deal = NMTCDeal(
                project_name=p.project_name,
                total_project_cost=p.total_project_cost,
                nmtc_allocation=p.qei_request,
                credit_price=credit_price,
                leverage_loan_rate=0.055,
                qlici_a_loan_rate=0.01,
                qlici_b_loan_rate=0.055,
                cde_fee_rate=cde_fee_rate,
            )
            result = nmtc_transaction.structure(deal)
        except (ValueError, ArithmeticError) as exc:
            raise _Refused(p.project_name, exc) from exc
        totals["qei"] += result.qei
        totals["nmtcs"] += result.total_nmtcs
        totals["investor_equity"] += result.investor_equity
        totals["leverage_loans"] += result.leverage_loan
        totals["cde_fees"] += result.cde_fee
        totals["leverage_ratio_sum"] += leverage_to_equity(result)

    n = len(projects)
    _checked_totals(totals)
    return {
        "total_qei": round(totals["qei"]),
        "total_nmtcs": round(totals["nmtcs"]),
        "total_investor_equity": round(totals["investor_equity"]),
        "total_leverage_loans": round(totals["leverage_loans"]),
        "total_cde_fees": round(totals["cde_fees"]),
        "total_net_subsidy": round(totals["qei"] - totals["cde_fees"]),
        "project_count": n,
        "avg_leverage_ratio": round(totals["leverage_ratio_sum"] / n, 3) if n > 0 else 0.0,
    }


def _compute_fallback(projects) -> dict:
    """Manual fallback, modelling the SAME structure the library models.

    THE TWO BRANCHES USED TO DISAGREE, and a CDE could not tell which one had
    run. ``_compute_via_library`` takes nmtc-calc's leverage loan, which is the
    residual QEI less investor equity; this branch sized it as
    ``total_qei * leverage_ratio_typical`` — a flat 80%. On the shipped
    20-project sample that is $98,000,000 here against $82,846,750 there, a
    $15.15MM difference in Section D's "Total Leverage Loans ($)" decided by
    whether nmtc-calc happened to be importable.

    Both now use the identity that is true of the structure the document
    describes: leverage loan + investor equity = QEI. ``leverage_ratio_typical``
    is no longer read anywhere.

    ``avg_leverage_ratio`` carried the same split definition — nmtc-calc
    defines it leverage/EQUITY (models/transaction.py:85, ~2.09x on that
    sample) while this branch returned 0.80, a fraction of QEI. Same key, two
    incompatible quantities, a factor of 2.6 apart. It now means what the
    library means. Nothing renders it; it reaches library callers through
    ``ApplicationAnalysis.to_dict()["deal_economics"]``.
    """
    credit_rate = NMTC_PROGRAM_CONSTRAINTS["credit_rate"]
    credit_price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    cde_fee_rate = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]

    total_qei = sum(p.qei_request for p in projects)
    total_nmtcs = total_qei * credit_rate
    total_investor_equity = total_nmtcs * credit_price
    total_leverage = max(0.0, total_qei - total_investor_equity)
    total_cde_fees = total_qei * cde_fee_rate
    _checked_totals({"qei": total_qei, "nmtcs": total_nmtcs,
                     "investor_equity": total_investor_equity,
                     "leverage_loans": total_leverage, "cde_fees": total_cde_fees})

    return {
        "total_qei": round(total_qei),
        "total_nmtcs": round(total_nmtcs),
        "total_investor_equity": round(total_investor_equity),
        "total_leverage_loans": round(total_leverage),
        "total_cde_fees": round(total_cde_fees),
        "total_net_subsidy": round(total_qei - total_cde_fees),
        "project_count": len(projects),
        "avg_leverage_ratio": (
            round(total_leverage / total_investor_equity, 3)
            if total_investor_equity else 0.0
        ),
    }


def _empty_economics() -> dict:
    return {
        "total_qei": 0,
        "total_nmtcs": 0,
        "total_investor_equity": 0,
        "total_leverage_loans": 0,
        "total_cde_fees": 0,
        "total_net_subsidy": 0,
        "project_count": 0,
        "avg_leverage_ratio": 0.0,
    }
