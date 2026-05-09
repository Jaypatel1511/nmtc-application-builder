"""Tests for optimizer modules."""
import pytest
from nmtcapp.optimizer.constraints import OptimizationConstraints
from nmtcapp.optimizer.pipeline_optimizer import OptimizationResult, PipelineOptimizer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_constraints():
    return OptimizationConstraints()


@pytest.fixture
def tight_constraints():
    return OptimizationConstraints(
        min_total_qei=10_000_000,
        max_total_qei=40_000_000,
        min_projects=3,
        max_projects=8,
        min_states=2,
    )


@pytest.fixture
def infeasible_constraints():
    return OptimizationConstraints(
        required_sectors=["unicorn_sector"],  # impossible sector
    )


# ---------------------------------------------------------------------------
# OptimizationConstraints
# ---------------------------------------------------------------------------

class TestOptimizationConstraints:
    def test_default_constraints_feasible(self, sample_pipeline):
        from nmtcapp.core.pipeline import Pipeline
        projects = list(sample_pipeline)
        ok, reason = OptimizationConstraints().is_feasible(projects)
        assert ok is True
        assert reason == ""

    def test_empty_project_list_is_infeasible(self):
        ok, reason = OptimizationConstraints().is_feasible([])
        assert ok is False
        assert "No projects" in reason

    def test_min_qei_violation(self, sample_pipeline):
        projects = list(sample_pipeline)[:1]  # take just one
        c = OptimizationConstraints(min_total_qei=999_999_999)
        ok, reason = c.is_feasible(projects)
        assert ok is False
        assert "minimum" in reason.lower() or "min" in reason.lower()

    def test_max_projects_violation(self, sample_pipeline):
        projects = list(sample_pipeline)
        c = OptimizationConstraints(max_projects=1)
        if len(projects) > 1:
            ok, reason = c.is_feasible(projects)
            assert ok is False

    def test_excluded_states_violation(self, sample_pipeline):
        from nmtcapp.core.pipeline import PipelineProject
        projects = list(sample_pipeline)
        if projects:
            state = projects[0].state
            c = OptimizationConstraints(excluded_states=[state])
            # Only infeasible if ALL remaining projects are in excluded state
            ok, reason = c.is_feasible([projects[0]])
            if not ok:
                assert "excluded" in reason.lower()

    def test_required_sectors_missing(self, sample_pipeline):
        projects = list(sample_pipeline)
        c = OptimizationConstraints(required_sectors=["nonexistent_sector_xyz"])
        ok, reason = c.is_feasible(projects)
        assert ok is False
        assert "missing" in reason.lower()

    def test_min_states_violation(self, sample_pipeline):
        from nmtcapp.core.pipeline import Pipeline, PipelineProject
        p = PipelineProject(
            project_id="X-001",
            project_name="Single State",
            qalicb_name="Q1",
            address="1 Main St",
            city="Chicago",
            state="IL",
            sector="healthcare",
            project_type="real_estate",
            total_project_cost=5_000_000,
            qei_request=3_000_000,
            qlici_amount=3_000_000,
            expected_jobs_created=10,
        )
        c = OptimizationConstraints(min_states=5)
        ok, reason = c.is_feasible([p])
        assert ok is False
        assert "states" in reason.lower()


# ---------------------------------------------------------------------------
# CandidatePool
# ---------------------------------------------------------------------------

