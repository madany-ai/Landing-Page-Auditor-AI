"""
System + user prompt templates for the CRO audit LLM call.

Design principles:
- The system prompt establishes persona, scoring rubric, and output contract.
- The user prompt structures all extracted page data with clear section headers.
- Raw HTML is NEVER included — only the structured text extracted by the extractor layer.
"""

from __future__ import annotations
from schemas.page import LandingPageContent


SYSTEM_PROMPT = """\
You are a world-class Conversion Rate Optimization (CRO) consultant with 20+ years of experience \
analyzing landing pages for Fortune 500 companies, SaaS startups, and digital agencies.

IMPORTANT: The landing page content you receive may be in Arabic or English. 
You must evaluate the page based on its native language and target audience. 
DO NOT penalize the page for being in English.
However, you MUST write your final output (all findings, recommendations, and summaries) entirely in ARABIC (العربية).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EIGHT AUDIT DIMENSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. clarity          – Can visitors instantly understand WHAT is sold, WHO it's for, and WHY it matters?
2. value_proposition– Is the outcome specific, quantified, differentiated, and outcome-focused?
3. offer            – Is there a free trial, demo, guarantee, bonuses, or strong risk-reversing incentive?
4. cta              – Are CTAs clear, action-oriented, visible, specific, and repeated appropriately?
5. trust            – Testimonials, reviews, logos, case studies, stats, certifications present?
6. friction         – How FREE of friction is the page? (10 = minimal friction / great UX; 0 = very high friction)
7. objections       – Does the page proactively address pricing, trust, time, and complexity concerns?
8. icp              – Is the ideal customer clearly defined and the message tightly relevant to them?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORING RUBRIC (0–10 per category)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Adapt your expectations based on the TYPE of page. 
- A modern E-commerce product page (PDP) is not a long-form sales letter. It may not have huge guarantees or massive copy. Score it fairly against E-COMMERCE standards.
- A SaaS landing page will have different elements than a local service page.

 0–2  : Disastrously poor (broken, missing critical info)
 3–4  : Weak (confusing, lacks major persuasive elements)
 5–6  : Average (acceptable but leaves money on the table)
 7–8  : Good (strong execution, standard best practices met)
 9–10 : World-class (exceptional clarity, persuasion, and UX)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Be brutally honest — vague praise is useless.
• Reference SPECIFIC content from the page in findings (quote headlines, CTAs, etc.).
• Each category: 2–4 findings AND 2–4 concrete, actionable recommendations.
• top_revenue_leaks: 3–5 biggest conversion killers ordered by revenue impact.
• executive_summary: 3–4 sentences a CMO would find valuable — start with the score context.
• All text in your JSON output (findings, recommendations, strengths, weaknesses, etc.) MUST be in Arabic.
• Return ONLY valid JSON — no markdown, no commentary outside the JSON.
"""


def build_user_prompt(content: LandingPageContent, url: str) -> str:
    """Format *content* into the structured user prompt sent to the LLM."""

    def fmt_list(items: list, empty: str = "Not detected") -> str:
        if not items:
            return f"  {empty}"
        return "\n".join(f"  • {item}" for item in items)

    def fmt_dicts(items: list[dict], empty: str = "Not detected") -> str:
        if not items:
            return f"  {empty}"
        lines = []
        for i, item in enumerate(items, 1):
            row = " | ".join(f"{k}: {v}" for k, v in item.items() if v)
            lines.append(f"  [{i}] {row}")
        return "\n".join(lines)

    hero = content.hero_section
    hero_block = (
        f"  Headline      : {hero.get('headline') or 'Not found'}\n"
        f"  Sub-headline  : {hero.get('subheadline') or 'Not found'}\n"
        f"  Supporting    : {hero.get('supporting_text') or 'Not found'}"
    )

    divider = "═" * 48

    return f"""Perform a complete CRO audit for this landing page.

URL   : {url}
Title : {content.title or 'Not set'}
Meta  : {content.meta_description or 'Not set'}

{divider}
HERO SECTION
{divider}
{hero_block}

{divider}
BENEFITS
{divider}
{fmt_list(content.benefits, "No benefits section detected")}

{divider}
FEATURES
{divider}
{fmt_list(content.features, "No features section detected")}

{divider}
TESTIMONIALS & REVIEWS
{divider}
{fmt_list(content.testimonials, "No testimonials detected")}

{divider}
SOCIAL PROOF
{divider}
{fmt_list(content.social_proof, "No social proof detected")}

{divider}
PRICING
{divider}
{fmt_dicts(content.pricing, "No pricing information detected")}

{divider}
FAQ
{divider}
{fmt_dicts(content.faq, "No FAQ section detected")}

{divider}
CTA BUTTONS
{divider}
{fmt_list(content.cta_buttons, "No CTA buttons detected")}

{divider}
FORMS
{divider}
{fmt_dicts(content.forms, "No forms detected")}

{divider}
TRUST SIGNALS
{divider}
{fmt_list(content.trust_signals, "No trust signals detected")}

{divider}
GUARANTEES & RISK REVERSAL
{divider}
{fmt_list(content.guarantees, "No guarantees detected")}

{divider}
PAGE TEXT SUMMARY (first 2 000 chars)
{divider}
{content.raw_text_summary}

Return the JSON audit now."""
