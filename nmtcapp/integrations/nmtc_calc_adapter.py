"""Adapter wrapping nmtc-calc for deal economics computation."""
from __future__ import annotations

import logging
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

    try:
        from nmtccalc import NMTCDeal
        import nmtccalc.models.transaction as nmtc_transaction
        return _compute_via_library(projects, NMTCDeal, nmtc_transaction)
    except Exception as exc:
        logger.warning(
            "nmtc-calc computation failed (%s). Using manual computation fallback.", exc
        )
        return _compute_fallback(projects)


def _compute_via_library(projects, NMTCDeal, nmtc_transaction) -> dict:
    """Use nmtc-calc library to structure each deal."""
    credit_price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    cde_fee_rate = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]

    totals = {
        "qei": 0.0, "nmtcs": 0.0, "investor_equity": 0.0,
        "leverage_loans": 0.0, "cde_fees": 0.0, "leverage_ratio_sum": 0.0,
    }

    for p in projects:
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
        totals["qei"] += result.qei
        totals["nmtcs"] += result.total_nmtcs
        totals["investor_equity"] += result.investor_equity
        totals["leverage_loans"] += result.leverage_loan
        totals["cde_fees"] += result.cde_fee
        totals["leverage_ratio_sum"] += result.leverage_ratio

    n = len(projects)
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
