"""Pydantic models for LLM analysis output."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CategoryAnalysis(BaseModel):
    """Analysis result for a single CRO category."""

    score: float = Field(
        ...,
        ge=0,
        le=10,
        description=(
            "Score 0–10: 0–3 = poor/missing, 4–5 = below average, "
            "6–7 = good, 8–9 = strong, 10 = world-class"
        ),
    )
    findings: list[str] = Field(
        default_factory=list,
        description="2–4 specific observations from the page content",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="2–4 concrete, actionable improvement recommendations",
    )


class AuditResult(BaseModel):
    """
    Complete structured audit result returned by the LLM.
    overall_score is NOT filled by the LLM — it is computed by the scoring engine.
    """

    clarity: CategoryAnalysis
    value_proposition: CategoryAnalysis
    offer: CategoryAnalysis
    cta: CategoryAnalysis
    trust: CategoryAnalysis
    friction: CategoryAnalysis
    objections: CategoryAnalysis
    icp: CategoryAnalysis

    strengths: list[str] = Field(
        default_factory=list,
        description="Top 3–5 things the page does well",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Top 3–5 critical problems on the page",
    )
    top_revenue_leaks: list[str] = Field(
        default_factory=list,
        description="Top 3–5 biggest conversion killers, ordered by impact",
    )
    executive_summary: str = Field(
        default="",
        description="3–4 sentence summary a CMO would find valuable",
    )

    # Set by scoring engine AFTER LLM call — not expected from LLM
    overall_score: Optional[float] = Field(default=None, exclude=False)
