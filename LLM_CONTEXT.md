# LLM Project Context: Landing Page Auditor AI

**Purpose of this document:** To quickly onboard any AI/LLM on how this project is structured, what the core design decisions are, and where logic lives.

---

## 1. High-Level Concept
This is a comprehensive Conversion Rate Optimization (CRO) and Competitive Intelligence tool. 
It takes a target landing page URL, scrapes it, analyzes its marketing structure, scores it across 8 CRO categories, discovers 3-5 direct local competitors using a DuckDuckGo AI Agent, audits those competitors, and generates a massive unified HTML/PDF "Intelligence Report" detailing gaps, strengths, and actionable priorities.

All output logic, prompts, and insights are generated in **Arabic**.

## 2. Core Architecture Pipeline
The system operates as a sequential pipeline, largely coordinated by `competitors/comparator.py`:

1. **Scraping (`scraper/`)**:
   - `fetch.py`: Tries fast HTTP (`Scrapling`). If it detects Cloudflare/bot-protection, falls back to `StealthyFetcher` (headless Chromium).
   - `page_loader.py`: Converts HTML into a clean `RawPage` schema (text, headings, lists).
2. **Extraction (`extractor/`)**:
   - `extractor.py`: Uses keyword heuristics (Arabic/English) to pull out specific sections (features, pricing, testimonials, CTAs). No LLM used here to save tokens. Outputs a `LandingPageContent` schema.
3. **Target Audit (`llm/analyzer.py`)**:
   - Sends the extracted `LandingPageContent` to the LLM (via `instructor` and `litellm` in `llm/client.py`).
   - The LLM returns a strictly typed `AuditResult` Pydantic model (found in `schemas/audit.py`).
4. **Competitor Discovery (`competitors/discovery.py`)**:
   - `CompetitorDiscoveryAgent`: A ReAct-style agent.
   - Extracts a business profile from the target page.
   - Uses `DDGS` (DuckDuckGo) to search for competitors in a specific `market` (e.g., Egypt, Saudi Arabia).
   - *Strict Validation:* Evaluates every candidate URL using the LLM to explicitly reject search results, blogs, directories, and login pages. Requires a dedicated product/category page.
5. **Competitor Audits**:
   - Runs the same Scrape -> Extract -> Audit pipeline on all validated competitors in parallel using a `ThreadPoolExecutor`.
6. **Gap Analysis (`competitors/comparator.py`)**:
   - Compares the target audit vs competitor audits.
   - Computes mathematical benchmarks (`CategoryBenchmarks`).
   - LLM generates a strategic gap analysis (`ComparisonInsights`).
7. **Report Generation (`reports/`)**:
   - Takes `ComparisonResult` and renders `report.html.j2` and `report.md.j2` using Jinja2.

## 3. Important Design Decisions & Constraints

- **Strict Validation Layer:** In `schemas/comparison.py`, we track `RejectedCandidate` and `DiscoveryMetrics`. The agent explicitly logs why it rejected sites to maintain transparency.
- **Token Efficiency:** The raw HTML is NEVER sent to the LLM. `extractor.py` slices the raw text. Even `content.raw_text_summary` is truncated to `[:2000]` characters in `prompts.py` to avoid massive Context Window overflows.
- **LLM Client Fallbacks:** `llm/client.py` (`safe_llm_call`) uses a fallback mechanism. If the primary model hits an OpenRouter Rate Limit (`429`), it cleanly catches it and falls back to a secondary model (e.g. `openrouter/owl-alpha`).
- **Gradio Interface:** The primary UI is `server.py` using `gradio`. It supports custom CSS themes and dynamically fetches models from OpenRouter.

## 4. Key Schemas (`schemas/`)
- `RawPage`: Raw HTML text split into tags.
- `LandingPageContent`: Structured marketing elements (CTAs, Trust Signals).
- `AuditResult`: CRO scoring and findings per category (Clarity, Friction, Trust, etc.).
- `CompetitorSummary`: The high-level score and confidence for a specific domain.
- `ComparisonResult`: The final monolithic object passed to Jinja2 templates containing Target, Competitors, Rejected Log, Metrics, Insights, and Benchmarks.

## 5. Next Steps / Typical Maintenance
If modifying the scraper, start in `scraper/fetch.py`.
If modifying what the LLM outputs, check `schemas/audit.py` or `schemas/comparison.py` AND `llm/prompts.py`.
If modifying the visual output, check `reports/templates/report.html.j2`.
