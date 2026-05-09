"""Candidate pool management for the NMTC pipeline optimizer."""
from __future__ import annotations

import random
from typing import Callable, List, Optional, TYPE_CHECKING

from nmtcapp.optimizer.constraints import OptimizationConstraints

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline, PipelineProject


class CandidatePool:
    """Manages a pool of candidate projects for optimization.

    Supports filtering by constraints, scoring, and random sampling.

    Example::

        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(pipeline)
        filtered = pool.filter(constraints)
        top = filtered.top_by_score(10, score_fn)
    """

    def __init__(self, projects: List["PipelineProject"]) -> None:
        self._projects = list(projects)

    @classmethod
    def from_pipeline(cls, pipeline: "Pipeline") -> "CandidatePool":
        """Build a pool from all projects in a Pipeline.

        Example::

            pool = CandidatePool.from_pipeline(pipeline)
        """
        return cls(list(pipeline))

    @property
    def projects(self) -> List["PipelineProject"]:
        return list(self._projects)

    def __len__(self) -> int:
        return len(self._projects)

    def filter(self, constraints: OptimizationConstraints) -> "CandidatePool":
        """Remove projects that violate hard per-project constraints.

        Filters out projects in excluded states. Other constraints (total QEI,
        project count) are checked at the portfolio level, not per-project.

        Args:
            constraints: :class:`~nmtcapp.optimizer.constraints.OptimizationConstraints`.

        Returns:
            New :class:`CandidatePool` with ineligible projects removed.

        Example::

            eligible_pool = pool.filter(constraints)
        """
        kept = [
            p for p in self._projects
            if p.state not in constraints.excluded_states
        ]
        return CandidatePool(kept)

    def top_by_score(
        self,
        n: int,
        score_fn: Callable[["PipelineProject"], float],
    ) -> List["PipelineProject"]:
        """Return the top-n projects ranked by a per-project score function.

        Args:
            n: Number of projects to return.
            score_fn: Callable that takes a PipelineProject and returns a float.

        Returns:
            List of up to n projects in descending score order.

        Example::

            top10 = pool.top_by_score(10, lambda p: p.qei_request)
        """
        scored = sorted(self._projects, key=score_fn, reverse=True)
        return scored[:n]

    def sample_random(
        self,
        n: int,
        seed: Optional[int] = None,
    ) -> List["PipelineProject"]:
        """Return a random sample of n projects without replacement.

        Args:
            n: Number of projects to sample.
            seed: Optional random seed for reproducibility.

        Returns:
            List of up to min(n, len(pool)) projects.

        Example::

            sample = pool.sample_random(8, seed=42)
        """
        rng = random.Random(seed)
        k = min(n, len(self._projects))
        return rng.sample(self._projects, k)

    def eligible_only(self) -> "CandidatePool":
        """Return a pool containing only NMTC-eligible projects.

        Example::

            eligible_pool = pool.eligible_only()
        """
        eligible = [p for p in self._projects if getattr(p, "is_nmtc_eligible", True)]
        return CandidatePool(eligible)
