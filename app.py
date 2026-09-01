from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_store import build_district_summary, load_clean_df
from utils.modeling import get_feature_importance, get_metrics
from utils.ui import apply_theme, render_hero, section_title, style_chart


apply_theme("Mustard Yield Intelligence Dashboard", "🌾")


def _sidebar_nav() -> None:
    st.sidebar.title("🌾 Mustard Yield AI")
    st.sidebar.caption("Rajasthan Crop Intelligence Platform")
    st.sidebar.markdown("Use the page menu below to explore the dashboard.")
    st.sidebar.markdown("---")
    if hasattr(st.sidebar, "page_link"):
        st.sidebar.page_link("pages/1_Overview.py", label="Overview")
        st.sidebar.page_link("pages/2_District_Heatmap.py", label="District Heatmap")
        st.sidebar.page_link("pages/3_Farmer_Advisory.py", label="Farmer Advisory")
        st.sidebar.page_link("pages/4_Scenario_Simulator.py", label="Operations Console")
        st.sidebar.page_link("pages/7_Risk_Alerts.py", label="Risk Alerts")
    else:
        st.sidebar.markdown(
            """
            - `pages/1_Overview.py`
            - `pages/2_District_Heatmap.py`
            - `pages/3_Farmer_Advisory.py`
            - `pages/4_Scenario_Simulator.py`
            - `pages/7_Risk_Alerts.py`
            """
        )


_sidebar_nav()

loaded_at = datetime.now()
df = load_clean_df()
summary = build_district_summary()
metrics = get_metrics()


def _current_season() -> str:
    return "Rabi" if loaded_at.month in {10, 11, 12, 1, 2, 3} else "Kharif"


def _render_animated_kpis() -> None:
    kpi_values = [
        ("Districts", int(summary.shape[0])),
        ("Rows", int(len(df))),
        ("Avg yield", round(float(df["Yield (quintals)"].mean()), 1)),
        ("Model R2", round(float(metrics["r2"]), 3)),
    ]
    cards = "".join(
        f'<div class="counter-card"><div class="counter-value" data-target="{value}">0</div><div class="counter-label">{label}</div></div>'
        for label, value in kpi_values
    )
    st.markdown(
        f"""
        <style>
        .counter-grid {{
            display:grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
            margin: 0.7rem 0 1rem 0;
        }}
        .counter-card {{
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(26,46,26,0.1);
            border-radius: 14px;
            padding: 0.85rem 0.9rem;
        }}
        .counter-value {{
            font-family: 'Bebas Neue', cursive;
            color: #1a2e1a;
            font-size: 2rem;
            line-height: 1;
            letter-spacing: 0.03em;
        }}
        .counter-label {{
            font-family: 'Space Mono', monospace;
            color: #2d5a1b;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-top: 0.25rem;
        }}
        </style>
        <div class="counter-grid">{cards}</div>
        <script>
        const counters = window.parent.document.querySelectorAll('.counter-value');
        counters.forEach((counter) => {{
            const target = parseFloat(counter.dataset.target);
            const duration = 950;
            const start = performance.now();
            const decimals = target % 1 === 0 ? 0 : (target.toString().split('.')[1] || '').length;
            const step = (now) => {{
                const progress = Math.min((now - start) / duration, 1);
                const value = target * progress;
                counter.textContent = value.toFixed(decimals);
                if (progress < 1) requestAnimationFrame(step);
            }};
            requestAnimationFrame(step);
        }});
        </script>
        """,
        unsafe_allow_html=True,
    )

render_hero(
    "Rajasthan Agri Intelligence",
    "MUSTARD YIELD\nPLATFORM",
    f"Built from {len(df):,} real records across {summary.shape[0]} districts. "
    f"The model bundle is trained from the local dataset when no saved artifact is present, so the dashboard stays fully data-driven.",
)

if int((summary["risk_band"] == "High").sum()) > 0:
    st.markdown(
        f"""
        <div style="background:#9f1c1c;color:#fff;padding:0.65rem 0.9rem;border-radius:10px;border:1px solid #7f1515;margin-bottom:0.8rem;">
            <strong>State Alert</strong>: {int((summary['risk_band'] == 'High').sum())} district(s) are in HIGH risk band.
            Immediate irrigation and nutrient intervention planning is recommended.
        </div>
        """,
        unsafe_allow_html=True,
    )

