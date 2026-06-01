"""Unit tests for the scoring engine."""

from __future__ import annotations
import pytest
from schemas.analysis import AuditResult, CategoryAnalysis
from scoring.scoring_engine import (
    WEIGHTS,
    calculate_score,
    get_score_grade,
    get_score_label,
    get_score_color_hex,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_result(score: float) -> AuditResult:
    """Build an AuditResult where all categories have the same *score*.

    Each field gets its own CategoryAnalysis instance so that deep copies
    produced by model_copy(deep=True) are truly independent.
    """
    def _cat() -> CategoryAnalysis:
        return CategoryAnalysis(score=score, findings=["test"], recommendations=["test"])

    return AuditResult(
        clarity=_cat(), value_proposition=_cat(), offer=_cat(), cta=_cat(),
        trust=_cat(), friction=_cat(), objections=_cat(), icp=_cat(),
    )


# ── Weights ───────────────────────────────────────────────────────────────────

def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_weights_keys_match_audit_result_fields() -> None:
    expected = {"clarity", "value_proposition", "offer", "trust", "cta", "icp", "objections", "friction"}
    assert set(WEIGHTS.keys()) == expected


# ── Score calculation ─────────────────────────────────────────────────────────

def test_perfect_score_is_100() -> None:
    result = _make_result(10.0)
    assert calculate_score(result) == 100.0


def test_zero_score_is_zero() -> None:
    result = _make_result(0.0)
    assert calculate_score(result) == 0.0


def test_mid_score_is_50() -> None:
    result = _make_result(5.0)
    assert calculate_score(result) == pytest.approx(50.0, abs=0.5)


def test_score_is_within_range() -> None:
    for s in [0, 2.5, 5, 7.5, 10]:
        overall = calculate_score(_make_result(s))
        assert 0.0 <= overall <= 100.0


def test_weighted_asymmetry() -> None:
    """Clarity (20%) should move the score more than Friction (5%)."""
    base = _make_result(5.0)

    # Boost clarity only
    clarity_boost = base.model_copy(deep=True)
    clarity_boost.clarity.score = 10.0
    s_clarity = calculate_score(clarity_boost)

    # Boost friction only
    friction_boost = base.model_copy(deep=True)
    friction_boost.friction.score = 10.0
    s_friction = calculate_score(friction_boost)

    assert s_clarity > s_friction, "Clarity (20%) should outweigh Friction (5%)"


# ── Grade / label ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (90, "A"), (75, "B"), (60, "C"), (45, "D"), (30, "F"),
])
def test_grade(score: float, expected: str) -> None:
    assert get_score_grade(score) == expected


@pytest.mark.parametrize("score,expected", [
    (90, "Excellent"), (75, "Good"), (60, "Average"), (45, "Needs Work"), (30, "Poor"),
])
def test_label(score: float, expected: str) -> None:
    assert get_score_label(score) == expected


# ── Colour ────────────────────────────────────────────────────────────────────

def test_color_green_for_high_score() -> None:
    assert get_score_color_hex(80) == "#10b981"


def test_color_amber_for_mid_score() -> None:
    assert get_score_color_hex(60) == "#f59e0b"


def test_color_red_for_low_score() -> None:
    assert get_score_color_hex(30) == "#ef4444"
