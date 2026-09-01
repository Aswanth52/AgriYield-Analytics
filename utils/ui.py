from __future__ import annotations

from typing import Any

import streamlit as st


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --bg: #f5f2eb;
    --panel: #1a2e1a;
    --panel-2: #2d5a1b;
    --accent: #5a9e3a;
    --accent-2: #8fb87a;
    --muted: #c8d5b9;
    --text: #1a2e1a;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, rgba(90,158,58,0.08), transparent 32%),
                linear-gradient(180deg, #f7f4ee 0%, #f3efe7 100%);
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #132213 0%, #1a2e1a 100%);
    border-right: 1px solid rgba(143,184,122,0.2);
}

[data-testid="stSidebar"] * {
    color: var(--muted) !important;
}

[data-testid="stAppViewContainer"] :where(p, label, span, li, div) {
    color: var(--text);
}

[data-testid="stAppViewContainer"] .stMarkdown,
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown span,
[data-testid="stAppViewContainer"] .stMarkdown li {
    color: var(--text);
}

[data-testid="stAppViewContainer"] [data-baseweb="select"] * {
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] [data-baseweb="input"] * {
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] [role="textbox"] {
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] .stDataFrame,
[data-testid="stAppViewContainer"] .stTable {
    color: var(--text);
}

header, footer {
    background: transparent !important;
}

.block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
    max-width: 100% !important;
}

.hero-banner {
    background: linear-gradient(135deg, #132213 0%, #1a2e1a 48%, #2d5a1b 100%);
    padding: 2.2rem 2.4rem 1.8rem 2.4rem;
    margin: -0.4rem -1rem 1.5rem -1rem;
    border-bottom: 4px solid #5a9e3a;
    position: relative;
    overflow: hidden;
}

.hero-banner::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 80% 10%, rgba(143,184,122,0.18), transparent 24%),
        radial-gradient(circle at 10% 80%, rgba(255,255,255,0.05), transparent 18%);
    pointer-events: none;
}

.hero-eyebrow {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #c8d5b9;
    background: rgba(90,158,58,0.18);
    border: 1px solid rgba(143,184,122,0.25);
    padding: 0.35rem 0.7rem;
    margin-bottom: 0.85rem;
    position: relative;
    z-index: 1;
}

.hero-title {
    font-family: 'Bebas Neue', cursive;
    font-size: clamp(2.8rem, 6vw, 5.8rem);
    color: #f5f2eb;
    line-height: 0.92;
    margin: 0 0 0.65rem 0;
    letter-spacing: 0.02em;
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    max-width: 56rem;
    color: #d5e2c7;
    font-family: 'DM Sans', sans-serif;
    line-height: 1.7;
    position: relative;
    z-index: 1;
}

.section-header {
    font-family: 'Bebas Neue', cursive;
    font-size: 1.95rem;
    color: #1a2e1a;
    letter-spacing: 0.05em;
    margin: 0.3rem 0 0.85rem 0;
    border-left: 6px solid #5a9e3a;
    padding-left: 0.9rem;
}

.subtle-card {
    background: rgba(255,255,255,0.58);
    border: 1px solid rgba(26,46,26,0.08);
    border-radius: 1rem;
    padding: 1rem 1.1rem;
    box-shadow: 0 8px 26px rgba(26,46,26,0.06);
}

.pill {
    display: inline-block;
    padding: 0.3rem 0.65rem;
    border-radius: 999px;
    background: rgba(90,158,58,0.12);
    color: #1a2e1a;
    border: 1px solid rgba(90,158,58,0.25);
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
</style>
"""


def apply_theme(page_title: str, page_icon: str = "🌾") -> None:
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide", initial_sidebar_state="expanded")
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def style_chart(fig: Any, height: int | None = None) -> Any:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f5f2eb",
        font=dict(family="Space Mono", color="#1a2e1a"),
        legend=dict(font=dict(color="#1a2e1a")),
    )
    fig.update_xaxes(title_font=dict(color="#1a2e1a"), tickfont=dict(color="#1a2e1a"), gridcolor="rgba(26,46,26,0.12)")
    fig.update_yaxes(title_font=dict(color="#1a2e1a"), tickfont=dict(color="#1a2e1a"), gridcolor="rgba(26,46,26,0.12)")
    if height is not None:
        fig.update_layout(height=height)

    for trace in fig.data:
        if hasattr(trace, "textfont"):
            trace.update(textfont=dict(color="#1a2e1a"))

    return fig