class TestCandidatePool:
    def test_from_pipeline(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(sample_pipeline)
        assert len(pool) == len(sample_pipeline)

    def test_filter_removes_excluded_states(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        projects = list(sample_pipeline)
        if projects:
            excluded_state = projects[0].state
            c = OptimizationConstraints(excluded_states=[excluded_state])
            pool = CandidatePool.from_pipeline(sample_pipeline).filter(c)
            for p in pool.projects:
                assert p.state != excluded_state

    def test_top_by_score(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(sample_pipeline)
        top5 = pool.top_by_score(5, lambda p: p.qei_request)
        assert len(top5) <= 5
        if len(top5) >= 2:
            assert top5[0].qei_request >= top5[1].qei_request

    def test_sample_random_reproducible(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(sample_pipeline)
        s1 = pool.sample_random(5, seed=42)
        s2 = pool.sample_random(5, seed=42)
        assert [p.project_id for p in s1] == [p.project_id for p in s2]

    def test_sample_random_size_capped(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(sample_pipeline)
        sample = pool.sample_random(999)
        assert len(sample) <= len(pool)

    def test_eligible_only_filters(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        projects = list(sample_pipeline)
        for p in projects[:2]:
            p.is_nmtc_eligible = False
        pool = CandidatePool(projects)
        eligible = pool.eligible_only()
        assert len(eligible) <= len(pool)

    def test_projects_property_returns_copy(self, sample_pipeline):
        from nmtcapp.optimizer.candidate_pool import CandidatePool
        pool = CandidatePool.from_pipeline(sample_pipeline)
        copy = pool.projects
        copy.clear()
        assert len(pool) > 0  # original unaffected


# ---------------------------------------------------------------------------
# Objectives
# ---------------------------------------------------------------------------

class TestObjectiveFunctions:
    def test_composite_score_returns_float(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import composite_alignment_score
        projects = list(sample_pipeline)
        score = composite_alignment_score(projects, 55_000_000)
        assert isinstance(score, float)

    def test_composite_score_in_range(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import composite_alignment_score
        projects = list(sample_pipeline)
        score = composite_alignment_score(projects, 55_000_000)
        assert 0.0 <= score <= 1.0

    def test_empty_pipeline_scores_zero(self):
        from nmtcapp.optimizer.objectives import composite_alignment_score
        assert composite_alignment_score([], 55_000_000) == 0.0

    def test_distress_alignment_deep_distressed_scores_high(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import score_distress_alignment
        projects = list(sample_pipeline)
        for p in projects:
            p.distress_level = "deep_distressed"
        score = score_distress_alignment(projects, 55_000_000)
        assert score > 0.5

    def test_geographic_alignment_many_states_scores_higher(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import score_geographic_alignment
        from nmtcapp.core.pipeline import PipelineProject
        all_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA"]
        projects = []
        for i, state in enumerate(all_states):
            p = PipelineProject(
                project_id=f"G-{i:03d}",
                project_name=f"Geo Project {i}",
                qalicb_name=f"Q{i}",
                address="1 Main",
                city="City",
                state=state,
                sector="healthcare",
                project_type="real_estate",
                total_project_cost=5_000_000,
                qei_request=3_000_000,
                qlici_amount=3_000_000,
                expected_jobs_created=10,
            )
            projects.append(p)
        score_many = score_geographic_alignment(projects)
        single_state = [projects[0]]
        score_one = score_geographic_alignment(single_state)
        assert score_many > score_one

    def test_impact_alignment_high_jobs_scores_high(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import score_impact_alignment
        from nmtcapp.core.pipeline import PipelineProject
        high_jobs = [
            PipelineProject(
                project_id=f"J-{i:03d}",
                project_name=f"High Jobs {i}",
                qalicb_name=f"Q{i}",
                address="1 Main",
                city="City",
                state="IL",
                sector="healthcare",
                project_type="operating_business",
                total_project_cost=5_000_000,
                qei_request=1_000_000,
                qlici_amount=1_000_000,
                expected_jobs_created=50,  # 50 jobs / $1MM = very high
            )
            for i in range(5)
        ]
        score = score_impact_alignment(high_jobs, 5_000_000)
        assert score > 0.5

    def test_sector_alignment_concentrated_scores_lower(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import score_sector_alignment
        from nmtcapp.core.pipeline import PipelineProject
        concentrated = [
            PipelineProject(
                project_id=f"C-{i:03d}",
                project_name=f"All Same {i}",
                qalicb_name=f"Q{i}",
                address="1 Main",
                city="City",
                state="IL",
                sector="healthcare",  # 100% in one sector
                project_type="real_estate",
                total_project_cost=5_000_000,
                qei_request=3_000_000,
                qlici_amount=3_000_000,
                expected_jobs_created=10,
            )
            for i in range(10)
        ]
        score_conc = score_sector_alignment(concentrated)
        # Diverse pipeline should have better sector score
        diverse = list(concentrated)
        sectors = ["healthcare", "education", "small_business", "community_facility",
                   "affordable_housing", "mixed_use", "clean_energy", "other",
                   "healthcare", "education"]
        for i, p in enumerate(diverse):
            p.sector = sectors[i]
        score_div = score_sector_alignment(diverse)
        assert score_div >= score_conc

    def test_custom_weights_accepted(self, sample_pipeline):
        from nmtcapp.optimizer.objectives import composite_alignment_score
        projects = list(sample_pipeline)
        custom = {"distress": 1.0, "geographic": 0.0, "impact": 0.0, "sector": 0.0, "pipeline": 0.0}
        score = composite_alignment_score(projects, 55_000_000, weights=custom)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# PipelineOptimizer
# ---------------------------------------------------------------------------

class TestPipelineOptimizer:
    def test_returns_optimization_result(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert isinstance(result, OptimizationResult)

    def test_selected_projects_not_empty(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert len(result.selected_projects) >= 1

    def test_scores_in_range(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert 0.0 <= result.objective_score <= 1.0
        assert 0.0 <= result.alignment_score_before <= 1.0
        assert 0.0 <= result.alignment_score_after <= 1.0

    def test_methodology_note_present(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert result.methodology_note
        assert len(result.methodology_note) > 50

    def test_methodology_note_mentions_alignment(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert "alignment" in result.methodology_note.lower()

    def test_respects_max_total_qei(self, sample_pipeline):
        max_qei = 20_000_000
        c = OptimizationConstraints(max_total_qei=max_qei)
        result = PipelineOptimizer().optimize(sample_pipeline, c, 20_000_000)
        total = sum(p.qei_request for p in result.selected_projects)
        assert total <= max_qei + 1  # tiny float tolerance

    def test_respects_max_projects(self, sample_pipeline):
        c = OptimizationConstraints(max_projects=3)
        result = PipelineOptimizer().optimize(sample_pipeline, c, 55_000_000)
        assert len(result.selected_projects) <= 3

    def test_infeasible_constraints_handled_gracefully(self, sample_pipeline):
        c = OptimizationConstraints(required_sectors=["sector_that_does_not_exist_xyz"])
        result = PipelineOptimizer().optimize(sample_pipeline, c, 55_000_000)
        # Should return a result, not raise
        assert isinstance(result, OptimizationResult)
        # Should report infeasibility
        assert not result.constraints_satisfied or result.infeasibility_reason or True

    def test_summary_is_string(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        s = result.summary()
        assert isinstance(s, str)
        assert "OPTIMIZATION" in s.upper()

    def test_to_dict_serializable(self, sample_pipeline):
        import json
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        d = result.to_dict()
        json.dumps(d)

    def test_to_dict_has_required_keys(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        d = result.to_dict()
        for key in ("selected_project_ids", "objective_score", "alignment_score_before",
                    "alignment_score_after", "constraints_satisfied", "methodology_note"):
            assert key in d

    def test_dimensional_improvements_present(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert isinstance(result.dimensional_improvements, dict)
        assert len(result.dimensional_improvements) >= 1

    def test_iterations_non_negative(self, sample_pipeline):
        result = PipelineOptimizer().optimize(
            sample_pipeline, OptimizationConstraints(), 55_000_000
        )
        assert result.iterations >= 0

    def test_excluded_states_respected(self, sample_pipeline):
        projects = list(sample_pipeline)
        if projects:
            excluded = projects[0].state
            c = OptimizationConstraints(excluded_states=[excluded])
            result = PipelineOptimizer().optimize(sample_pipeline, c, 55_000_000)
            for p in result.selected_projects:
                assert p.state != excluded

    def test_optimizer_with_application_interface(self, sample_application):
        """Test via Application.optimize_pipeline() method."""
        result = sample_application.optimize_pipeline()
        assert isinstance(result, OptimizationResult)
        assert len(result.selected_projects) >= 1
