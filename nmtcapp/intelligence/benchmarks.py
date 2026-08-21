"""Place a pipeline's metrics in THIS TOOL'S OWN diagnostic bands.

NOT A COMPARISON AGAINST WINNERS, and the module summary said it was until
1.5.0: "Compare a pipeline analysis result against historical NMTC winner
benchmarks." No winner distribution was ever loaded, and the bands below are
not derived from one.

WHAT THE FUND PUBLISHES -- CORRECTED. THE TEXT THAT STOOD HERE WAS FALSE.
This docstring and ``_METHODOLOGY`` both asserted that the CDFI Fund
"publishes no winner-pattern distribution" and does "not report the
distribution of any pipeline characteristic across" Allocatees. That was
untrue on the day it was written. On **7 August 2026** -- thirteen days before
this module was last edited -- the Fund released the **NMTC Public Data
Release 2003-2023** (announced at cdfifund.gov/news/736): a 24-slide summary
report and a transaction-level workbook of **21,202 QLICI rows** carrying CDE
name, state, QLICI amount, Metro/Non-Metro, origination year, QALICB type and
census tract. Separately, each round's **Award Book** reports pipeline
commitments across the Allocatees of that round -- the CY 2024-2025 edition
gives the service-area scope of all 142 (65 national, 39 multistate, 24
statewide, 14 local) and their rural, Native-area and deep-distress
commitments. Per-Allocatee distributions ARE published. This module gave their
non-existence as the reason 61 constants could not be sourced.

WHY THE CONSTANTS STILL DO NOT MOVE, WHICH IS A NARROWER CLAIM. The Fund's
figures are QLICI-DOLLAR-DENOMINATED REALIZED DEPLOYMENT across Allocatees.
The constants here are QEI-DENOMINATED APPLICATION-PIPELINE figures. Those are
different quantities over different populations, and reconciling them is real
inferential work on an artifact that informs a federal filing -- methodology
written and hostile-audited BEFORE any number changes, which is this project's
standing rule. Application-level data for non-winners remains unpublished.

So every value below is a HOUSE ESTIMATE PENDING THAT RECONCILIATION. That is
what is true today, and it is deliberately phrased so a future round can
correct the numbers without first having to retract a false claim about the
Fund -- which is the position the 1.5.0 sentence created.

What this module does is place each metric in a strong / competitive / weak
band against a threshold in ``data.benchmark_thresholds.WINNER_PATTERN_THRESHOLDS``
-- round numbers this package chose, carrying ``HOUSE`` rows in
``tests/scoring_attribution.txt`` because no retrievable document supports
them. The bands are a prompt about your own pipeline, not a measurement of
where you stand.

DELETED IN 1.5.0: ``percentile_vs_winners``. It pushed an invented mean and an
invented standard deviation through a normal CDF to assert a POSITION IN A
DISTRIBUTION -- location, spread and distributional family all fabricated, for
a population this package holds no data on. Six of its eight standard
deviations were bare literals typed at the call site. It was the most
authoritative-looking number here and every input to it was made up.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from nmtcapp.renderers._disclosure import wrap_disclosure
from nmtcapp.data.benchmark_thresholds import (
    BENCHMARK_METRIC_WEIGHTS,
    BENCHMARK_SCORE_POINTS,
    WINNER_PATTERN_THRESHOLDS,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

_METHODOLOGY = (
    "THESE BANDS ARE THIS TOOL'S OWN, NOT A CDFI FUND FIGURE. Each metric is "
    "placed in a strong / competitive / weak band by comparing it to a "
    "threshold in nmtcapp.data.benchmark_thresholds.WINNER_PATTERN_THRESHOLDS. "
    "The CDFI Fund publishes no such thresholds: the bands are round numbers "
    "chosen by this package and are unsourced. The Fund DOES publish data on "
    "its Allocatees: the NMTC Public Data Release covering 2003 through 2023 "
    "(released 7 August 2026; 21,202 transaction rows), and each round's "
    "Award Book. But those report REALIZED DEPLOYMENT measured in QLICI "
    "dollars, while these bands are APPLICATION PIPELINE figures measured in "
    "QEI. This package has NOT reconciled the two, and application data for "
    "entities that did not win is not published at all; these values are "
    "house estimates pending that work. "
    "A band "
    "is therefore a diagnostic prompt about your own pipeline, NOT a "
    "measurement of where you stand against real applicants, NOT a percentile, "
    "and NOT a prediction of any funding outcome."
)


@dataclass
class MetricBenchmark:
    """One metric's placement in this tool's own diagnostic bands."""
    metric: str
    label: str
    value: float
    tier: str                   # "strong", "competitive", "weak", "below_weak"
    score: float                # 0–100 benchmark contribution
    threshold_strong: float
    threshold_competitive: float
    threshold_weak: float
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
            "note": self.note,
        }


@dataclass
class BenchmarkComparison:
    """A pipeline's metrics placed in this tool's own diagnostic bands.

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
            "  PIPELINE DIAGNOSTIC BANDS — THIS TOOL'S OWN, NOT CDFI FUND DATA",
            f"  Overall Band Score: {self.overall_benchmark_score:.1f} / 100 "
            "(this tool's own scale)",
            "=" * 68,
            "",
        ]
        for t in ("strong", "competitive", "weak", "below_weak"):
            cnt = self.tier_summary.get(t, 0)
            if cnt:
                sym = _tier_symbol[t]
                lines.append(f"  {sym} {t.upper():<18} {cnt} metric(s)")
        lines.append("")
        # NOT AN f-STRING EXPRESSION. A backslash inside the braces is a
        # SyntaxError before 3.12, and requires-python is >=3.9 -- caught by
        # running the sdist suite on 3.9.25, which is why that run is part of
        # deriving FLOOR rather than an optional extra.
        _band_header = "Band (this tool's own)"
        lines.append(f"  {'Metric':<34} {'Value':>8}   {_band_header}")
        lines.append(f"  {'-'*34} {'-'*8}   {'-'*22}")
        for m in self.metrics:
            sym = _tier_symbol.get(m.tier, "[ ]")
            lines.append(
                f"  {sym} {m.label:<32} {m.value:>8.2f}   {m.tier}"
            )
        lines.extend([
            "",
            "  Methodology:",
            *wrap_disclosure(self.methodology_disclosure),
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
    """Place a pipeline's metrics in this tool's own diagnostic bands.

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
            note="Band boundaries are this tool's own; the CDFI Fund "
                 "publishes no distribution of this figure across winners.",
        ))

        # States served
        metrics.append(self._assess(
            "min_geographic_states", "States Served",
            value=float(g.get("states_count", 0)),
            higher_is_better=True,
            note="Band boundaries are this tool's own. Geographic reach is "
                 "a real scoring consideration; the state COUNTS here are not "
                 "a Fund figure.",
        ))

        # Geographic HHI
        metrics.append(self._assess(
            "max_geographic_hhi", "Geographic HHI",
            value=float(g.get("hhi", 10_000)),
            higher_is_better=False,
            note="HHI and its band boundaries are this tool's own "
                 "construct. The CDFI Fund neither computes nor publishes an "
                 "HHI for any applicant.",
        ))

        # Jobs per $1MM QEI
        metrics.append(self._assess(
            "min_jobs_per_mm_qei", "Jobs per $1MM QEI",
            value=float(i.get("jobs_per_million_qei", 0.0)),
            higher_is_better=True,
            note="Band boundaries are this tool's own. The CDFI Fund "
                 "publishes no jobs-per-QEI benchmark in any denominator.",
        ))

        # Max single sector
        metrics.append(self._assess(
            "max_single_sector_pct", "Max Single Sector %",
            value=float(s.get("max_single_sector_pct", 1.0)),
            higher_is_better=False,
            note="Band boundaries are this tool's own; no Fund question "
                 "asks for a sector concentration limit.",
        ))

        # Sectors represented
        metrics.append(self._assess(
            "min_sectors_represented", "Sectors Represented",
            value=float(s.get("sectors_represented", 0)),
            higher_is_better=True,
            note="Band boundaries are this tool's own; no Fund question "
                 "asks how many sectors a pipeline spans.",
        ))

        # Pipeline project count
        metrics.append(self._assess(
            "min_projects", "Pipeline Projects",
            value=float(pipeline_result.total_projects),
            higher_is_better=True,
            note="Band boundaries are this tool's own; the Fund publishes "
                 "no project-count distribution across Allocatees.",
        ))

        # Eligibility rate
        metrics.append(self._assess(
            "min_eligible_pct", "NMTC Eligibility %",
            value=pipeline_result.eligibility_pct,
            higher_is_better=True,
            note="Band boundaries are this tool's own. Eligibility itself "
                 "is a statutory test, but the bands over it are not a Fund "
                 "figure.",
        ))

        # THE RURAL BENCHMARK IS DELETED (1.4.0 premise ruling), and this
        # comment is its record because a removal leaves nothing else behind.
        #
        # It scored `geographic_diversity["rural_pct"]` against
        # WINNER_GEOGRAPHIC_PATTERNS["rural_pct_mean"] at weight 0.05 and rolled
        # the result into overall_benchmark_score. Four defects stacked, and
        # repairing only the first would have made the other three harder to
        # see, not easier:
        #
        #   1. THE CDE'S SIDE had no basis — a QEI share over a hard-coded
        #      twelve-state list. That is what 1.4.0 R2 fixed.
        #   2. THE WINNER'S SIDE has none either, and this package already
        #      knows it. data/historical_awards.py's own header states that the
        #      four "Source: CDFI Fund Annual Reports" comments — including the
        #      one over WINNER_GEOGRAPHIC_PATTERNS — cite a publication that
        #      does not exist, and that "Every value under them is unsourced."
        #      0.18 is one of those values.
        #   3. THE WINNER MEAN IS A COMPLEMENT TOO. rural_pct_mean 0.18 and
        #      urban_pct_mean 0.82 sum to exactly 1.000 across a population of
        #      award winners, which is arithmetic and not measurement — the
        #      same structural defect as the figure it was benchmarking.
        #   4. THERE IS NO QUESTION TO BENCHMARK. Question 22(c)/(d) asks what
        #      percentage of QLICIs the Applicant COMMITS to deploy in
        #      Non-Metropolitan Counties, and Question 22 is not scored in
        #      Phase I. Comparing a pipeline's current QEI share to a "winner
        #      mean" scores an Applicant against a number the Fund never asked
        #      them for. See renderers/_question_22.
        #
        # Fixing (1) alone would have left a more authoritative version of the
        # same misleading comparison, which is the outcome this ruling exists
        # to refuse. The non-metropolitan share survives as an unbenchmarked
        # characterisation on the CLI and the Streamlit tab, with its basis and
        # its nature named; what is gone is scoring a CDE against it.
        #
        # _weighted_score normalises by the weights actually present, so the
        # remaining eight metrics renormalise from 0.95 to 1.0 on their own and
        # no weight is retyped.

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
        note: str,
    ) -> MetricBenchmark:
        # NO FALLBACK BAND. Through 1.4.0 a metric absent from
        # WINNER_PATTERN_THRESHOLDS silently got bands of
        # ``winner_mean``, ``winner_mean * 0.7`` and ``winner_mean * 0.4`` —
        # two more unsourced constants, invisible because nothing reached them
        # (all eight metrics carry an entry). An armed-but-unreached default is
        # how the next metric added would have got invented bands with no
        # review, so it raises instead.
        thresholds = WINNER_PATTERN_THRESHOLDS.get(metric)
        if not thresholds:
            raise KeyError(
                f"no band is defined for metric {metric!r} in "
                "WINNER_PATTERN_THRESHOLDS. Add one there, with an entry in "
                "tests/scoring_attribution.txt saying where it came from — "
                "this used to fabricate bands from the winner mean instead."
            )
        t_strong = float(thresholds["strong"])
        t_competitive = float(thresholds["competitive"])
        t_weak = float(thresholds["weak"])

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

        return MetricBenchmark(
            metric=metric,
            label=label,
            value=value,
            tier=tier,
            score=score,
            threshold_strong=t_strong,
            threshold_competitive=t_competitive,
            threshold_weak=t_weak,
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

