"""
Smoke test: cde_profile_sample.yaml must score within ±2 points of its documented values.

Catches drift between the YAML calibration comments and the actual scoring model output.
"""
from pathlib import Path

from nmtcapp import Application, Pipeline
from nmtcapp.core.cde import CDEProfile

YAML_PATH = Path(__file__).parent.parent / "templates" / "cde_profile_sample.yaml"
TOLERANCE = 2

# Documented in cde_profile_sample.yaml calibration comment block
DOCUMENTED = {
    "business_strategy": 43,   # / 50
    "community_outcomes": 47,  # / 50
    "priority_points": 9,      # / 10
    "aggregate": 90,           # / 100
}


def _make_score():
    cde = CDEProfile.from_yaml(str(YAML_PATH))
    app = Application(cde=cde, requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    return app.score_win_probability()


def test_yaml_business_strategy_score():
    score = _make_score()
    actual = score.business_strategy.get("section_total", -1)
    assert abs(actual - DOCUMENTED["business_strategy"]) <= TOLERANCE, (
        f"Business Strategy: got {actual}/50, documented as {DOCUMENTED['business_strategy']}/50 ± {TOLERANCE}. "
        "Update cde_profile_sample.yaml calibration comment if intentional."
    )


def test_yaml_community_outcomes_score():
    score = _make_score()
    actual = score.community_outcomes.get("section_total", -1)
    assert abs(actual - DOCUMENTED["community_outcomes"]) <= TOLERANCE, (
        f"Community Outcomes: got {actual}/50, documented as {DOCUMENTED['community_outcomes']}/50 ± {TOLERANCE}. "
        "Update cde_profile_sample.yaml calibration comment if intentional."
    )


def test_yaml_priority_points_score():
    score = _make_score()
    actual = score.priority_points.get("section_total", -1)
    assert abs(actual - DOCUMENTED["priority_points"]) <= TOLERANCE, (
        f"Priority Points: got {actual}/10, documented as {DOCUMENTED['priority_points']}/10 ± {TOLERANCE}. "
        "Update cde_profile_sample.yaml calibration comment if intentional."
    )


def test_yaml_aggregate_score():
    score = _make_score()
    actual = score.aggregate_base_score
    assert abs(actual - DOCUMENTED["aggregate"]) <= TOLERANCE, (
        f"Aggregate base score: got {actual}/100, documented as {DOCUMENTED['aggregate']}/100 ± {TOLERANCE}. "
        "Update cde_profile_sample.yaml calibration comment if intentional."
    )


def test_yaml_tier_is_qualified():
    score = _make_score()
    assert score.tier in ("Highly Qualified", "Top Tier"), (
        f"cde_profile_sample.yaml expected Highly Qualified or Top Tier, got '{score.tier}'. "
        "Update calibration comment if intentional."
    )
