"""
LLM prompts for competitive comparison analysis.

Takes structured audit data from the target and its competitors
and asks the LLM for strategic competitive insights.
"""

from __future__ import annotations

from schemas.comparison import CompetitorSummary


COMPARISON_SYSTEM_PROMPT = """\
You are a Senior CRO Consultant, Conversion Optimization Expert, and Product Strategist.

You will receive structured audit data for a TARGET landing page and several COMPETITOR landing pages.
Each page has been independently audited across 8 CRO dimensions with scores from 0–10.

Your task is to perform a true Competitive Gap Analysis that answers:
- What are competitors doing better?
- What conversion opportunities are missing?
- What strengths does the analyzed page already have?
- What specific improvements would close the conversion gap?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Do NOT generate a generic comparison that only contains scores or shallow summaries.
Every insight must be grounded in EVIDENCE from the provided scraped data.
Explain WHY competitors outperform the analyzed page and WHAT should be changed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You must output a highly structured JSON object adhering to the schema requested:

1. missing_elements: Array of things competitors consistently have that the target lacks.
2. competitive_advantages: Array of things the target does better than competitors.
3. quick_wins: Array of low-effort improvements with potentially high impact.
4. deep_insights: Array of specific business insights. Each insight must contain:
   - observation: What did you observe across the competitors vs the target?
   - evidence: What specific data/content from the audit supports this observation?
   - impact: Why does this matter for conversion rates and revenue?
   - recommendation: What exactly should the target page do to fix or capitalize on this?
5. action_plan: Array of a prioritized roadmap. Each item must contain:
   - priority: Rank (1 is highest priority)
   - title: Short action title
   - expected_impact: High, Medium, or Low
   - effort: High, Medium, or Low
   - description: Specific implementation details

IMPORTANT: All output MUST be in Arabic (العربية).
Return ONLY valid JSON — no markdown, no commentary outside the JSON.
"""


def build_comparison_user_prompt(
    target: CompetitorSummary,
    competitors: list[CompetitorSummary],
) -> str:
    """Build the user prompt for competitive comparison."""

    divider = "═" * 48

    def _format_page(label: str, page: CompetitorSummary) -> str:
        return f"""{label}
  URL:              {page.url}
  Domain:           {page.domain}
  Title:            {page.title}
  Overall Score:    {page.overall_score}/100 (Grade: {page.grade})
  ─── Category Scores ───
  Clarity:          {page.clarity_score}/10
  Value Prop:       {page.value_proposition_score}/10
  Offer:            {page.offer_score}/10
  Trust:            {page.trust_score}/10
  CTA:              {page.cta_score}/10
  ICP:              {page.icp_score}/10
  Objections:       {page.objections_score}/10
  Friction:         {page.friction_score}/10
  ─── Key Findings ───
  Strengths:  {'; '.join(page.strengths) or 'None'}
  Weaknesses: {'; '.join(page.weaknesses) or 'None'}"""

    sections = [
        f"Perform a strategic competitive gap analysis as a Senior CRO Consultant.\n",
        divider,
        "🎯 TARGET PAGE (the page we want to improve)",
        divider,
        _format_page("TARGET", target),
        "",
    ]

    for i, comp in enumerate(competitors, 1):
        sections.extend([
            divider,
            f"⚔️ COMPETITOR {i}",
            divider,
            _format_page(f"COMPETITOR {i}", comp),
            "",
        ])

    sections.append("\nGenerate the highly structured JSON Competitive Intelligence report now in Arabic.")
    return "\n".join(sections)
