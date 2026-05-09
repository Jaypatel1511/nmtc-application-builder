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
    - ``total_leverage_loans`` – total leverage loan component
    - ``total_cde_fees`` – aggregate CDE fees (2.5% of QEI)
    - ``total_net_subsidy`` – total net subsidy to QALICBs (QEI – fees)
    - ``project_count`` – number of projects modeled
    - ``avg_leverage_ratio`` – average leverage ratio across deals

    Example::

        economics = compute_pipeline_economics(pipeline)
        print(f"Total NMTCs: ${economics['total_nmtcs']:,.0f}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_economics()

    try:
        from nmtccalc import NMTCDeal
        import nmtccalc.transaction as nmtc_transaction
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
    """Manual fallback using published NMTC program parameters."""
    credit_rate = NMTC_PROGRAM_CONSTRAINTS["credit_rate"]
    credit_price = NMTC_PROGRAM_CONSTRAINTS["standard_credit_price"]
    cde_fee_rate = NMTC_PROGRAM_CONSTRAINTS["cde_fee_rate_typical"]
    leverage_ratio = NMTC_PROGRAM_CONSTRAINTS["leverage_ratio_typical"]

    total_qei = sum(p.qei_request for p in projects)
    total_nmtcs = total_qei * credit_rate
    total_investor_equity = total_nmtcs * credit_price
    total_leverage = total_qei * leverage_ratio
    total_cde_fees = total_qei * cde_fee_rate

    return {
        "total_qei": round(total_qei),
        "total_nmtcs": round(total_nmtcs),
        "total_investor_equity": round(total_investor_equity),
        "total_leverage_loans": round(total_leverage),
        "total_cde_fees": round(total_cde_fees),
        "total_net_subsidy": round(total_qei - total_cde_fees),
        "project_count": len(projects),
        "avg_leverage_ratio": leverage_ratio,
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
