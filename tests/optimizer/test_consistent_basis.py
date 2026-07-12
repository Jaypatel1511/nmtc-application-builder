"""H2: optimizer before/after must be scored on ONE component basis.

Auditor probe: with 6 verified + 2 unverified projects and a QEI cap, the
optimizer scored the full mixed pipeline WITHOUT the distress component
(auto-excluded) but scored the all-verified selected subset WITH it —
reporting +16.0 pts of "improvement" that was actually −6.8 on a consistent
basis. Every scoring call — before, greedy per-project ranking, local
search, after — must share the component basis computed ONCE from the full
input set.
"""
import pytest

import nmtcapp.optimizer.pipeline_optimizer as optimizer_mod
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.optimizer.constraints import OptimizationConstraints
from nmtcapp.optimizer.objectives import composite_alignment_score
from nmtcapp.optimizer.pipeline_optimizer import PipelineOptimizer

ALLOCATION = 40_000_000


def _verified(pid: str, state: str, sector: str, qei: float,
              jobs: int) -> PipelineProject:
    return PipelineProject(
        project_id=pid, project_name=f"Verified {pid}",
        qalicb_name=f"{pid} QALICB LLC", address="1 Main St", city="Town",
        state=state, sector=sector, project_type="real_estate",
        total_project_cost=qei * 1.4, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=jobs,
        census_tract="17031000100", is_nmtc_eligible=True,
        distress_level="deep", is_native_area=False,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )


def _unverified(pid: str, state: str, sector: str, qei: float,
                jobs: int) -> PipelineProject:
    p = PipelineProject(
        project_id=pid, project_name=f"Unverified {pid}",
        qalicb_name=f"{pid} QALICB LLC", address="1 Main St", city="Town",
        state=state, sector=sector, project_type="real_estate",
        total_project_cost=qei * 1.4, qei_request=qei, qlici_amount=qei,
        expected_jobs_created=jobs,
    )
    p.geocode_success = False
    return p


def _mixed_pipeline() -> Pipeline:
    """6 verified deep-distress + 2 unverified. QEI cap (below) excludes the
    two oversized unverified projects, so the selected subset is all-verified
    — exactly the configuration where an auto basis flips components."""
    return Pipeline([
        _verified("V-01", "IL", "healthcare", 6_000_000, 40),
        _verified("V-02", "TX", "education", 6_000_000, 35),
        _verified("V-03", "OH", "small_business", 6_000_000, 60),
        _verified("V-04", "TN", "healthcare", 6_000_000, 45),
        _verified("V-05", "GA", "mixed_use", 6_000_000, 30),
        _verified("V-06", "LA", "education", 6_000_000, 38),
        _unverified("U-01", "MT", "healthcare", 20_000_000, 10),
        _unverified("U-02", "WY", "education", 20_000_000, 8),
    ])


def _constraints() -> OptimizationConstraints:
    return OptimizationConstraints(max_total_qei=36_000_000)


def test_before_and_after_share_one_component_basis():
    pipeline = _mixed_pipeline()
    all_projects = list(pipeline)
    result = PipelineOptimizer().optimize(pipeline, _constraints(), ALLOCATION)

    assert result.score_is_partial is True

    # The input set contains unverified projects → the basis for EVERYTHING
    # is "without eligibility components", fixed once from the full input.
    expected_before = composite_alignment_score(
        all_projects, ALLOCATION, include_eligibility=False)
    expected_after = composite_alignment_score(
        result.selected_projects, ALLOCATION, include_eligibility=False)

    assert result.alignment_score_before == pytest.approx(expected_before, abs=1e-4)
    assert result.alignment_score_after == pytest.approx(expected_after, abs=1e-4)

    # The reported delta must equal the same-basis delta (this is the
    # assertion class that catches the auditor's +16.0-reported vs −6.8-actual)
    reported_delta = result.alignment_score_after - result.alignment_score_before
    assert reported_delta == pytest.approx(expected_after - expected_before, abs=2e-4)

    # Sanity: the selected subset really is all-verified, so an auto basis
    # WOULD have scored it differently — the mismatch this test guards against.
    assert all(p.is_nmtc_eligible is not None for p in result.selected_projects)
    auto_after = composite_alignment_score(result.selected_projects, ALLOCATION)
    assert auto_after != pytest.approx(expected_after, abs=1e-4)


def test_every_optimizer_scoring_call_uses_the_input_basis(monkeypatch):
    """Greedy ranking, local search, before AND after must all pass the
    basis computed once from the full input — never per-subset auto."""
    seen_bases = []
    real = composite_alignment_score

    def spy(projects, requested_allocation, weights=None, include_eligibility=None):
        seen_bases.append(include_eligibility)
        return real(projects, requested_allocation, weights,
                    include_eligibility=include_eligibility)

    monkeypatch.setattr(optimizer_mod, "composite_alignment_score", spy)

    PipelineOptimizer().optimize(_mixed_pipeline(), _constraints(), ALLOCATION)

    assert seen_bases, "optimizer never called composite_alignment_score"
    assert all(basis is False for basis in seen_bases), (
        f"scoring calls used mixed bases: {set(seen_bases)}"
    )


def test_greedy_ranks_verified_and_unverified_twins_on_same_scale():
    """Two projects identical except for eligibility fields must receive the
    same per-project score under the shared (no-eligibility) basis."""
    verified_twin = _verified("T-01", "IL", "healthcare", 6_000_000, 40)
    unverified_twin = _unverified("T-02", "IL", "healthcare", 6_000_000, 40)
    s_verified = composite_alignment_score(
        [verified_twin], ALLOCATION, include_eligibility=False)
    s_unverified = composite_alignment_score(
        [unverified_twin], ALLOCATION, include_eligibility=False)
    assert s_verified == pytest.approx(s_unverified)


def test_include_eligibility_none_preserves_auto_behavior():
    """Back-compat: omitting include_eligibility (or passing None) keeps the
    existing auto behavior for external callers."""
    verified_only = [
        _verified("V-01", "IL", "healthcare", 6_000_000, 40),
        _verified("V-02", "TX", "education", 6_000_000, 35),
    ]
    auto = composite_alignment_score(verified_only, ALLOCATION)
    explicit_none = composite_alignment_score(
        verified_only, ALLOCATION, include_eligibility=None)
    with_elig = composite_alignment_score(
        verified_only, ALLOCATION, include_eligibility=True)
    assert auto == pytest.approx(explicit_none)
    assert auto == pytest.approx(with_elig)  # all verified → auto includes
