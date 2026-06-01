"""
Weighted scoring engine.

PRD weights:
  Clarity            20%
  Value Proposition  15%
  Offer              15%
  Trust              15%
  CTA                10%
  ICP                10%
  Objections         10%
  Friction            5%

LLM category scores are 0–10.
Final score = weighted average × 10 → range 0–100.
"""

from __future__ import annotations
from schemas.analysis import AuditResult


WEIGHTS: dict[str, float] = {
    "clarity":           0.20,
    "value_proposition": 0.15,
    "offer":             0.15,
    "trust":             0.15,
    "cta":               0.10,
    "icp":               0.10,
    "objections":        0.10,
    "friction":          0.05,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


def calculate_score(result: AuditResult) -> float:
    """
    Compute the overall CRO score (0–100, one decimal place).

    Each category score is 0–10; the weighted sum is scaled to 0–100.
    """
    raw: dict[str, float] = {
        "clarity":           result.clarity.score,
        "value_proposition": result.value_proposition.score,
        "offer":             result.offer.score,
        "trust":             result.trust.score,
        "cta":               result.cta.score,
        "icp":               result.icp.score,
        "objections":        result.objections.score,
        "friction":          result.friction.score,
    }
    weighted_sum = sum(raw[k] * WEIGHTS[k] for k in WEIGHTS)
    return round(weighted_sum * 10, 1)   # 0–10 → 0–100


def get_score_grade(score: float) -> str:
    """Letter grade for the overall score."""
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def get_score_label(score: float) -> str:
    """Human-readable label for the overall score."""
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Average"
    if score >= 40:
        return "Needs Work"
    return "Poor"


def get_score_color_hex(score: float) -> str:
    """Return a hex colour appropriate for the given score."""
    if score >= 70:
        return "#10b981"   # green
    if score >= 50:
        return "#f59e0b"   # amber
    return "#ef4444"       # red
