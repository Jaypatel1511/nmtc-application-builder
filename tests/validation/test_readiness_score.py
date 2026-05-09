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
    assert "Recommendations" in summary


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


def test_readiness_score_has_strengths_and_weaknesses(sample_pipeline_result):
    score = compute_readiness_score(
        sample_pipeline_result,
        [ValidationResult("check", True, [], [])],
    )
    assert isinstance(score.top_strengths, list)
    assert isinstance(score.top_weaknesses, list)
    assert isinstance(score.recommendations, list)
    assert len(score.top_strengths) > 0