meta_left, meta_right = st.columns([0.7, 0.3])
meta_left.markdown(f"**Live Season Badge:** `{_current_season()}`")
meta_right.caption(f"Last updated: {loaded_at.strftime('%d %b %Y %I:%M:%S %p')}")

_render_animated_kpis()

action_cols = st.columns(3)
action_cols[0].page_link("pages/3_Farmer_Advisory.py", label="Advise a Farmer", icon="👨‍🌾", use_container_width=True)
action_cols[1].page_link("pages/2_District_Heatmap.py", label="View Risk Map", icon="🗺", use_container_width=True)
action_cols[2].page_link("pages/4_Scenario_Simulator.py", label="Run Scenario", icon="🧠", use_container_width=True)

st.markdown(
    """
    <div class="subtle-card">
        <span class="pill">Start here</span>
        <p style="margin:0.65rem 0 0 0; line-height:1.7;">
            Use the sidebar pages for the district heatmap, farmer advisory, operations console, and risk alerts.
            Every page reuses the same local dataset and the same model bundle so the numbers stay consistent across the app.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)
section_title("At A Glance")

top_district = summary.iloc[0]
worst_district = summary.sort_values("risk_score", ascending=False).iloc[0]
avg_yield = df["Yield (quintals)"].mean()
avg_rain = df["rain"].mean()

metric_cols = st.columns(4)
metric_cols[0].metric("Districts covered", summary.shape[0])
metric_cols[1].metric("Average yield", f"{avg_yield:.1f} quintals")
metric_cols[2].metric("Best district", top_district["District"])
metric_cols[3].metric("Model R²", f'{metrics["r2"]:.3f}')

left, right = st.columns([1.15, 0.85])

with left:
    section_title("District Performance")
    ranked = summary.head(10).sort_values("avg_yield", ascending=True)
    fig = px.bar(
        ranked,
        x="avg_yield",
        y="District",
        orientation="h",
        color="risk_band",
        color_discrete_map={"Low": "#2d5a1b", "Moderate": "#8fb87a", "High": "#d68910", "Critical": "#c0392b"},
        text=ranked["avg_yield"].round(1),
        title="Top districts by average yield",
    )
    style_chart(fig, height=380)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=True)
    selected = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
    if isinstance(selected, dict):
        points = selected.get("selection", {}).get("points", [])
        if points:
            idx = int(points[0].get("point_index", 0))
            chosen = ranked.iloc[idx]["District"]
            st.session_state["selected_district"] = chosen
            st.info(f"Selected {chosen}. Opening District Heatmap...")
            if hasattr(st, "switch_page"):
                st.switch_page("pages/2_District_Heatmap.py")

    section_title("Feature Importance")
    fi = get_feature_importance().head(8).sort_values("importance", ascending=True)
    fi_fig = px.bar(
        fi,
        x="importance",
        y="feature",
        orientation="h",
        color="importance",
        color_continuous_scale="YlGn",
    )
    style_chart(fi_fig, height=320)
    fi_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fi_fig, use_container_width=True)

with right:
    section_title("Model Quality")
    st.metric("Test R²", f'{metrics["r2"]:.3f}')
    st.metric("MAE", f'{metrics["mae"]:.2f} quintals')
    st.metric("RMSE", f'{metrics["rmse"]:.2f} quintals')
    if metrics.get("cv_r2") is not None:
        st.metric("Cross-val R²", f'{metrics["cv_r2"]:.3f} ± {metrics["cv_r2_std"]:.3f}')

    st.markdown("**Highest yield district**")
    st.write(f"{top_district['District']} at {top_district['avg_yield']:.1f} quintals/ha")
    st.markdown("**Highest risk district**")
    st.write(f"{worst_district['District']} with risk score {worst_district['risk_score']:.1f}")
    st.markdown("**Average rainfall**")
    st.write(f"{avg_rain:.1f} mm")

section_title("District Intelligence Table")
table_cols = [
    "District",
    "avg_yield",
    "total_production",
    "water_stress_ratio",
    "nutrient_index",
    "risk_score",
    "risk_band",
    "top_irrigation",
]
display_table = summary[table_cols].rename(
    columns={
        "avg_yield": "Avg yield",
        "total_production": "Total production",
        "water_stress_ratio": "Water stress",
        "nutrient_index": "Nutrient index",
        "risk_score": "Risk score",
        "risk_band": "Risk band",
        "top_irrigation": "Top irrigation",
    }
)
st.dataframe(display_table, use_container_width=True, hide_index=True)
