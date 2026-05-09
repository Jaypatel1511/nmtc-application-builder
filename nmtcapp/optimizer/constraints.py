"""Constraint definitions for the NMTC pipeline optimizer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import PipelineProject


@dataclass
class OptimizationConstraints:
    """Constraints that the optimizer must respect when selecting a project subset.

    All constraints are soft-checked: the optimizer tries to satisfy them and
    reports any violations in :attr:`~OptimizationResult.infeasibility_reason`.

    Example::

        from nmtcapp.optimizer.constraints import OptimizationConstraints
        constraints = OptimizationConstraints(
            min_total_qei=40_000_000,
            max_total_qei=65_000_000,
            min_projects=10,
            min_states=5,
        )
    """
    min_total_qei: float = 0.0
    max_total_qei: float = float("inf")
    min_projects: int = 1
    max_projects: int = 9999
    required_sectors: List[str] = field(default_factory=list)
    excluded_states: List[str] = field(default_factory=list)
    min_distress_pct: float = 0.0        # minimum % deep/severe distress required
    min_states: int = 1
    max_single_sector_pct: float = 1.0   # max fraction of QEI in one sector
    min_rural_pct: float = 0.0           # minimum rural QEI fraction
    min_eligibility_pct: float = 0.0     # minimum % of projects that are eligible

    def is_feasible(self, projects: List["PipelineProject"]) -> tuple[bool, str]:
        """Check whether a candidate project list satisfies all constraints.

        Args:
            projects: Candidate list of :class:`~nmtcapp.core.pipeline.PipelineProject`.

        Returns:
            ``(True, "")`` if all constraints are satisfied, or
            ``(False, reason_string)`` with the first violated constraint.

        Example::

            ok, reason = constraints.is_feasible(project_list)
            if not ok:
                print(f"Infeasible: {reason}")
        """
        if not projects:
            return False, "No projects selected"

        total_qei = sum(p.qei_request for p in projects)
        n = len(projects)

        if total_qei < self.min_total_qei:
            return False, (
                f"Total QEI ${total_qei:,.0f} < minimum ${self.min_total_qei:,.0f}"
            )
        if total_qei > self.max_total_qei:
            return False, (
                f"Total QEI ${total_qei:,.0f} > maximum ${self.max_total_qei:,.0f}"
            )
        if n < self.min_projects:
            return False, f"{n} projects < minimum {self.min_projects}"
        if n > self.max_projects:
            return False, f"{n} projects > maximum {self.max_projects}"

        # Required sectors
        if self.required_sectors:
            present = {p.sector for p in projects}
            missing = [s for s in self.required_sectors if s not in present]
            if missing:
                return False, f"Required sectors missing: {', '.join(missing)}"

        # Excluded states
        if self.excluded_states:
            bad = [p.state for p in projects if p.state in self.excluded_states]
            if bad:
                return False, f"Projects in excluded state(s): {set(bad)}"

        # States count
        states = len({p.state for p in projects})
        if states < self.min_states:
            return False, f"{states} states < minimum {self.min_states}"

        return True, ""
