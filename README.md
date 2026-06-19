# 🚀 Landing Page Auditor AI & Competitor Intelligence

**An enterprise-grade, AI-powered Conversion Rate Optimization (CRO) auditor that turns any landing page into actionable marketing insights and performs deep competitive benchmarking.**

Landing Page Auditor AI doesn't just read websites; it scrapes them, structure-parses their marketing elements, evaluates them against rigorous CRO frameworks using advanced LLMs, and deploys autonomous agents to find and benchmark your exact competitors across local and global markets.

---

## 🛑 The Problem it Solves

1. **Manual CRO audits take hours:** Analyzing a landing page for clarity, friction, trust signals, and offer strength is tedious and subjective.
2. **Blind spots in competitive strategy:** Most tools just compare scores. You need to know *what* competitors are doing better and *how* to close the gap.
3. **Standard LLMs fail at raw HTML:** If you paste raw HTML into ChatGPT, it gets confused by the noise (scripts, CSS, SVG paths) and misses the actual marketing copy.
4. **Different markets need different context:** Searching for an Egyptian ecommerce store shouldn't bring up US competitors.

## 💡 The Solution

This tool solves these problems through a modular, agentic pipeline:
- **Stealth Scraping:** Uses `Scrapling` and headless browsers to bypass Cloudflare and render JavaScript-heavy SPAs automatically.
- **Smart Extraction:** Parses raw HTML into structured CRO elements (CTAs, Benefits, Testimonials) *before* the AI sees it. 
- **Autonomous Competitor Discovery:** Uses a ReAct-style agent with DuckDuckGo integration to find exact product/ecommerce competitors in a specific regional market, explicitly rejecting blogs, review sites, and login pages.
- **Deep Gap Analysis:** Audits the target page and 3-5 competitors simultaneously, then uses an LLM to generate strategic gap analysis, missing elements, and a prioritized action plan.
- **Client-Ready Reporting:** Generates interactive HTML and print-ready PDF reports containing the full CRO audit and competitor benchmark.
- **Web Interface:** Features a modern, premium Web UI powered by Gradio.

---

## 🛠️ Tech Stack & Technologies Used

- **Scraping:** `Scrapling`, `Playwright` (Stealth browser fallback).
- **AI & Agents:** `LiteLLM` (OpenRouter/OpenAI/Gemini), `Instructor` (Structured Pydantic JSON), DuckDuckGo Search (`duckduckgo-search`).
- **Reporting:** `Jinja2` (HTML templating), `markdown-pdf` / HTML to PDF tools.
- **Web UI:** `Gradio` with custom premium CSS and dark-mode themes.
- **Data Structures:** `Pydantic` v2.

---

## 📂 Project Architecture

```text
landing-page-auditor/
├── main.py               # CLI entry point (Typer + Rich)
├── server.py             # Gradio Web UI entry point (Main Interface)
├── pipeline.py           # Orchestrator (ties scraping and auditing together)
├── config/               # Environment & logging settings
├── schemas/              # Pydantic models (Data contracts between layers)
├── scraper/              # Fetch layer (Fast HTTP + Stealth Browser fallback)
├── extractor/            # Parses raw HTML into structured CRO elements
├── llm/                  # Prompts, Instructor integration, and AI logic
├── scoring/              # Mathematical weighting and grading logic
├── competitors/          # Agentic Competitor Discovery and Comparator pipelines
├── reports/              # HTML, PDF, and Markdown report generators
└── output/               # Auto-generated reports saved here
```

---

## 🚀 How to Install and Use

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Stealth Browsers
To ensure the app can scrape heavily protected or JavaScript-rendered websites:
```bash
python -m patchright install
# or playwright install depending on your setup
```

### 4. Setup API Keys
Copy the example environment file:
```bash
copy .env.example .env
```
Open `.env` and add your **OpenRouter API Key**.

---

## 💻 Usage

### 🖥️ 1. Premium Web UI (Recommended)
Launch the beautiful Gradio Web UI:
```bash
python server.py
```
Open your browser to `http://127.0.0.1:7860`. Paste your URL, select your target market (e.g. Egypt, Global, Saudi Arabia), select the LLM model, and click "Generate Intelligence Report". 

### ⌨️ 2. Command Line Interface (CLI)
For developers or batch processing:
```bash
python main.py audit https://example.com --market Egypt
```

---

## 🌍 Multilingual & Regional Support
- **Language Aware:** Evaluates pages in their native language (English, Arabic, etc.) without penalizing them, but outputs all findings in **Arabic** for Middle Eastern clients.
- **Market Aware:** The Competitor Discovery Agent restricts searches to your selected market (e.g. searching explicitly in Egypt to find local direct competitors rather than global giants).
