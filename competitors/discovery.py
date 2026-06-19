"""
Competitor discovery via Autonomous ReAct Agent.

Finds competing landing pages for a given URL by:
1. Profiling the target page (Industry, Audience, Offer).
2. Dynamically strategizing search queries.
3. Fetching and semantically evaluating candidates in a loop.
4. Stopping when high-confidence matches are found.
"""

from __future__ import annotations

import re
import warnings
from urllib.parse import urlparse
from loguru import logger
from pydantic import BaseModel, Field

from ddgs import DDGS
from schemas.page import LandingPageContent, RawPage
from schemas.comparison import CandidateEvaluation
from llm.client import get_client, get_model_name, safe_llm_call
from scraper.page_loader import load_page


# Domains to always exclude from competitor results
_EXCLUDED_DOMAINS = {
    "youtube.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "linkedin.com", "tiktok.com", "pinterest.com",
    "reddit.com", "wikipedia.org", "wikimedia.org", "quora.com",
    "amazon.com", "ebay.com", "google.com", "apple.com",
    "play.google.com", "apps.apple.com", "noon.com", "jumia.com", "aliexpress.com",
}

MARKET_REGIONS = {
    "Egypt": "eg-ar",
    "Saudi Arabia": "sa-ar",
    "UAE": "ae-ar",
    "Global": "wt-wt"
}


class TargetProfile(BaseModel):
    page_type: str = Field(description="e.g. SaaS, E-commerce, Local Business")
    industry: str = Field(description="The broad industry")
    category: str = Field(description="The specific product/service category")
    offer: str = Field(description="The core product or service being sold")
    audience: str = Field(description="Ideal Customer Profile")
    positioning: str = Field(description="How they position themselves in the market")


class SearchStrategy(BaseModel):
    thought: str = Field(description="Reasoning for the next search step based on current roster and rejected candidates.")
    query: str = Field(description="The exact DuckDuckGo search query to execute. ALWAYS write the query in English for maximum quality.")


