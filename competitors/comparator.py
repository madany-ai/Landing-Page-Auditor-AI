"""
Competitor comparison orchestrator.

Takes a target URL, discovers competitors, audits them all,
and produces a strategic ComparisonResult.
"""

from __future__ import annotations

import time
from typing import Optional, Callable
from urllib.parse import urlparse

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from competitors.discovery import discover_competitors
from pipeline import run_audit_pipeline, get_output_dir
from schemas.comparison import CompetitorSummary, ComparisonInsights, ComparisonResult
from scoring.scoring_engine import get_score_grade
from llm.client import get_client, get_model_name
from llm.comparison_prompts import COMPARISON_SYSTEM_PROMPT, build_comparison_user_prompt
from config.settings import settings
from reports.comparison_report import generate_comparison_html


# Type alias
ProgressCallback = Callable[[str, int, int], None]


def _audit_to_summary(data: dict) -> CompetitorSummary:
    """Convert a run_audit_pipeline result dict into a CompetitorSummary."""
    result = data["result"]
    raw_page = data.get("raw_page")
    url = raw_page.url if raw_page else ""
    domain = urlparse(url).netloc.replace("www.", "") if url else ""

    return CompetitorSummary(
        url=url,
        domain=domain,
        title=raw_page.title if raw_page else "",
        overall_score=data["overall_score"],
        grade=get_score_grade(data["overall_score"]),
        clarity_score=result.clarity.score,
        value_proposition_score=result.value_proposition.score,
        offer_score=result.offer.score,
        trust_score=result.trust.score,
        cta_score=result.cta.score,
        icp_score=result.icp.score,
        objections_score=result.objections.score,
        friction_score=result.friction.score,
        strengths=result.strengths[:3],
        weaknesses=result.weaknesses[:3],
    )


from concurrent.futures import ThreadPoolExecutor, as_completed

