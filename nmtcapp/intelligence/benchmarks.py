"""Compare a pipeline analysis result against historical NMTC winner benchmarks."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from nmtcapp.data.benchmark_thresholds import (
    BENCHMARK_METRIC_WEIGHTS,
    BENCHMARK_SCORE_POINTS,
    WINNER_PATTERN_THRESHOLDS,
)
from nmtcapp.data.historical_awards import (
    WINNER_DISTRESS_PATTERNS,
    WINNER_GEOGRAPHIC_PATTERNS,
    WINNER_IMPACT_BENCHMARKS,
    WINNER_SECTOR_PATTERNS,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

_METHODOLOGY = (
    "Benchmarks compare input metrics against patterns observed in CDFI Fund NMTC "
    "award announcements (CY2020–CY2024). Only winner-level data is publicly "
    "available; non-winner distributions are unknown. Scores reflect alignment "
    "with historical winners, not probability of selection. Use as diagnostic "
    "guidance only — not as a prediction of funding outcomes."
)


@dataclass
class MetricBenchmark:
    """Benchmark assessment for a single metric against historical winners."""
    metric: str
    label: str
    value: float
    tier: str                   # "strong", "competitive", "weak", "below_weak"
    score: float                # 0–100 benchmark contribution
    threshold_strong: float
    threshold_competitive: float
    threshold_weak: float
    percentile_vs_winners: float  # 0.0–1.0 estimated position in winner distribution
    note: str

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "label": self.label,
            "value": self.value,
            "tier": self.tier,
            "score": self.score,
            "thresholds": {
                "strong": self.threshold_strong,
                "competitive": self.threshold_competitive,
                "weak": self.threshold_weak,
            },
            "percentile_vs_winners": self.percentile_vs_winners,
            "note": self.note,
        }


@dataclass
class BenchmarkComparison:
    """Full benchmark comparison of a pipeline against historical NMTC winners.

    Example::

        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        bc = HistoricalBenchmarks().compare(pipeline_result, 55_000_000)
        print(bc.summary())
    """
    metrics: List[MetricBenchmark]
    overall_benchmark_score: float
    tier_summary: dict
    methodology_disclosure: str = field(default=_METHODOLOGY)

    def summary(self) -> str:
        """Return a formatted benchmark comparison report."""
        _tier_symbol = {
            "strong": "[+]",
            "competitive": "[~]",
            "weak": "[-]",
            "below_weak": "[!]",
        }
        lines = [
            "=" * 68,
            "  BENCHMARK vs. HISTORICAL NMTC WINNERS (CY2020–CY2024)",
            f"  Overall Alignment Score: {self.overall_benchmark_score:.1f} / 100",
            "=" * 68,
            "",
        ]
        for t in ("strong", "competitive", "weak", "below_weak"):
            cnt = self.tier_summary.get(t, 0)
            if cnt:
                sym = _tier_symbol[t]
                lines.append(f"  {sym} {t.upper():<18} {cnt} metric(s)")
        lines.append("")
        lines.append(f"  {'Metric':<34} {'Value':>8}   {'Tier':<12}  Pctile")
        lines.append(f"  {'-'*34} {'-'*8}   {'-'*12}  ------")
        for m in self.metrics:
            sym = _tier_symbol.get(m.tier, "[ ]")
            lines.append(
                f"  {sym} {m.label:<32} {m.value:>8.2f}   {m.tier:<12}  "
                f"{m.percentile_vs_winners:.0%}"
            )
        lines.extend([
            "",
            "  Methodology:",
            f"  {self.methodology_disclosure[:140]}",
            "=" * 68,
        ])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "overall_benchmark_score": self.overall_benchmark_score,
            "tier_summary": self.tier_summary,
            "metrics": [m.to_dict() for m in self.metrics],
            "methodology_disclosure": self.methodology_disclosure,
        }


class HistoricalBenchmarks:
    """Compare a pipeline analysis result to CDFI Fund historical winner patterns.

    Example::

        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        bc = HistoricalBenchmarks().compare(pipeline_result, 55_000_000)
        bc.summary()
    """

    def compare(
        self,
        pipeline_result: "PipelineAnalysisResult",
        requested_allocation: float,
    ) -> BenchmarkComparison:
        """Run the full benchmark comparison.

        Args:
            pipeline_result: Result from :class:`~nmtcapp.intelligence.pipeline_analyzer.PipelineAnalyzer`.
            requested_allocation: CDE's requested allocation in dollars.

        Returns:
            :class:`BenchmarkComparison` with per-metric assessments and composite score.

        Example::

            bc = HistoricalBenchmarks().compare(result, 55_000_000)
            print(bc.summary())
        """
        d = pipeline_result.distress_breakdown
        g = pipeline_result.geographic_diversity
        s = pipeline_result.sector_mix
        i = pipeline_result.aggregate_impact

        metrics: List[MetricBenchmark] = []

        # Distress concentration
        metrics.append(self._assess(
            "min_deep_distress_pct", "Deep/Severe Distress %",
            value=d.get("pct_deep_or_severe", 0.0),
            higher_is_better=True,
            winner_mean=WINNER_DISTRESS_PATTERNS["mean_pct_deep_or_severe"],
            winner_std=WINNER_DISTRESS_PATTERNS["std_pct_deep_or_severe"],
            note=f"Winner median: {WINNER_DISTRESS_PATTERNS['p50_pct_deep_or_severe']:.0%}",
        ))

        # States served
        metrics.append(self._assess(
            "min_geographic_states", "States Served",
            value=float(g.get("states_count", 0)),
            higher_is_better=True,
            winner_mean=WINNER_GEOGRAPHIC_PATTERNS["mean_states"],
            winner_std=WINNER_GEOGRAPHIC_PATTERNS["std_states"],
            note=f"Winner median: {WINNER_GEOGRAPHIC_PATTERNS['p50_states']:.0f} states",
        ))

        # Geographic HHI
        metrics.append(self._assess(
            "max_geographic_hhi", "Geographic HHI",
            value=float(g.get("hhi", 10_000)),
            higher_is_better=False,
            winner_mean=WINNER_GEOGRAPHIC_PATTERNS["mean_hhi"],
            winner_std=300.0,
            note=f"Winner mean HHI: {WINNER_GEOGRAPHIC_PATTERNS['mean_hhi']:.0f}",
        ))

        # Jobs per $1MM QEI
        metrics.append(self._assess(
            "min_jobs_per_mm_qei", "Jobs per $1MM QEI",
            value=float(i.get("jobs_per_million_qei", 0.0)),
            higher_is_better=True,
            winner_mean=WINNER_IMPACT_BENCHMARKS["mean_jobs_per_mm_qei"],
            winner_std=6.0,
            note=f"Winner p75: {WINNER_IMPACT_BENCHMARKS['p75_jobs_per_mm_qei']:.0f} jobs/$MM",
        ))

        # Max single sector
        metrics.append(self._assess(
            "max_single_sector_pct", "Max Single Sector %",
            value=float(s.get("max_single_sector_pct", 1.0)),
            higher_is_better=False,
            winner_mean=WINNER_SECTOR_PATTERNS["max_single_sector_pct"],
            winner_std=0.08,
            note=f"Winners rarely exceed {WINNER_SECTOR_PATTERNS['max_single_sector_pct']:.0%}",
        ))

        # Sectors represented
        metrics.append(self._assess(
            "min_sectors_represented", "Sectors Represented",
            value=float(s.get("sectors_represented", 0)),
            higher_is_better=True,
            winner_mean=WINNER_SECTOR_PATTERNS["mean_sectors_represented"],
            winner_std=1.2,
            note=f"Winner mean: {WINNER_SECTOR_PATTERNS['mean_sectors_represented']:.1f} sectors",
        ))

        # Pipeline project count
        metrics.append(self._assess(
            "min_projects", "Pipeline Projects",
            value=float(pipeline_result.total_projects),
            higher_is_better=True,
            winner_mean=WINNER_GEOGRAPHIC_PATTERNS["mean_projects"],
            winner_std=4.0,
            note=f"Winner median: {WINNER_GEOGRAPHIC_PATTERNS['p50_projects']:.0f} projects",
        ))

        # Eligibility rate
        metrics.append(self._assess(
            "min_eligible_pct", "NMTC Eligibility %",
            value=pipeline_result.eligibility_pct,
            higher_is_better=True,
            winner_mean=WINNER_DISTRESS_PATTERNS["mean_pct_eligible"],
            winner_std=0.04,
            note="Winners average 96% eligibility",
        ))

        # Rural concentration
        metrics.append(self._assess(
            "min_rural_pct", "Rural % of QEI",
            value=float(g.get("rural_pct", 0.0)),
            higher_is_better=True,
            winner_mean=WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"],
            winner_std=0.10,
            note=f"Winner mean rural: {WINNER_GEOGRAPHIC_PATTERNS['rural_pct_mean']:.0%}",
        ))

        overall = self._weighted_score(metrics)
        tier_summary = {
            t: sum(1 for m in metrics if m.tier == t)
            for t in ("strong", "competitive", "weak", "below_weak")
        }

        return BenchmarkComparison(
            metrics=metrics,
            overall_benchmark_score=round(overall, 1),
            tier_summary=tier_summary,
        )

    def _assess(
        self,
        metric: str,
        label: str,
        value: float,
        higher_is_better: bool,
        winner_mean: float,
        winner_std: float,
        note: str,
    ) -> MetricBenchmark:
        thresholds = WINNER_PATTERN_THRESHOLDS.get(metric, {})
        t_strong = float(thresholds.get("strong", winner_mean))
        t_competitive = float(thresholds.get("competitive", winner_mean * 0.7))
        t_weak = float(thresholds.get("weak", winner_mean * 0.4))

        if higher_is_better:
            if value >= t_strong:
                tier = "strong"
            elif value >= t_competitive:
                tier = "competitive"
            elif value >= t_weak:
                tier = "weak"
            else:
                tier = "below_weak"
        else:
            if value <= t_strong:
                tier = "strong"
            elif value <= t_competitive:
                tier = "competitive"
            elif value <= t_weak:
                tier = "weak"
            else:
                tier = "below_weak"

        score = float(BENCHMARK_SCORE_POINTS[tier])
        std_safe = max(winner_std, 1e-9)
        raw_pctile = _normal_cdf((value - winner_mean) / std_safe)
        percentile = raw_pctile if higher_is_better else (1.0 - raw_pctile)
        percentile = min(1.0, max(0.0, percentile))

        return MetricBenchmark(
            metric=metric,
            label=label,
            value=value,
            tier=tier,
            score=score,
            threshold_strong=t_strong,
            threshold_competitive=t_competitive,
            threshold_weak=t_weak,
            percentile_vs_winners=round(percentile, 3),
            note=note,
        )

    def _weighted_score(self, metrics: List[MetricBenchmark]) -> float:
        total_w = 0.0
        weighted = 0.0
        for m in metrics:
            w = BENCHMARK_METRIC_WEIGHTS.get(m.metric, 0.0)
            weighted += m.score * w
            total_w += w
        return (weighted / total_w) if total_w > 0 else 0.0


def _normal_cdf(x: float) -> float:
    return math.erfc(-x / math.sqrt(2)) * 0.5
