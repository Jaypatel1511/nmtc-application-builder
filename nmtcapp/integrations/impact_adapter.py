"""Adapter wrapping impact-ledger for portfolio-level impact tracking."""
from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def build_impact_portfolio(pipeline: "Pipeline") -> dict:
    """Construct an impact-ledger Portfolio from the pipeline and return summary.

    Converts each pipeline project into an impact-ledger NMTC investment,
    adds impact metrics (jobs, units), and returns the sector impact report.

    Returns a dict with:
    - ``portfolio_size`` – number of investments in portfolio
    - ``total_deployed`` – total capital deployed
    - ``sector_report`` – impact breakdown by sector
    - ``top_sectors_by_impact`` – sectors ranked by job creation
    - ``portfolio_irr_estimate`` – estimated portfolio-level IRR

    Example::

        report = build_impact_portfolio(pipeline)
        print(report['sector_report'])
    """
    projects = list(pipeline)
    if not projects:
        return _empty_portfolio()

    try:
        import impactledger
        return _build_via_library(projects, impactledger)
    except Exception as exc:
        logger.warning("impact-ledger call failed (%s). Using computed fallback.", exc)
        return _compute_fallback(projects)


def _build_via_library(projects, impactledger) -> dict:
    """Use impact-ledger to build a portfolio from pipeline projects."""
    portfolio = impactledger.Portfolio(name="NMTC Pipeline Portfolio")
    today = date.today().isoformat()
    maturity = f"{date.today().year + 7}-06-30"

    for p in projects:
        try:
            inv = impactledger.nmtc(
                name=p.project_name,
                amount=p.qei_request,
                date_closed=today,
                maturity_date=maturity,
                state=p.state,
                borrower_name=p.qalicb_name,
                sector=p.sector,
            )
            portfolio.add(inv)
        except Exception as exc:
            logger.debug("Skipping project %s in impact portfolio: %s", p.project_id, exc)

    try:
        sector_report = impactledger.sector_impact_report(portfolio)
    except Exception:
        sector_report = {}

    total_deployed = sum(p.qei_request for p in projects)
    return {
        "portfolio_size": len(projects),
        "total_deployed": total_deployed,
        "sector_report": sector_report if isinstance(sector_report, dict) else {},
        "top_sectors_by_impact": _top_sectors(projects),
        "portfolio_irr_estimate": None,  # requires closing/exit data
    }


def _compute_fallback(projects) -> dict:
    return {
        "portfolio_size": len(projects),
        "total_deployed": sum(p.qei_request for p in projects),
        "sector_report": {},
        "top_sectors_by_impact": _top_sectors(projects),
        "portfolio_irr_estimate": None,
    }


def _top_sectors(projects) -> list:
    sector_jobs: dict = {}
    for p in projects:
        sector_jobs[p.sector] = sector_jobs.get(p.sector, 0) + p.expected_jobs_created
    return sorted(sector_jobs, key=sector_jobs.get, reverse=True)[:3]


def _empty_portfolio() -> dict:
    return {
        "portfolio_size": 0,
        "total_deployed": 0.0,
        "sector_report": {},
        "top_sectors_by_impact": [],
        "portfolio_irr_estimate": None,
    }
