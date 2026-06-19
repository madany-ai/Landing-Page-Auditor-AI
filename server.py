"""
Gradio Web UI — Landing Page Auditor AI.

Provides two tabs:
  1. Single Audit: Audit one landing page
  2. Competitor Comparison: Audit + discover competitors + compare

Launch via: python server.py  or  python main.py serve
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.logging import setup_logging
setup_logging()

import gradio as gr
from loguru import logger

from pipeline import run_audit_pipeline
from competitors.comparator import run_competitor_pipeline
from scoring.scoring_engine import get_score_grade, get_score_label, get_score_color_hex


from llm.models_api import get_openrouter_models

# ── Available models ─────────────────────────────────────────────────────────
MODELS = get_openrouter_models()


# ══════════════════════════════════════════════════════════════════════════════
# Single Audit Logic
# ══════════════════════════════════════════════════════════════════════════════

def run_single_audit(url: str, model: str, progress=gr.Progress()):
    """Run audit pipeline and return formatted results."""
    if not url or not url.startswith("http"):
        raise gr.Error("❌ Please enter a valid URL starting with http:// or https://")

    progress(0.0, desc="🚀 Starting audit...")

    def _progress_cb(msg: str, step: int, total: int) -> None:
        progress(step / total, desc=f"[{step}/{total}] {msg}")

    try:
        data = run_audit_pipeline(url, model=model or None, progress_cb=_progress_cb)
    except Exception as exc:
        raise gr.Error(f"❌ Audit failed: {exc}")

    result = data["result"]
    score = data["overall_score"]
    grade = get_score_grade(score)
    label = get_score_label(score)
    color = get_score_color_hex(score)

    # ── Build results ────────────────────────────────────────────────────
    # Score summary
    score_md = f"""
## 📊 Audit Result: {score}/100 — {grade} ({label})

{result.executive_summary}
"""

    # Category scores table
    categories = [
        ("Clarity", result.clarity.score, "20%"),
        ("Value Proposition", result.value_proposition.score, "15%"),
        ("Offer Strength", result.offer.score, "15%"),
        ("Trust Signals", result.trust.score, "15%"),
        ("CTA Quality", result.cta.score, "10%"),
        ("ICP Alignment", result.icp.score, "10%"),
        ("Objection Handling", result.objections.score, "10%"),
        ("Friction", result.friction.score, "5%"),
    ]

    table_md = "### 📈 Category Scores\n\n"
    table_md += "| Category | Score | Weight | Rating |\n|---|---|---|---|\n"
    for name, s, w in categories:
        bar = "█" * int(s) + "░" * (10 - int(s))
        emoji = "🟢" if s >= 7 else "🟡" if s >= 5 else "🔴"
        table_md += f"| {name} | {emoji} {s}/10 | {w} | {bar} |\n"

    # Revenue leaks
    leaks_md = "### 🚨 Top Revenue Leaks\n\n"
    for i, leak in enumerate(result.top_revenue_leaks, 1):
        leaks_md += f"{i}. {leak}\n"

    # Strengths & Weaknesses
    sw_md = "### 💪 Strengths\n\n"
    for s in result.strengths:
        sw_md += f"- ✅ {s}\n"
    sw_md += "\n### ⚠️ Weaknesses\n\n"
    for w in result.weaknesses:
        sw_md += f"- ❌ {w}\n"

    # Detailed findings
    detail_md = "### 🔍 Detailed Findings & Recommendations\n\n"
    for name, s, w in categories:
        attr = name.lower().replace(" ", "_").replace("_strength", "").replace("_quality", "").replace("_alignment", "").replace("_handling", "")
        # Map display names to attribute names
        attr_map = {
            "Clarity": "clarity",
            "Value Proposition": "value_proposition",
            "Offer Strength": "offer",
            "Trust Signals": "trust",
            "CTA Quality": "cta",
            "ICP Alignment": "icp",
            "Objection Handling": "objections",
            "Friction": "friction",
        }
        cat = getattr(result, attr_map[name])
        detail_md += f"#### {name} ({cat.score}/10)\n\n"
        detail_md += "**Findings:**\n"
        for f in cat.findings:
            detail_md += f"- {f}\n"
        detail_md += "\n**Recommendations:**\n"
        for r in cat.recommendations:
            detail_md += f"- 💡 {r}\n"
        detail_md += "\n---\n\n"

    full_md = score_md + "\n" + table_md + "\n" + leaks_md + "\n" + sw_md + "\n" + detail_md

    # Report file paths
    report_info = f"""### 📁 Reports Saved
