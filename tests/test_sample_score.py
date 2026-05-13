"""
Smoke test: CDEProfile.sample() must score within ±2 points of the documented value.

This catches future drift when scoring model weights change but the README
quickstart comment is not updated.
"""
from nmtcapp import Application, CDEProfile, Pipeline

DOCUMENTED_COMPOSITE = 90  # README quickstart comment: "90/100 [Highly Qualified]"
TOLERANCE = 2


def test_sample_cde_composite_score():
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    score = app.score_win_probability()
    assert abs(score.composite_score - DOCUMENTED_COMPOSITE) <= TOLERANCE, (
        f"CDEProfile.sample() composite score drifted: got {score.composite_score}, "
        f"documented as {DOCUMENTED_COMPOSITE} ± {TOLERANCE}. "
        "Update README quickstart comment if this is intentional."
    )


def test_sample_cde_tier():
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    score = app.score_win_probability()
    assert score.tier in ("Highly Qualified", "Top Tier"), (
        f"CDEProfile.sample() expected Highly Qualified or Top Tier, got '{score.tier}'. "
        "README quickstart may need updating."
    )
