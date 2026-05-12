"""Score consistency tests.

Catches the class of bug where two different code paths produce different
WinProbabilityScore values for the same application:

  - app.score_win_probability() — used at the top of Win Alignment Scorer
  - app.recommendations()       — used in the recommendations panel

Both must read from the same CDE attributes so that the section totals
cited in recommendation text match the numbers displayed at the top of the page.
"""
import sys
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.intelligence.recommendations import RecommendationEngine
from nmtcapp.intelligence.win_probability import WinProbabilityModel


@pytest.fixture(scope="module")
def sample_app():
    cde = CDEProfile.sample()
    pipeline = Pipeline.sample(n=20)
    app = Application(cde=cde, requested_allocation=65_000_000, application_round="CY2025")
    app.add_pipeline(pipeline)
    return app


class TestScoreConsistency:
    """score_win_probability() and the score used inside recommendations() must agree."""

    def test_section_totals_match(self, sample_app):
        """Bug 2 regression: recs used a score with no CDE attrs → wrong section totals."""
        displayed_score = sample_app.score_win_probability()
        recs = sample_app.recommendations()

        # The overall_assessment in the recommendations set should cite the SAME
        # aggregate and section totals as the displayed score.
        displayed_agg = displayed_score.aggregate_base_score
        displayed_bs = displayed_score.business_strategy["section_total"]
        displayed_co = displayed_score.community_outcomes["section_total"]

        # Extract numbers from the assessment string
        assert str(displayed_agg) in recs.overall_assessment, (
            f"Displayed aggregate {displayed_agg} not found in recommendations assessment: "
            f"{recs.overall_assessment!r}"
        )
        assert str(displayed_bs) in recs.overall_assessment, (
            f"Displayed BS total {displayed_bs} not found in recommendations assessment: "
            f"{recs.overall_assessment!r}"
        )
        assert str(displayed_co) in recs.overall_assessment, (
            f"Displayed CO total {displayed_co} not found in recommendations assessment: "
            f"{recs.overall_assessment!r}"
        )

    def test_no_false_gating_recs_for_qualified_app(self, sample_app):
        """The sample CDE is Highly Qualified — no gating recs should fire."""
        displayed_score = sample_app.score_win_probability()
        assert displayed_score.tier in ("Highly Qualified", "Top Tier"), (
            f"Sample CDE expected to be Highly Qualified or Top Tier, got {displayed_score.tier}"
        )

        recs = sample_app.recommendations()
        gating_recs = [
            r for r in recs.recommendations
            if "below the 40-point minimum" in r.finding
            and r.priority == "critical"
        ]
        assert len(gating_recs) == 0, (
            f"Gating recommendations fired for a {displayed_score.tier} app — "
            f"Bug 2 still present. Found: {[r.finding for r in gating_recs]}"
        )

    def test_prior_award_count_propagated(self, sample_app):
        """CDE attributes (prior awards) must propagate to recommendations' internal score."""
        recs_score = _internal_win_score(sample_app)
        direct_score = sample_app.score_win_probability()

        assert recs_score.business_strategy["track_record_strength"] == \
               direct_score.business_strategy["track_record_strength"], (
            "track_record_strength differs between the recommendations' internal score "
            "and score_win_probability() — CDE attributes not propagated in recommendations()"
        )

    def test_recommendation_engine_uses_passed_score(self, sample_app):
        """RecommendationEngine.recommend() must surface scores from the score object it receives."""
        analysis = sample_app.analyze()
        score = sample_app.score_win_probability()

        from nmtcapp.intelligence.benchmarks import HistoricalBenchmarks
        bc = HistoricalBenchmarks().compare(analysis.pipeline_result, sample_app.requested_allocation)
        recs = RecommendationEngine().recommend(analysis.pipeline_result, bc, score)

        # The assessment must cite the same aggregate as the score we passed
        assert str(score.aggregate_base_score) in recs.overall_assessment


class TestDemoModeLogic:
    """Verify is_demo_data session-state logic works as expected."""

    def test_no_cde_attrs_produces_lower_bs_score(self):
        """Sanity: omitting CDE attrs genuinely changes Business Strategy."""
        cde = CDEProfile.sample()
        pipeline = Pipeline.sample(n=20)
        app = Application(cde=cde, requested_allocation=65_000_000)
        app.add_pipeline(pipeline)

        score_with_attrs = app.score_win_probability()
        analysis = app.analyze()
        score_without_attrs = WinProbabilityModel().score(
            analysis.pipeline_result, app.requested_allocation
        )

        # The sample CDE has prior awards; without attrs, track record is 0
        bs_with = score_with_attrs.business_strategy["track_record_strength"]
        bs_without = score_without_attrs.business_strategy["track_record_strength"]
        assert bs_with > bs_without, (
            "Expected higher track_record_strength when CDE attributes are provided "
            f"(got {bs_with} vs {bs_without}) — CDE sample may have no prior awards"
        )

    def test_recommendations_consistent_with_score_win_probability(self):
        """End-to-end: recs and score_win_probability() must agree on BS/CO totals."""
        cde = CDEProfile.sample()
        pipeline = Pipeline.sample(n=20)
        app = Application(cde=cde, requested_allocation=65_000_000)
        app.add_pipeline(pipeline)

        score = app.score_win_probability()
        recs = app.recommendations()

        bs_from_score = score.business_strategy["section_total"]
        co_from_score = score.community_outcomes["section_total"]

        # The assessment text is built from the score object inside recommendations().
        # If they differ, the text will cite a different number than what's displayed.
        assert str(bs_from_score) in recs.overall_assessment, (
            f"BS total from score ({bs_from_score}) not in recommendations assessment. "
            f"This means recommendations() used a different WinProbabilityScore."
        )
        assert str(co_from_score) in recs.overall_assessment, (
            f"CO total from score ({co_from_score}) not in recommendations assessment."
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _internal_win_score(app: Application):
    """Reproduce what Application.recommendations() computes internally."""
    from nmtcapp.intelligence.win_probability import WinProbabilityModel
    analysis = app.analyze()
    cde_attributes = dict(app.cde.extra) if app.cde.extra else {}
    if "prior_award_count" not in cde_attributes:
        cde_attributes["prior_award_count"] = len(app.cde.prior_awards)
    return WinProbabilityModel().score(
        analysis.pipeline_result,
        app.requested_allocation,
        app.application_round,
        cde_attributes=cde_attributes,
    )
