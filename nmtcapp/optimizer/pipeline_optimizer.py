"""
NMTC pipeline optimizer using greedy construction + swap-based local search.

The objective is to maximize composite alignment with historical winner patterns
subject to the constraints defined in :class:`~nmtcapp.optimizer.constraints.OptimizationConstraints`.

Implementation notes:
- No LP/MIP solver dependency; uses pure-Python greedy + local search.
- Greedy phase: score each project individually, add greedily until QEI cap or
  project cap is reached.
- Local search phase: try pairwise swaps (one out, one in); accept if the
  composite score improves.
- Infeasible constraints are reported gracefully — no exception is raised.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from nmtcapp.optimizer.candidate_pool import CandidatePool
from nmtcapp.optimizer.constraints import OptimizationConstraints
from nmtcapp.optimizer.objectives import (
    DEFAULT_WEIGHTS,
    composite_alignment_score,
    score_distress_alignment,
    score_geographic_alignment,
    score_impact_alignment,
    score_pipeline_quality,
    score_sector_alignment,
)

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline, PipelineProject

logger = logging.getLogger(__name__)

_METHODOLOGY = (
    "Pipeline optimized using greedy construction (projects ranked by individual "
    "alignment contribution) followed by swap-based local search. Objective: maximize "
    "composite alignment score with historical NMTC winner patterns (CY2020–CY2024). "
    "Subject to QEI budget, project count, state diversity, and sector constraints. "
    "Alignment score ≠ win probability — see WinProbabilityModel for framing guidance."
)


@dataclass
class OptimizationResult:
    """Result from PipelineOptimizer.optimize().

    Example::

        result = PipelineOptimizer().optimize(pipeline, constraints, 55_000_000)
        print(f"Score improved: {result.alignment_score_before:.2f} → {result.alignment_score_after:.2f}")
    """
    selected_projects: List["PipelineProject"]
    objective_score: float           # composite alignment score of selected set [0, 1]
    alignment_score_before: float    # score of original full pipeline
    alignment_score_after: float     # score of optimized subset
    constraints_satisfied: bool
    infeasibility_reason: str        # empty string if feasible
    dimensional_improvements: Dict[str, float]  # per-dimension delta
    iterations: int
    methodology_note: str = field(default=_METHODOLOGY)

    def summary(self) -> str:
        """Return a formatted optimization result report."""
        lines = [
            "=" * 68,
            "  PIPELINE OPTIMIZATION RESULT",
            f"  Projects selected:    {len(self.selected_projects)}",
            f"  Total QEI:            ${sum(p.qei_request for p in self.selected_projects):,.0f}",
            f"  Alignment (before):   {self.alignment_score_before * 100:.1f} / 100",
            f"  Alignment (after):    {self.alignment_score_after * 100:.1f} / 100",
            f"  Improvement:          {(self.alignment_score_after - self.alignment_score_before) * 100:+.1f} pts",
            f"  Constraints met:      {'Yes' if self.constraints_satisfied else 'No'}",
        ]
        if not self.constraints_satisfied:
            lines.append(f"  Infeasibility:        {self.infeasibility_reason}")
        lines.append(f"  Search iterations:    {self.iterations}")
        lines.append("")
        lines.append("  Dimensional Improvements:")
        for dim, delta in self.dimensional_improvements.items():
            arrow = "+" if delta >= 0 else ""
            lines.append(f"    {dim.replace('_', ' ').title():<30} {arrow}{delta * 100:.1f} pts")
        lines.extend(["", f"  NOTE: {self.methodology_note[:120]}...", "=" * 68])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "selected_project_ids": [p.project_id for p in self.selected_projects],
            "objective_score": self.objective_score,
            "alignment_score_before": self.alignment_score_before,
            "alignment_score_after": self.alignment_score_after,
            "constraints_satisfied": self.constraints_satisfied,
            "infeasibility_reason": self.infeasibility_reason,
            "dimensional_improvements": self.dimensional_improvements,
            "iterations": self.iterations,
            "methodology_note": self.methodology_note,
        }


class PipelineOptimizer:
    """Optimize a NMTC pipeline subset to maximize alignment with historical winners.

    Uses greedy construction followed by swap-based local search. Pure-Python
    implementation; no LP/MIP solver required.

    Example::

        from nmtcapp.optimizer import PipelineOptimizer, OptimizationConstraints
        constraints = OptimizationConstraints(
            min_total_qei=40_000_000,
            max_total_qei=65_000_000,
            min_projects=10,
            min_states=5,
        )
        result = PipelineOptimizer().optimize(pipeline, constraints, 55_000_000)
        print(result.summary())
    """

    def __init__(
        self,
        max_iterations: int = 500,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.max_iterations = max_iterations
        self.weights = weights or DEFAULT_WEIGHTS

    def optimize(
        self,
        pipeline: "Pipeline",
        constraints: OptimizationConstraints,
        requested_allocation: float,
    ) -> OptimizationResult:
        """Run the optimization.

        Args:
            pipeline: Source :class:`~nmtcapp.core.pipeline.Pipeline` to draw projects from.
            constraints: :class:`~nmtcapp.optimizer.constraints.OptimizationConstraints`.
            requested_allocation: Requested allocation amount in dollars.

        Returns:
            :class:`OptimizationResult` — always returns, even if constraints are infeasible.

        Example::

            result = PipelineOptimizer().optimize(pipeline, constraints, 55_000_000)
        """
        all_projects = list(pipeline)
        score_before = composite_alignment_score(all_projects, requested_allocation, self.weights)

        pool = CandidatePool.from_pipeline(pipeline).filter(constraints)
        candidates = pool.projects

        if len(candidates) == 0:
            return self._infeasible_result(
                all_projects, score_before, "No projects remain after applying constraints"
            )

        logger.info("Optimizer starting: %d candidates, max_iter=%d", len(candidates), self.max_iterations)

        # --- Phase 1: Greedy construction ---
        selected = self._greedy_construct(candidates, constraints, requested_allocation)

        if not selected:
            return self._infeasible_result(
                all_projects, score_before,
                "Greedy construction failed — constraints may be infeasible for this pipeline"
            )

        # --- Phase 2: Swap-based local search ---
        selected, iters = self._local_search(selected, candidates, constraints, requested_allocation)

        # Check feasibility
        ok, reason = constraints.is_feasible(selected)

        score_after = composite_alignment_score(selected, requested_allocation, self.weights)

        # Dimensional improvements
        def _dims(projects):
            return {
                "distress": score_distress_alignment(projects, requested_allocation),
                "geographic": score_geographic_alignment(projects),
                "impact": score_impact_alignment(projects, requested_allocation),
                "sector": score_sector_alignment(projects),
                "pipeline": score_pipeline_quality(projects, requested_allocation),
            }

        dims_before = _dims(all_projects)
        dims_after = _dims(selected)
        dimensional_improvements = {k: dims_after[k] - dims_before[k] for k in dims_before}

        logger.info(
            "Optimizer complete: %d projects selected, score %.3f → %.3f, %d iterations",
            len(selected), score_before, score_after, iters,
        )

        return OptimizationResult(
            selected_projects=selected,
            objective_score=round(score_after, 4),
            alignment_score_before=round(score_before, 4),
            alignment_score_after=round(score_after, 4),
            constraints_satisfied=ok,
            infeasibility_reason=reason,
            dimensional_improvements={k: round(v, 4) for k, v in dimensional_improvements.items()},
            iterations=iters,
        )

    # ------------------------------------------------------------------
    # Internal optimization phases
    # ------------------------------------------------------------------

    def _greedy_construct(
        self,
        candidates: List["PipelineProject"],
        constraints: OptimizationConstraints,
        requested_allocation: float,
    ) -> List["PipelineProject"]:
        """Greedy construction: add projects in descending per-project score order."""
        def _per_project_score(p: "PipelineProject") -> float:
            return composite_alignment_score([p], requested_allocation, self.weights)

        ranked = sorted(candidates, key=_per_project_score, reverse=True)
        selected: List["PipelineProject"] = []
        total_qei = 0.0

        for p in ranked:
            if len(selected) >= constraints.max_projects:
                break
            if total_qei + p.qei_request > constraints.max_total_qei:
                continue
            selected.append(p)
            total_qei += p.qei_request

        # Enforce required sectors: append lowest-cost project from each missing sector
        if constraints.required_sectors:
            present = {p.sector for p in selected}
            for req_sector in constraints.required_sectors:
                if req_sector not in present:
                    candidates_in_sector = [p for p in candidates if p.sector == req_sector]
                    if candidates_in_sector:
                        best = min(candidates_in_sector, key=lambda p: p.qei_request)
                        if total_qei + best.qei_request <= constraints.max_total_qei:
                            selected.append(best)
                            total_qei += best.qei_request
                            present.add(req_sector)

        return selected

    def _local_search(
        self,
        selected: List["PipelineProject"],
        candidates: List["PipelineProject"],
        constraints: OptimizationConstraints,
        requested_allocation: float,
    ) -> tuple[List["PipelineProject"], int]:
        """Swap-based local search: try replacing one project at a time."""
        not_selected = [p for p in candidates if p not in selected]
        best_score = composite_alignment_score(selected, requested_allocation, self.weights)
        iters = 0

        for _ in range(self.max_iterations):
            improved = False
            for i, out_proj in enumerate(list(selected)):
                for in_proj in not_selected:
                    # Try swap: remove out_proj, add in_proj
                    candidate_set = [p for j, p in enumerate(selected) if j != i] + [in_proj]
                    total_qei = sum(p.qei_request for p in candidate_set)
                    if total_qei > constraints.max_total_qei:
                        continue
                    if total_qei < constraints.min_total_qei and len(candidate_set) < constraints.min_projects:
                        continue
                    new_score = composite_alignment_score(candidate_set, requested_allocation, self.weights)
                    if new_score > best_score + 1e-6:
                        selected = candidate_set
                        not_selected = [p for p in candidates if p not in selected]
                        best_score = new_score
                        improved = True
                        iters += 1
                        break
                if improved:
                    break
            if not improved:
                break

        return selected, iters

    def _infeasible_result(
        self,
        original: List["PipelineProject"],
        score_before: float,
        reason: str,
    ) -> OptimizationResult:
        return OptimizationResult(
            selected_projects=original,
            objective_score=round(score_before, 4),
            alignment_score_before=round(score_before, 4),
            alignment_score_after=round(score_before, 4),
            constraints_satisfied=False,
            infeasibility_reason=reason,
            dimensional_improvements={},
            iterations=0,
        )
