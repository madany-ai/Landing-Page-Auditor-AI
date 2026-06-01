# 🚀 Landing Page Auditor AI

**An enterprise-grade, AI-powered Conversion Rate Optimization (CRO) auditor that turns any landing page into actionable marketing insights.**

Landing Page Auditor AI doesn't just read websites; it scrapes them, structure-parses their marketing elements, evaluates them against rigorous CRO frameworks using advanced LLMs, and generates beautiful, client-ready reports in multiple formats.

---

## 🛑 The Problem it Solves

1. **Manual CRO audits take hours:** Analyzing a landing page for clarity, friction, trust signals, and offer strength is tedious and subjective.
2. **Standard LLMs fail at raw HTML:** If you paste raw HTML into ChatGPT, it gets confused by the noise (scripts, CSS, SVG paths) and misses the actual marketing copy.
3. **Modern websites block scrapers:** Single Page Applications (SPAs) and sites behind Cloudflare easily block standard HTTP requests, preventing automated analysis.
4. **Different pages need different rules:** An E-commerce product page (PDP) should not be judged by the same rigid standards as a long-form SaaS sales letter.

## 💡 The Solution

This tool solves these problems through a modular, agentic pipeline:
- **Stealth Scraping:** Uses `Scrapling` and headless `Patchright` browsers to bypass Cloudflare and render JavaScript-heavy SPAs automatically.
- **Smart Extraction:** A dedicated Extractor layer parses the raw HTML and categorizes it into clean, structured data (CTAs, Benefits, Testimonials, Pricing) *before* the AI sees it. 
- **Adaptive AI Evaluation:** Instructs the LLM to identify the *type* of page (e.g., E-commerce vs. Direct Response) and grades it fairly based on its specific context.
- **Weighted Scoring Engine:** Grades the page out of 100 across 8 proven conversion dimensions.
- **Client-Ready Reporting:** Generates interactive HTML, print-ready PDF, and Markdown reports.
- **Accessible GUI:** Features a clean, fully functional Desktop GUI (Tkinter) with full RTL (Arabic) support.

---

## 🛠️ Tech Stack & Technologies Used

- **Scraping:** `Scrapling`, `Playwright` / `Patchright` (for stealth browser fallback).
- **AI & LLM:** `LiteLLM` (allows using any model from OpenAI, Anthropic, Gemini, OpenRouter), `Instructor` (to force strict `Pydantic` JSON outputs from the LLM).
- **Reporting:** `Jinja2` (HTML templating), `markdown-pdf` (PDF generation), `Rich` (CLI styling).
- **GUI:** `Tkinter` with `arabic-reshaper` and `python-bidi` for flawless RTL Arabic rendering in the logs.
- **Data Structures:** `Pydantic` v2.

---

## 📂 Project Architecture

The project is cleanly separated into specialized modules (Separation of Concerns):

```text
landing-page-auditor/
├── main.py               # CLI entry point (Typer + Rich)
├── gui_app.py            # GUI entry point launcher
├── pipeline.py           # Orchestrator (ties all layers together)
├── config/               # Environment & logging settings
├── schemas/              # Pydantic models (Data contracts between layers)
├── scraper/              # Fetch layer (Fast HTTP + Stealth Browser fallback)
├── extractor/            # Parses raw HTML into structured CRO elements
├── llm/                  # Prompts, Instructor integration, and AI logic
├── scoring/              # Mathematical weighting and grading logic
├── reports/              # HTML, PDF, and Markdown report generators
├── gui/                  # Tkinter UI components and logic
└── output/               # Auto-generated reports saved here
```

---

## 🚀 How to Install and Use

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Install Dependencies
Clone the repository, then install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Install Stealth Browsers
To ensure the app can scrape heavily protected or JavaScript-rendered websites (like Shahid, Shopify stores, etc.), install the underlying browser binaries:
```bash
python -m patchright install
```

### 4. Setup API Keys
Copy the example environment file and add your LLM API key:
```bash
# Windows
copy .env.example .env
# Mac/Linux
cp .env.example .env
```
Open `.env` and add your **OpenRouter API Key** (or modify the code to use OpenAI/Gemini directly via LiteLLM).

---

## 💻 Usage

### 🖥️ 1. Graphical User Interface (GUI)
Launch the beautiful Desktop UI:
```bash
python gui_app.py
```
Just paste the URL, click "Run Audit", and watch the live logs. Once finished, click the buttons to open your PDF, HTML, or Markdown reports!

### ⌨️ 2. Command Line Interface (CLI)
For developers or batch processing, run it directly from the terminal:
```bash
python main.py https://example.com
```
To override the default AI model on the fly:
```bash
python main.py https://example.com --model google/gemini-flash-1.5
```

---

## 📊 How the Scoring Works

The LLM evaluates the extracted content and the Scoring Engine applies the following weights to generate a final score out of 100:

| Category               | Weight | Description |
|------------------------|--------|-------------|
| **Clarity**            | 20%    | Is the primary message instantly understandable? |
| **Value Proposition**  | 15%    | Does it clearly explain *why* the user should care? |
| **Offer Strength**     | 15%    | Is the core offer compelling and competitive? |
| **Trust Signals**      | 15%    | Are there reviews, guarantees, or security badges? |
| **CTA Quality**        | 10%    | Are Call-to-Actions visible, varied, and compelling? |
| **ICP Alignment**      | 10%    | Does it speak directly to the Ideal Customer Profile? |
| **Objection Handling** | 10%    | Does it answer common doubts and FAQs? |
| **Friction**           | 5%     | Are there confusing elements or too many choices? |

---

## 🌍 Multilingual Support (Arabic & English)
This tool is built with a deep understanding of RTL languages. 
- The Prompts instruct the LLM to output findings in **Arabic** while evaluating pages in their native language (without penalizing English pages for being in English).
- The Tkinter GUI is uniquely patched with `python-bidi` and `arabic-reshaper` to render Arabic logs beautifully right-to-left without letter-disconnection bugs.

---
*Built as a practical, production-ready implementation of Agentic AI workflows.*