class CompetitorDiscoveryAgent:
    def __init__(self, url: str, content: LandingPageContent, model: str | None, market: str = "Global", max_results: int = 3, max_iterations: int = 5):
        self.target_url = url
        self.target_domain = self._extract_domain(url)
        self.content = content
        self.model_name = get_model_name(model)
        self.client = get_client()
        self.market = market
        self.ddg_region = MARKET_REGIONS.get(market, "wt-wt")
        self.max_results = max_results
        self.max_iterations = max_iterations
        
        self.profile: TargetProfile | None = None
        self.competitors: list[dict] = []
        self.rejected: list[dict] = []
        self.search_history: list[str] = []
        self.seen_domains: set[str] = {self.target_domain}

    def _extract_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower().replace("www.", "")

    def _build_profile(self) -> TargetProfile:
        logger.info(f"[AGENT] Building target profile for {self.target_domain} in market: {self.market}...")
        sys_prompt = "You are an expert marketing strategist. Deeply profile this business based on their landing page."
        user_prompt = f"""
Hero: {self.content.hero_section}
Benefits: {self.content.benefits}
Features: {self.content.features}
Summary: {self.content.raw_text_summary[:500]}
Target Market: {self.market}
"""
        res = safe_llm_call(
            client=self.client,
            model=self.model_name,
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            response_model=TargetProfile,
            temperature=0.1,
            max_tokens=500,
        )
        self.profile = res
        logger.info(f"[AGENT PROFILE] Industry: {res.industry} | Offer: {res.offer} | Market: {self.market}")
        return res

    def _strategize(self) -> SearchStrategy:
        logger.info("[AGENT] Strategizing next search query...")
        sys_prompt = f"You are an autonomous Competitor Discovery Agent. Your goal is to find exact direct competitors in the {self.market} market. Decide what to search next on DuckDuckGo."
        
        rejected_context = ""
        if self.rejected:
            rejected_context = "Previously Rejected Candidates:\n" + "\n".join(
                f"- {r['domain']} (Confidence: {r['confidence']}%): {r['reason']}" for r in self.rejected[-5:]
            )

        user_prompt = f"""
Target Profile:
- Industry: {self.profile.industry}
- Category: {self.profile.category}
- Offer: {self.profile.offer}
- Audience: {self.profile.audience}
- Target Market: {self.market}

Search History: {self.search_history}
Current Valid Competitors Found: {len(self.competitors)}/{self.max_results}

{rejected_context}

Based on this, what is the single best search query to execute right now?
Strategy Tip: Start with Exact Product Search. If that fails, try Category Search, then Brand Alternatives Search.
"""
        return safe_llm_call(
            client=self.client,
            model=self.model_name,
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            response_model=SearchStrategy,
            temperature=0.5,
            max_tokens=400,
        )

    def _search(self, query: str) -> list[dict]:
        logger.info(f"[AGENT SEARCH] Executing DDGS for: '{query}' (Region: {self.ddg_region})")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, region=self.ddg_region, max_results=10))
            logger.info(f"[AGENT SEARCH] Found {len(results)} raw results.")
            return results
        except Exception as exc:
            logger.error(f"[AGENT SEARCH] Failed: {exc}")
            return []

    def _evaluate(self, raw_page: RawPage) -> CandidateEvaluation:
        sys_prompt = "You are a ruthless Competitive Intelligence Analyst. Evaluate if this candidate URL is a DIRECT competitor to the target business."
        
        user_prompt = f"""
TARGET BUSINESS PROFILE:
- Offer: {self.profile.offer}
- Category: {self.profile.category}
- Audience: {self.profile.audience}
- Market: {self.market}

A VALID competitor MUST be:
1. A dedicated product page
OR
2. A dedicated category page
OR
3. A direct ecommerce store

You MUST strictly REJECT the following types of pages:
- Search results pages (e.g. "?s=" or "/search" or marketplace listings)
- Login or signup pages
- Blog posts or articles
- Review sites (e.g. Trustpilot, G2, Capterra)
- Directory pages
- Affiliate pages
- Empty, parked, or error pages

CANDIDATE URL: {raw_page.url}
CANDIDATE TITLE: {raw_page.title}
CANDIDATE CONTENT (Truncated):
{raw_page.body_text[:1500]}

Is this candidate a direct competitor selling a competing product/service to the same audience?
"""
        return safe_llm_call(
            client=self.client,
            model=self.model_name,
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            response_model=CandidateEvaluation,
            temperature=0.1,
            max_tokens=400,
        )

    def run(self) -> list[dict]:
        if not self.content:
            logger.error("[AGENT] Cannot run agent without LandingPageContent.")
            return []

        try:
            self._build_profile()
        except Exception as exc:
            logger.error(f"[AGENT] Failed to build profile: {exc}")
            return []
        
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n[AGENT] === Iteration {iteration}/{self.max_iterations} ===")
            
            # 1. Strategize
            try:
                strategy = self._strategize()
                logger.info(f"[AGENT THOUGHT] {strategy.thought}")
                self.search_history.append(strategy.query)
            except Exception as exc:
                logger.error(f"[AGENT] Strategize failed: {exc}")
                continue
            
            # 2. Search
            raw_results = self._search(strategy.query)
            if not raw_results:
                logger.warning("[AGENT] 0 results found for query. Will rethink and retry.")
                continue
                
            # 3. Evaluate Candidates
            for result in raw_results:
                if len(self.competitors) >= self.max_results:
                    break
                    
                href = result.get("href", "")
                if not href: continue
                c_domain = self._extract_domain(href)
                
                if c_domain in self.seen_domains or any(x in c_domain for x in _EXCLUDED_DOMAINS):
                    continue
                    
                self.seen_domains.add(c_domain)
                logger.info(f"[AGENT FETCH] {c_domain}")
                
                try:
                    raw_page = load_page(href)
                    if not raw_page.body_text:
                        logger.warning(f"[AGENT REJECTED] {c_domain} | Reason: Failed to scrape content.")
                        continue
                        
                    eval_res = self._evaluate(raw_page)
                    
                    if eval_res.is_competitor and eval_res.confidence >= 80:
                        logger.success(f"[AGENT ACCEPTED] {c_domain} | Conf: {eval_res.confidence}% | Reason: {eval_res.reason}")
                        self.competitors.append({
                            "url": href,
                            "domain": c_domain,
                            "title": raw_page.title or result.get("title", ""),
                            "snippet": result.get("body", ""),
                            "evaluation": eval_res
                        })
                    else:
                        logger.warning(f"[AGENT REJECTED] {c_domain} | Conf: {eval_res.confidence}% | Reason: {eval_res.reason}")
                        self.rejected.append({
                            "url": href,
                            "domain": c_domain,
                            "reason": eval_res.reason,
                            "confidence": eval_res.confidence
                        })
                        
                except Exception as exc:
                    logger.error(f"[AGENT ERROR] Failed to fetch/evaluate {c_domain}: {exc}")

            # 4. Check stopping condition
            if len(self.competitors) >= self.max_results:
                logger.success(f"\n[AGENT STOP] Met condition: Found {len(self.competitors)} high-confidence competitors.")
                break
                
        if not self.competitors:
            logger.error("\n[AGENT DIAGNOSTIC] Failed to find competitors.")
            logger.error(f"- Queries tried: {self.search_history}")
            logger.error(f"- Total rejected candidates: {len(self.rejected)}")
            
        return {
            "competitors": self.competitors,
            "rejected": self.rejected,
            "searches": len(self.search_history),
            "evaluated": len(self.competitors) + len(self.rejected)
        }


def discover_competitors(
    url: str,
    content: LandingPageContent | None = None,
    model: str | None = None,
    market: str = "Global",
    max_results: int = 3,
) -> dict:
    """
    Entrypoint for competitor discovery agent.
    """
    if not content:
        # Fallback if somehow called without content
        logger.warning("No content provided, using basic heuristic search.")
        domain = urlparse(url).netloc.lower().replace("www.", "")
        domain_words = re.sub(r"[-_.]", " ", domain.split(".")[0]).strip()
        query = f"{domain_words} competitors"
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=max_results))
            return {
                "competitors": [{"url": r["href"], "domain": urlparse(r["href"]).netloc, "title": r.get("title", ""), "evaluation": CandidateEvaluation(url=r["href"], title=r.get("title", ""), is_competitor=True, is_direct_seller=True, confidence=50, reason="Fallback search", industry_match=True, audience_match=True, offer_match=True)} for r in raw_results],
                "rejected": [],
                "searches": 1,
                "evaluated": len(raw_results)
            }
        except Exception:
            return {"competitors": [], "rejected": [], "searches": 1, "evaluated": 0}

    agent = CompetitorDiscoveryAgent(url, content, model, market=market, max_results=max_results)
    return agent.run()
