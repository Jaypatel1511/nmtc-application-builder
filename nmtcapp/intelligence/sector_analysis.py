"""Sector mix analysis for NMTC pipelines."""
from __future__ import annotations

import logging
import math
from collections import Counter
from typing import TYPE_CHECKING

from nmtcapp.data.schema import TARGET_SECTORS

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Priority sectors in winning applications (CDFI Fund historical data)
_HIGH_PRIORITY_SECTORS = {"healthcare", "affordable_housing", "education"}


def analyze_sector_mix(pipeline: "Pipeline") -> dict:
    """Compute sector composition and diversity metrics for the pipeline.

    Returns a dict with:
    - ``sector_breakdown`` – per-sector {count, qei_dollars, pct, priority}
    - ``dominant_sector`` – sector with highest QEI share
    - ``sector_diversity_score`` – 0–100 score (100 = perfectly even spread)
    - ``high_priority_pct`` – fraction of QEI in CDFI Fund priority sectors
    - ``sectors_represented`` – count of distinct sectors
    - ``vs_winning_application_patterns`` – qualitative label

    Example::

        result = analyze_sector_mix(pipeline)
        print(f"Dominant sector: {result['dominant_sector']}")
    """
    projects = list(pipeline)
    if not projects:
        return _empty_sector_result()

    total_qei = sum(p.qei_request for p in projects)
    if total_qei == 0:
        return _empty_sector_result()

    sector_qei: dict = {}
    sector_count: Counter = Counter()

    for p in projects:
        sector = p.sector
        sector_qei[sector] = sector_qei.get(sector, 0.0) + p.qei_request
        sector_count[sector] += 1

    sectors = sorted(sector_qei.keys())
    n_sectors = len(sectors)

    sector_breakdown = {
        s: {
            "count": sector_count[s],
            "qei_dollars": round(sector_qei[s]),
            "pct": sector_qei[s] / total_qei,
            "priority": TARGET_SECTORS.get(s, {}).get("priority", "unknown"),
        }
        for s in sectors
    }

    dominant_sector = max(sector_qei, key=sector_qei.get)

    # Shannon diversity → normalized 0–100
    diversity_score = _sector_diversity_score(sector_qei, total_qei)

    high_priority_qei = sum(
        v for k, v in sector_qei.items() if k in _HIGH_PRIORITY_SECTORS
    )
    high_priority_pct = high_priority_qei / total_qei

    max_single_sector_pct = max(
        (v["pct"] for v in sector_breakdown.values()), default=1.0
    )

    return {
        "sector_breakdown": sector_breakdown,
        "dominant_sector": dominant_sector,
        "sector_diversity_score": round(diversity_score, 1),
        "sectors_represented": n_sectors,
        "max_single_sector_pct": max_single_sector_pct,
        "high_priority_pct": high_priority_pct,
        "total_qei": total_qei,
        "vs_winning_application_patterns": _assess_vs_winners(high_priority_pct, n_sectors),
    }


def _sector_diversity_score(sector_qei: dict, total_qei: float) -> float:
    """Normalized Shannon entropy — 0 (single sector) to 100 (perfectly even)."""
    n = len(sector_qei)
    if n <= 1:
        return 0.0
    entropy = 0.0
    for v in sector_qei.values():
        p = v / total_qei
        if p > 0:
            entropy -= p * math.log(p)
    max_entropy = math.log(n)
    return (entropy / max_entropy) * 100 if max_entropy > 0 else 0.0


def _assess_vs_winners(high_priority_pct: float, n_sectors: int) -> str:
    if high_priority_pct >= 0.70 and n_sectors >= 3:
        return "strong_alignment"
    if high_priority_pct >= 0.50:
        return "moderate_alignment"
    return "weak_alignment"


def _empty_sector_result() -> dict:
    return {
        "sector_breakdown": {},
        "dominant_sector": None,
        "sector_diversity_score": 0.0,
        "sectors_represented": 0,
        "high_priority_pct": 0.0,
        "total_qei": 0.0,
        "vs_winning_application_patterns": "weak_alignment",
    }
