"""Pydantic models for competitor comparison results."""

from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field


class CompetitorSummary(BaseModel):
    """Summarised audit result for one page (target or competitor)."""

    url: str = ""
    domain: str = ""
    title: str = ""
    overall_score: float = 0.0
    grade: str = ""
    confidence: int = 0
    selection_reason: str = ""

    # Per-category scores (0-10)
    clarity_score: float = 0.0
    value_proposition_score: float = 0.0
    offer_score: float = 0.0
    trust_score: float = 0.0
    cta_score: float = 0.0
    icp_score: float = 0.0
    objections_score: float = 0.0
    friction_score: float = 0.0

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class RejectedCandidate(BaseModel):
    """A candidate URL that was rejected during discovery."""
    domain: str
    url: str
    reason: str
    confidence: int


class DiscoveryMetrics(BaseModel):
    """Metrics detailing the quality of the discovery process."""
    quality_score: int = 0
    total_searches: int = 0
    total_evaluated: int = 0


class CandidateEvaluation(BaseModel):
    """Agentic semantic evaluation of a potential competitor."""
    url: str = Field(description="The URL of the candidate")
    title: str = Field(description="The title of the candidate page")
    is_competitor: bool = Field(description="True if this is a direct competitor")
    is_direct_seller: bool = Field(description="True ONLY if they directly sell products/services (not a blog, review, or directory)")
    confidence: int = Field(description="Confidence score 0-100")
    reason: str = Field(description="Why was this accepted or rejected?")
    industry_match: bool = Field(description="Does it match the target industry?")
    audience_match: bool = Field(description="Does it target the same audience?")
    offer_match: bool = Field(description="Does it offer a similar product/service?")


class BusinessInsight(BaseModel):
    """A deep, actionable competitive gap or advantage."""
    observation: str = Field(description="What did you observe across the competitors vs the target?")
    evidence: str = Field(description="What specific data/content from the audit supports this observation?")
    impact: str = Field(description="Why does this matter for conversion rates and revenue?")
    recommendation: str = Field(description="What exactly should the target page do to fix or capitalize on this?")


class ActionPlanItem(BaseModel):
    """A ranked item in the prioritized roadmap."""
    priority: int = Field(description="Rank (1 is highest priority)")
    title: str = Field(description="Short action title")
    expected_impact: str = Field(description="High, Medium, or Low")
    effort: str = Field(description="High, Medium, or Low")
    description: str = Field(description="Specific implementation details")


class ComparisonInsights(BaseModel):
    """LLM-generated strategic competitive intelligence."""

    missing_elements: list[str] = Field(
        default_factory=list,
        description="Things competitors consistently have that the target lacks",
    )
    competitive_advantages: list[str] = Field(
        default_factory=list,
        description="Things the target does better than competitors",
    )
    quick_wins: list[str] = Field(
        default_factory=list,
        description="Low-effort, high-impact improvements",
    )
    deep_insights: list[BusinessInsight] = Field(
        default_factory=list,
        description="Deep dive analyses into specific competitive gaps",
    )
    action_plan: list[ActionPlanItem] = Field(
        default_factory=list,
        description="Prioritized roadmap of actions",
    )


class BenchmarkStats(BaseModel):
    """Calculated benchmark for a specific category."""
    target_score: float = 0.0
    competitor_average: float = 0.0
    gap: float = 0.0


class CategoryBenchmarks(BaseModel):
    """Mathematical benchmarks for all CRO categories."""
    clarity: BenchmarkStats = Field(default_factory=BenchmarkStats)
    value_proposition: BenchmarkStats = Field(default_factory=BenchmarkStats)
    offer: BenchmarkStats = Field(default_factory=BenchmarkStats)
    trust: BenchmarkStats = Field(default_factory=BenchmarkStats)
    cta: BenchmarkStats = Field(default_factory=BenchmarkStats)
    icp: BenchmarkStats = Field(default_factory=BenchmarkStats)
    objections: BenchmarkStats = Field(default_factory=BenchmarkStats)
    friction: BenchmarkStats = Field(default_factory=BenchmarkStats)


class ComparisonResult(BaseModel):
    """Full comparison result: target + competitors + AI insights + Benchmarks."""

    target: CompetitorSummary
    competitors: list[CompetitorSummary] = Field(default_factory=list)
    rejected_candidates: list[RejectedCandidate] = Field(default_factory=list)
    discovery_metrics: DiscoveryMetrics = Field(default_factory=DiscoveryMetrics)
    insights: ComparisonInsights = Field(default_factory=ComparisonInsights)
    benchmarks: CategoryBenchmarks = Field(default_factory=CategoryBenchmarks)
    html_path: str | Path = Field(default="")
    pdf_path: str | Path = Field(default="")
