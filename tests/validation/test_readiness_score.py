"""Tests for readiness score computation."""
import pytest

from nmtcapp.data.schema import ValidationResult
from nmtcapp.validation.readiness_score import ReadinessScore, compute_readiness_score


def test_readiness_score_creation():
    score = ReadinessScore(
        overall_score=75.0,
        component_scores={"a": 80.0, "b": 70.0},
        grade="B",
        top_strengths=["Good eligibility"],
        top_weaknesses=["Low distress"],
        recommendations=["Add more projects"],
    )
    assert score.overall_score == 75.0
    assert score.grade == "B"


def test_readiness_score_summary_method():
    score = ReadinessScore(
        overall_score=80.0,
        component_scores={"eligibility_quality": 90.0, "distress_concentration": 70.0},
        grade="B",
        top_strengths=["High eligibility"],
        top_weaknesses=["Improve distress"],
        recommendations=["Add deep-distress projects"],
    )
    summary = score.summary()
    assert isinstance(summary, str)
    assert "80.0" in summary
    assert "Grade: B" in summary or "[B]" in summary
    # 1.5.2 T1: a hand-built ReadinessScore keeps whatever lists it was given,
    # so this constructed object still renders its recommendations under the
    # heading that says they are NOT composite-derived. What no longer holds
    # is that compute_readiness_score() produces any — see
    # test_the_composite_emits_no_narrative below.
    assert "Add deep-distress projects" in summary


def test_compute_readiness_score_returns_readiness_score(sample_pipeline_result):
    validations = [
        ValidationResult("eligibility_check", True, [], []),
        ValidationResult("completeness_check", True, [], []),
        ValidationResult("consistency_check", True, [], []),
    ]
    score = compute_readiness_score(sample_pipeline_result, validations)
    assert isinstance(score, ReadinessScore)
    assert 0 <= score.overall_score <= 100


def test_readiness_score_grade_A(sample_pipeline_result):
    validations = [ValidationResult("check", True, [], [])]
    score = compute_readiness_score(sample_pipeline_result, validations)
    # Sample pipeline has strong distress concentration and eligibility
    assert score.grade in ("A", "B")  # should be high


def test_readiness_score_penalized_by_failures(sample_pipeline_result):
    good = compute_readiness_score(
        sample_pipeline_result,
        [ValidationResult("check", True, [], [])],
    )
    bad = compute_readiness_score(
        sample_pipeline_result,
        [ValidationResult("check", False, ["Critical issue 1", "Critical issue 2"], [])],
    )
    assert bad.overall_score < good.overall_score


def test_readiness_score_to_dict(sample_pipeline_result):
    score = compute_readiness_score(
        sample_pipeline_result,
        [ValidationResult("check", True, [], [])],
    )
    d = score.to_dict()
    assert isinstance(d, dict)
    assert "overall_score" in d
    assert "grade" in d
    assert "component_scores" in d
    assert "recommendations" in d


def test_the_narrative_fields_survive_as_public_api(sample_pipeline_result):
    """RENAMED AND INVERTED BY 1.5.2 T1, AND THE FIELDS ARE THE POINT.

    This asserted ``len(score.top_strengths) > 0``. T1 withdrew the composite's
    narrative, so that is now false by design.

    WHAT IS ASSERTED INSTEAD IS THE THING THE WITHDRAWAL HAD TO PRESERVE. The
    three fields are public API and they are still here, still lists, still in
    to_dict(). Emptying them is a patch; REMOVING them is a breaking change
    and belongs with the 2.0.0 deletion of overall_score and grade. If a later
    round deletes them, this test is what goes red — and it should, because
    that release is not a patch.
    """
    score = compute_readiness_score(
        sample_pipeline_result,
        [ValidationResult("check", True, [], [])],
    )
    assert isinstance(score.top_strengths, list)
    assert isinstance(score.top_weaknesses, list)
    assert isinstance(score.recommendations, list)

    d = score.to_dict()
    for key in ("top_strengths", "top_weaknesses", "recommendations",
                "narrative_withdrawn", "narrative_note"):
        assert key in d, (
            f"to_dict() no longer carries {key!r}. The withdrawal was supposed "
            "to empty the narrative, not remove the API that reports it."
        )
    assert d["narrative_withdrawn"] is True
    assert "WITHDRAWN" in d["narrative_note"]
