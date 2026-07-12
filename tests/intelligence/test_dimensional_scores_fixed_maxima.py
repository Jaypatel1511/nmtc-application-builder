"""H3: dimensional_scores must divide by FIXED structural maxima (50/50/10).

In degraded mode Community Outcomes' ``max_available`` shrinks to 25 (the two
distress components cannot be assessed). Dividing the section total by
max_available inflated a degraded 20/25 into 80.0 on the 0–100 dimensional
scale — as if the CDE had scored 40/50. On the structural scale the honest
value is 40.0: 20 points earned out of a 50-point section.
"""
import pytest

from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
from nmtcapp.intelligence.win_probability import WinProbabilityModel


def _degraded_result(distress_breakdown=None) -> PipelineAnalysisResult:
    return PipelineAnalysisResult(
        total_projects=5,
        total_qei_request=30_000_000,
        total_project_cost=42_000_000,
        eligibility_pct=0.0,
        distress_breakdown=distress_breakdown or {},
        geographic_diversity={"states_count": 4, "rural_pct": 0.1},
        sector_mix={},
        aggregate_impact={"jobs_per_million_qei": 12.0},
        deal_economics_summary={},
        eligibility_data_status="unavailable",
        eligibility_data_error="CDFI Fund download failed",
    )


def test_degraded_community_outcomes_uses_structural_max():
    """Degraded CO 20/25 must map to 40.0 (of the structural 50), not 80.0."""
    # coq=9 (third-party validation), ca=10 (0.44 board + engagement),
    # st=1 (8% native area) → co_total = 20 with hdt/ddc excluded (None).
    attrs = {
        "has_quantified_outcomes": True,
        "has_third_party_validation": True,
        "lic_board_representation_pct": 0.44,
        "has_community_engagement_track_record": True,
    }
    result = _degraded_result(distress_breakdown={"pct_native_area": 0.08})
    score = WinProbabilityModel().score(result, 55_000_000, cde_attributes=attrs)

    assert score.partial is True
    assert score.community_outcomes["section_total"] == 20
    assert score.community_outcomes["max_available"] == 25
    assert score.dimensional_scores["community_outcomes"] == 40.0


def test_dimensional_scores_structural_maxima_all_sections():
    result = _degraded_result()
    score = WinProbabilityModel().score(result, 55_000_000)
    bs_total = score.business_strategy["section_total"]
    co_total = score.community_outcomes["section_total"]
    pp_total = score.priority_points["section_total"]
    assert score.dimensional_scores["business_strategy"] == round(bs_total / 50 * 100, 1)
    assert score.dimensional_scores["community_outcomes"] == round(co_total / 50 * 100, 1)
    assert score.dimensional_scores["priority_points"] == round(pp_total / 10 * 100, 1)


def test_non_degraded_dimensional_scores_unchanged():
    """Healthy runs already divide by 50/50/10 — behavior must not shift."""
    from nmtcapp.core.application import Application
    from nmtcapp.core.cde import CDEProfile
    from nmtcapp.core.pipeline import Pipeline

    app = Application(cde=CDEProfile.sample(), requested_allocation=55_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    score = app.score_win_probability()
    assert score.partial is False
    assert score.dimensional_scores["community_outcomes"] == round(
        score.community_outcomes["section_total"] / 50 * 100, 1
    )