- 📄 Markdown: `{data['md_path']}`
- 🌐 HTML: `{data['html_path']}`
- 📕 PDF: `{data['pdf_path']}`
"""

    html_path = str(data['html_path'])
    pdf_path = str(data['pdf_path'])

    return full_md, report_info, html_path, pdf_path


# ══════════════════════════════════════════════════════════════════════════════
# Competitor Comparison Logic
# ══════════════════════════════════════════════════════════════════════════════

def run_comparison(url: str, model: str, market: str, num_competitors: int, progress=gr.Progress()):
    """Run competitor comparison pipeline and return formatted results."""
    if not url or not url.startswith("http"):
        raise gr.Error("❌ Please enter a valid URL starting with http:// or https://")

    num_competitors = int(num_competitors)
    progress(0.0, desc="🚀 Starting competitor analysis...")

    def _progress_cb(msg: str, step: int, total: int) -> None:
        progress(step / total, desc=f"[{step}/{total}] {msg}")

    try:
        result = run_competitor_pipeline(
            url, model=model or None,
            market=market,
            num_competitors=num_competitors,
            progress_cb=_progress_cb,
        )
    except Exception as exc:
        raise gr.Error(f"❌ Competitor analysis failed: {exc}")

    # ── Build comparison results ─────────────────────────────────────────
    target = result.target
    competitors = result.competitors
    insights = result.insights
    benchmarks = result.benchmarks

    comp_md = f"## 📊 Competitive Gap Analysis\n\n"

    # Quick Wins
    if insights.quick_wins:
        comp_md += "### ⚡ Quick Wins\n\n"
        for win in insights.quick_wins:
            comp_md += f"- {win}\n"
        comp_md += "\n"

    # Benchmarks
    comp_md += "### 📈 Category Benchmarks\n\n"
    comp_md += "| Category | Your Score | Competitor Avg | Gap |\n"
    comp_md += "|---|---|---|---|\n"
    
    def _b_row(name: str, b):
        c = "🟢" if b.gap >= 0 else "🔴"
        return f"| **{name}** | {b.target_score} | {b.competitor_average} | {c} {b.gap} |\n"

    comp_md += _b_row("Clarity", benchmarks.clarity)
    comp_md += _b_row("Value Prop", benchmarks.value_proposition)
    comp_md += _b_row("Offer", benchmarks.offer)
    comp_md += _b_row("Trust", benchmarks.trust)
    comp_md += _b_row("CTA", benchmarks.cta)
    comp_md += _b_row("ICP", benchmarks.icp)
    comp_md += _b_row("Objections", benchmarks.objections)
    comp_md += _b_row("Friction", benchmarks.friction)

    # Missing Elements & Advantages
    if insights.missing_elements:
        comp_md += "\n### 🔻 Missing Elements\n"
        for me in insights.missing_elements:
            comp_md += f"- {me}\n"
            
    if insights.competitive_advantages:
        comp_md += "\n### 💪 Your Advantages\n"
        for adv in insights.competitive_advantages:
            comp_md += f"- {adv}\n"

    # Deep Insights
    if insights.deep_insights:
        comp_md += "\n### 💡 Strategic Insights\n\n"
        for ins in insights.deep_insights:
            comp_md += f"#### {ins.observation}\n"
            comp_md += f"- **Evidence:** {ins.evidence}\n"
            comp_md += f"- **Business Impact:** {ins.impact}\n"
            comp_md += f"- **Recommendation:** {ins.recommendation}\n\n"

    # Action Plan
    if insights.action_plan:
        comp_md += "### 🚀 Prioritized Roadmap\n\n"
        comp_md += "| Priority | Action | Impact | Effort | Description |\n"
        comp_md += "|---|---|---|---|---|\n"
        for action in sorted(insights.action_plan, key=lambda x: x.priority):
            comp_md += f"| {action.priority} | **{action.title}** | {action.expected_impact} | {action.effort} | {action.description} |\n"

    report_info = f"### 📁 Report Saved\n- 🌐 HTML: `{result.html_path}`\n- 📕 PDF: `{result.pdf_path}`\n"
    return comp_md, report_info, str(result.html_path), str(result.pdf_path)


# ══════════════════════════════════════════════════════════════════════════════
# Gradio UI (Premium SaaS Mode)
# ══════════════════════════════════════════════════════════════════════════════

from gradio.themes.utils import colors, fonts

def create_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app with a premium SaaS aesthetic."""

    # ── Custom CSS ───────────────────────────────────────────────────────────
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #FFB50F;
        --secondary: #0F5FFF;
        --accent: #FF0628;
        --bg-color: #000000;
        --surface: #0a0a0a;
        --border-color: rgba(255, 255, 255, 0.08);
        --text-main: #ffffff;
        --text-muted: #a1a1aa;
    }
    
    body, .gradio-container, .gr-box, .gr-form {
        background-color: var(--bg-color) !important;
        font-family: 'Inter', sans-serif !important;
        color: var(--text-main) !important;
    }

    .gradio-container { 
        max-width: 800px !important; 
        margin: auto !important; 
        padding-top: 64px !important; 
        padding-bottom: 64px !important;
    }

    /* Hero Section */
    .hero-container {
        text-align: center;
        margin-bottom: 48px;
    }
    .hero-title { 
        font-weight: 800;
        font-size: 3.5rem;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin-bottom: 16px;
    }
    .hero-title span {
        color: var(--primary);
    }
    .hero-subtitle { 
        color: var(--text-muted); 
        font-size: 1.1rem; 
        font-weight: 400; 
        line-height: 1.6;
        max-width: 600px;
        margin: 0 auto;
    }

    /* Main Form Card */
    .main-card {
        background: var(--surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 32px !important;
        box-shadow: 0 24px 48px rgba(0,0,0,0.8), 0 0 0 1px inset rgba(255,255,255,0.03) !important;
    }

    /* Form Fields */
    .gr-input, .gr-dropdown, .gr-box {
        background-color: #121212 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
        transition: all 0.2s ease !important;
        padding: 12px 16px !important;
    }
    .gr-input:focus, .gr-dropdown:focus, .gr-box:focus-within {
        border-color: var(--secondary) !important;
        box-shadow: 0 0 0 3px rgba(15, 95, 255, 0.2) !important;
        outline: none !important;
    }
    
    /* Segmented Controls Wrapper (Hacky way to style radio) */
    .segmented-radio {
        background: #121212 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 6px !important;
    }

    /* Primary Button */
    #run-btn { 
        background: var(--primary) !important;
        color: #000000 !important;
        font-size: 1.1rem !important; 
        font-weight: 600 !important; 
        border-radius: 12px !important; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
        margin-top: 24px !important;
        padding: 16px !important;
        box-shadow: 0 4px 12px rgba(255, 181, 15, 0.2) !important;
    }
    #run-btn:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 8px 24px rgba(255, 181, 15, 0.4) !important; 
    }

    /* Output Section */
    .output-card {
        margin-top: 32px !important;
        padding: 32px !important;
        background: var(--surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
    }
    .output-card h2, .output-card h3 {
        color: white !important;
        font-weight: 600 !important;
        margin-bottom: 16px !important;
        margin-top: 32px !important;
    }
    .output-card h2:first-child { margin-top: 0 !important; }
    
    /* Clean Markdown Tables */
    .output-card table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 24px 0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid var(--border-color) !important;
        font-size: 0.9rem !important;
    }
    .output-card th {
        background: #141414 !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
        padding: 16px !important;
        border-bottom: 1px solid var(--border-color) !important;
        text-align: left !important;
    }
    .output-card td {
        padding: 16px !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        color: var(--text-main) !important;
        vertical-align: middle !important;
    }
    .output-card tr:last-child td { border-bottom: none !important; }
    
    /* Footer */
    .footer-text {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-top: 48px;
        padding-top: 24px;
        border-top: 1px solid var(--border-color);
    }
    .footer-text a {
        color: var(--secondary);
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    .footer-text a:hover {
        color: #3b82f6;
    }
    """

    # Minimal Dark Theme Foundation
    custom_theme = gr.themes.Base(
        primary_hue=colors.orange,
        secondary_hue=colors.blue,
        neutral_hue=colors.zinc,
    ).set(
        body_background_fill="#000000",
        block_background_fill="#0a0a0a",
        block_border_width="0px",
        block_shadow="none",
    )

    with gr.Blocks(title="Auditor AI | Premium", theme=custom_theme, css=css) as app:
        
        # ── Hero Section
        with gr.Column(elem_classes=["hero-container"]):
            gr.Markdown(
                """
                <div class="hero-title">Landing Page <span>Auditor AI</span></div>
                <div class="hero-subtitle">Optimize your conversion rate with AI. Analyze clarity, value proposition, and competitor gaps instantly.</div>
                """
            )

        # ── Main Input Card
        with gr.Column(elem_classes=["main-card"]):
            url_input = gr.Textbox(
                label="Target Landing Page URL",
                placeholder="https://your-product.com",
                lines=1,
                show_label=True,
            )
            
            with gr.Row():
                model_input = gr.Dropdown(
                    choices=MODELS,
                    value=MODELS[0],
                    label="AI Model Engine",
                    container=True
                )
                market_input = gr.Dropdown(
                    choices=["Global", "Egypt", "Saudi Arabia", "UAE", "Custom"],
                    value="Global",
                    label="Target Market",
                    container=True
                )
                
            competitor_slider = gr.Slider(
                minimum=1, maximum=5, value=3, step=1,
                label="Competitors to Analyze",
                visible=True,
            )

            run_btn = gr.Button("Generate Intelligence Report", elem_id="run-btn")

        # ── Output Area
        output_display = gr.Markdown(elem_classes=["output-card"], visible=False)

        with gr.Accordion("Report Downloads", open=True, visible=False) as downloads_group:
            report_info = gr.Markdown()
            with gr.Row():
                html_file = gr.File(label="HTML Report", interactive=False, visible=False)
                pdf_file = gr.File(label="PDF Report", interactive=False, visible=False)

        # Wrapper function to route to the unified pipeline
        def unified_audit(url, model, market, comp_count):
            # Render loading state on output display instantly
            yield (
                gr.update(value="### ⏳ Discovering competitors and generating intelligence report...", visible=True),
                gr.update(visible=False),
                gr.update(), gr.update(), gr.update()
            )
            
            try:
                md, info, html_path, pdf_path = run_comparison(url, model, market, comp_count)
                yield (
                    gr.update(value=md, visible=True), 
                    gr.update(visible=True), 
                    info, 
                    gr.update(value=html_path, visible=True), 
                    gr.update(value=pdf_path, visible=True)
                )
            except Exception as e:
                error_md = f"### <span style='color:#FF0628'>⚠️ Analysis Failed</span>\n\n```\n{str(e)}\n```"
                yield (
                    gr.update(value=error_md, visible=True),
                    gr.update(visible=False),
                    gr.update(), gr.update(), gr.update()
                )

        run_btn.click(
            fn=unified_audit,
            inputs=[url_input, model_input, market_input, competitor_slider],
            outputs=[output_display, downloads_group, report_info, html_file, pdf_file],
            show_progress="full",
        )

        # ── Footer
        gr.Markdown(
            """
            <div class="footer-text">
                Built with accuracy in mind. Powered by <b>LiteLLM</b> & <b>Scrapling</b>.<br>
                <a href="https://github.com/mohamed-madany/Landing-Page-Auditor-AI" target="_blank">View on GitHub</a>
            </div>
            """
        )

    return app

# ── Direct launch ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    share = os.environ.get("GRADIO_SHARE") == "True"
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share,
        inbrowser=True,
    )