def _call_comparison_llm(messages: list[dict], model: str) -> ComparisonInsights:
    """Call the LLM for competitive comparison insights."""
    client = get_client()
    from llm.client import safe_llm_call
    return safe_llm_call(
        client=client,
        messages=messages,
        response_model=ComparisonInsights,
        model=model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


def run_competitor_pipeline(
    url: str,
    model: Optional[str] = None,
    market: str = "Global",
    num_competitors: int = 3,
    progress_cb: Optional[ProgressCallback] = None,
) -> ComparisonResult:
    """
    Full competitor comparison pipeline.

    Steps:
        1. Audit target page
        2. Discover competitors via DuckDuckGo
        3. Audit each competitor concurrently
        4. Run LLM comparison analysis
        5. Generate Unified Intelligence Report
    """
    total_steps = 3 + num_competitors

    def notify(msg: str, step: int) -> None:
        logger.info(f"[{step}/{total_steps}] {msg}")
        if progress_cb:
            progress_cb(msg, step, total_steps)

    start = time.perf_counter()

    # ── Step 1: Audit target ─────────────────────────────────────────────
    notify("Auditing target page…", 1)
    target_data = run_audit_pipeline(url, model=model, skip_reports=True)
    target_summary = _audit_to_summary(target_data)

    # ── Step 2: Discover competitors ─────────────────────────────────────
    notify("Searching for competitors…", 2)
    content = target_data.get("content")
    discovery_data = discover_competitors(url, content=content, model=model, market=market, max_results=num_competitors)
    
    competitor_urls = discovery_data.get("competitors", [])
    rejected_raw = discovery_data.get("rejected", [])
    total_searches = discovery_data.get("searches", 0)
    total_evaluated = discovery_data.get("evaluated", 0)
    
    from schemas.comparison import RejectedCandidate, DiscoveryMetrics
    
    rejected_candidates = [
        RejectedCandidate(
            domain=r.get("domain", ""),
            url=r.get("url", ""),
            reason=r.get("reason", ""),
            confidence=r.get("confidence", 0)
        )
        for r in rejected_raw
    ]
    
    accepted_confidences = [c["evaluation"].confidence for c in competitor_urls if "evaluation" in c]
    avg_confidence = sum(accepted_confidences) // len(accepted_confidences) if accepted_confidences else 0
    discovery_metrics = DiscoveryMetrics(
        quality_score=avg_confidence,
        total_searches=total_searches,
        total_evaluated=total_evaluated
    )

    # ── Steps 3..N: Audit each competitor concurrently ───────────────────
    competitor_summaries: list[CompetitorSummary] = []
    
    def _audit_competitor(i: int, comp_info: dict) -> CompetitorSummary:
        step = 3 + i
        comp_url = comp_info["url"]
        comp_domain = comp_info.get("domain", "")
        notify(f"Auditing competitor: {comp_domain}…", step)
        
        confidence = 0
        reason = ""
        if "evaluation" in comp_info:
            confidence = comp_info["evaluation"].confidence
            reason = comp_info["evaluation"].reason

        try:
            comp_data = run_audit_pipeline(comp_url, model=model, skip_reports=True)
            summary = _audit_to_summary(comp_data)
            summary.confidence = confidence
            summary.selection_reason = reason
            return summary
        except Exception as exc:
            logger.warning(f"Failed to audit competitor {comp_domain}: {exc}")
            return CompetitorSummary(
                url=comp_url,
                domain=comp_domain,
                title=comp_info.get("title", ""),
                overall_score=0,
                grade="N/A",
                confidence=confidence,
                selection_reason=reason
            )

    with ThreadPoolExecutor(max_workers=num_competitors) as executor:
        futures = [
            executor.submit(_audit_competitor, i, comp_info) 
            for i, comp_info in enumerate(competitor_urls)
        ]
        for future in as_completed(futures):
            competitor_summaries.append(future.result())

    # ── Final step: LLM comparison ───────────────────────────────────────
    notify("Running competitive analysis…", total_steps - 1)
    model_name = get_model_name(model)

    valid_competitors = [c for c in competitor_summaries if c.overall_score > 0]

    if valid_competitors:
        messages = [
            {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
            {"role": "user", "content": build_comparison_user_prompt(target_summary, valid_competitors)},
        ]
        insights = _call_comparison_llm(messages, model_name)
    else:
        logger.warning("No competitors were successfully audited — skipping comparison LLM call.")
        insights = ComparisonInsights()

    # ── Calculate Benchmarks ─────────────────────────────────────────────
    from schemas.comparison import CategoryBenchmarks, BenchmarkStats
    
    benchmarks = CategoryBenchmarks()
    if valid_competitors:
        def calc_bench(attr: str) -> BenchmarkStats:
            t_score = getattr(target_summary, attr)
            c_scores = [getattr(c, attr) for c in valid_competitors]
            c_avg = sum(c_scores) / len(c_scores) if c_scores else 0.0
            return BenchmarkStats(
                target_score=round(t_score, 1),
                competitor_average=round(c_avg, 1),
                gap=round(t_score - c_avg, 1)
            )

        benchmarks.clarity = calc_bench("clarity_score")
        benchmarks.value_proposition = calc_bench("value_proposition_score")
        benchmarks.offer = calc_bench("offer_score")
        benchmarks.trust = calc_bench("trust_score")
        benchmarks.cta = calc_bench("cta_score")
        benchmarks.icp = calc_bench("icp_score")
        benchmarks.objections = calc_bench("objections_score")
        benchmarks.friction = calc_bench("friction_score")

    # ── Final step: Unified Reports ───────────────────────────────────────
    notify("Generating unified intelligence report…", total_steps)
    
    comp_result = ComparisonResult(
        target=target_summary,
        competitors=competitor_summaries,
        rejected_candidates=rejected_candidates,
        discovery_metrics=discovery_metrics,
        insights=insights,
        benchmarks=benchmarks,
    )

    output_dir = get_output_dir(url)
    
    from reports.markdown_report import generate_markdown_report
    from reports.html_report import generate_html_report
    from reports.pdf_report import generate_pdf_report
    
    md_path = generate_markdown_report(target_data["result"], url, output_dir, comparison_result=comp_result)
    html_path = generate_html_report(target_data["result"], url, output_dir, comparison_result=comp_result)
    pdf_path = generate_pdf_report(md_path)
    
    comp_result.html_path = html_path
    comp_result.pdf_path = pdf_path

    elapsed = time.perf_counter() - start
    logger.success(f"Competitor analysis complete in {elapsed:.1f}s | "
                   f"target={target_summary.overall_score}/100 | "
                   f"competitors={len(valid_competitors)} | HTML={html_path}")

    return comp_result
