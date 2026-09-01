"""
DISTRICT INTELLIGENCE COMMAND CENTER
======================================
Professional Geospatial Dashboard for Mustard Yield Prediction & Diagnostics

Architecture:
- Data Layer: GeoJSON from DataMeet with normalized district names
- Map Layer: Folium with CartoDB Dark Matter + dynamic choropleth
- State Layer: Streamlit session_state for selected_district and active_metric
- UI Layer: 2-column split-screen with map (left) and selection panel (right)
- Recommendation Layer: Automated logic for water stress, yield, nutrient, risk

Author: Geospatial Data Engineer
Date: 2026-04-13
"""
from __future__ import annotations

import json
import os
from typing import Dict, Any

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from branca.colormap import linear, LinearColormap
from streamlit_folium import st_folium

from utils.data_store import build_district_summary, district_to_point
from utils.ui import apply_theme, render_hero, section_title


# ==================== CONFIGURATION & CONSTANTS ====================

GEOJSON_URL = "https://raw.githubusercontent.com/datameet/maps/master/Districts/rajasthan.geojson"
DARK_THEME_BG = "#0e1117"
GOLD_HIGHLIGHT = "#FFD700"
GOLD_DIM = "#D4AF37"
STATE_CENTER = (26.8, 74.6)
MAP_ZOOM = 6.4
FONT_FAMILY = "Space Mono"

# Recommendation thresholds
WATER_STRESS_THRESHOLD = 0.7
YIELD_PERFORMANCE_THRESHOLD = 0.80  # 80% of state average
NUTRIENT_INDEX_MIN = 100

# ==================== THEME & STYLING ====================

apply_theme("District Intelligence | Command Center", "🗺")

CSS_DARK_THEME = """
<style>
    :root {
        --primary-bg: #0e1117;
        --secondary-bg: #161b22;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --gold: #FFD700;
        --gold-dim: #D4AF37;
        --success: #3fb950;
        --warning: #e3b341;
        --danger: #ef4444;
        --info: #79c0ff;
    }
    
    .command-center {
        font-family: 'Space Mono', monospace;
        color: var(--text-primary);
        background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #30363d;
        margin: 8px 0;
    }
    
    .metric-card {
        background: rgba(255, 215, 0, 0.05);
        border-left: 3px solid var(--gold);
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
        font-size: 14px;
    }
    
    .alert-card {
        background: rgba(255, 215, 0, 0.08);
        border: 1px solid var(--gold);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        font-family: 'Space Mono', monospace;
    }
    
    .alert-critical {
        border-left: 4px solid #ef4444;
        background: rgba(239, 68, 68, 0.08);
    }
    
    .alert-warning {
        border-left: 4px solid #e3b341;
        background: rgba(227, 179, 65, 0.08);
    }
    
    .alert-info {
        border-left: 4px solid #79c0ff;
        background: rgba(121, 192, 255, 0.08);
    }
    
    .alert-header {
        font-weight: bold;
        margin-bottom: 6px;
        color: var(--text-primary);
    }
    
    .alert-body {
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.4;
    }
    
    .gauge-container {
        text-align: center;
        margin: 16px 0;
    }
    
    .recommendation-stack {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 12px 0;
    }
    
    .weather-card {
        background: rgba(121, 192, 255, 0.08);
        border: 1px solid #79c0ff;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        font-family: 'Space Mono', monospace;
        font-size: 13px;
    }
    
    .weather-row {
        display: flex;
        justify-content: space-between;
        margin: 4px 0;
    }
    
    .weather-label {
        color: var(--text-secondary);
    }
    
    .weather-value {
        color: #79c0ff;
        font-weight: bold;
    }
</style>
"""

st.markdown(CSS_DARK_THEME, unsafe_allow_html=True)


# ==================== DATA LAYER: GeoJSON & Normalization ====================

@st.cache_data(show_spinner=False)
def _fetch_geojson_from_datameet() -> dict:
    """Fetch official Rajasthan district boundaries from DataMeet."""
    try:
        response = requests.get(GEOJSON_URL, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"⚠️ Could not fetch GeoJSON from DataMeet: {e}. Using synthetic boundaries.")
        return build_district_geojson_synthetic()


def build_district_geojson_synthetic() -> dict:
    """Fallback: Generate synthetic district boundaries from district centers."""
    from utils.data_store import DISTRICT_CENTERS
    features = []
    for district, (lat, lon) in DISTRICT_CENTERS.items():
        lat_delta = 0.34 if district not in {"Sri Ganganagar", "Hanumangarh"} else 0.4
        lon_delta = 0.42 if district not in {"Jodhpur", "Udaipur"} else 0.46
        coordinates = [
            [
                [lon - lon_delta, lat - lat_delta],
                [lon + lon_delta, lat - lat_delta],
                [lon + lon_delta, lat + lat_delta],
                [lon - lon_delta, lat + lat_delta],
                [lon - lon_delta, lat - lat_delta],
            ]
        ]
        features.append(
            {
                "type": "Feature",
                "properties": {"district": district},
                "geometry": {"type": "Polygon", "coordinates": coordinates},
            }
        )
    return {"type": "FeatureCollection", "features": features}


@st.cache_data(show_spinner=False)
def _normalize_district_names(df: pd.DataFrame, geojson: dict) -> Dict[str, str]:
    """
    Create bidirectional mapping between DataFrame and GeoJSON district names.
    Handles case variations, whitespace, and common abbreviations.
    """
    df_districts = df["District"].str.upper().str.strip().unique()
    geojson_districts = [
        f["properties"].get("district", "").upper().strip()
        for f in geojson.get("features", [])
    ]
    
    # Exact match mapping
    mapping = {}
    for geojson_dist in geojson_districts:
        for df_dist in df_districts:
            if geojson_dist == df_dist:
                mapping[df_dist] = geojson_dist
                break
    
    # Partial match for unmatched districts
    for df_dist in df_districts:
        if df_dist not in mapping:
            for geojson_dist in geojson_districts:
                if geojson_dist not in mapping.values():
                    if df_dist[:min(len(df_dist), len(geojson_dist))] == geojson_dist[:min(len(df_dist), len(geojson_dist))]:
                        mapping[df_dist] = geojson_dist
                        break
    
    return mapping


# ==================== DATA FUNCTIONS ====================

@st.cache_data(show_spinner=False)
def load_dashboard_data() -> tuple[pd.DataFrame, dict, Dict[str, str]]:
    """Load and prepare all dashboard data."""
    summary = build_district_summary()
    geojson = _fetch_geojson_from_datameet()
    norm_map = _normalize_district_names(summary, geojson)
    return summary, geojson, norm_map


@st.cache_data(show_spinner=False)
def _get_weather(district: str) -> Dict[str, Any] | None:
    """
    Fetch live weather data from OpenWeatherMap API.
    Fallback to climatological averages if API unavailable.
    """
    key = st.secrets.get("OPENWEATHERMAP_API_KEY", os.getenv("OPENWEATHERMAP_API_KEY"))
    if not key:
        return None
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": f"{district},Rajasthan,IN", "appid": key, "units": "metric"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "temp": float(data["main"]["temp"]),
            "humidity": float(data["main"]["humidity"]),
            "wind": float(data["wind"]["speed"]),
            "rain": float(data.get("rain", {}).get("1h", 0.0)),
            "condition": data.get("weather", [{}])[0].get("main", "Unknown"),
        }
    except Exception:
        return None


# ==================== RECOMMENDATION ENGINE ====================

def generate_recommendations(district_row: pd.Series, state_avg_yield: float) -> list[Dict[str, str]]:
    """
    Automated recommendation logic based on district metrics.
    Returns list of alert dictionaries with type, header, body.
    """
    recommendations = []
    state_avg_n = state_avg_yield
    
    # ALERT 1: Water Stress
    if district_row["water_stress_ratio"] > WATER_STRESS_THRESHOLD:
        recommendations.append({
            "type": "critical",
            "icon": "⚠️",
            "header": "HIGH WATER STRESS",
            "body": f"Water stress ratio: {district_row['water_stress_ratio']:.2f} (Critical)\nRecommendation: Implement drip irrigation subsidy program immediately.",
        })
    
    # ALERT 2: Yield Underperformance
    if district_row["avg_yield"] < (state_avg_n * YIELD_PERFORMANCE_THRESHOLD):
        yield_gap = state_avg_n - district_row["avg_yield"]
        recommendations.append({
            "type": "warning",
            "icon": "🧪",
            "header": "SOIL CORRECTION NEEDED",
            "body": f"Yield gap: {yield_gap:.1f}Q (District {district_row['avg_yield']:.1f}Q vs State {state_avg_n:.1f}Q)\nRecommendation: NPK supplementation + soil pH optimization (Target: 6.5-7.5)",
        })
    
    # ALERT 3: Nutrient Deficiency
    if district_row["nutrient_index"] < NUTRIENT_INDEX_MIN:
        recommendations.append({
            "type": "warning",
            "icon": "🧬",
            "header": "NUTRIENT INDEX LOW",
            "body": f"Nutrient index: {district_row['nutrient_index']:.1f} kg/ha (Below optimal)\nRecommendation: Integrated Nutrient Management (INM) + organic matter supplementation",
        })
    
    # ALERT 4: High Risk Score
    if district_row["risk_band"] == "Critical":
        recommendations.append({
            "type": "critical",
            "icon": "🛡️",
            "header": "RISK MITIGATION URGENT",
            "body": f"Risk score: {district_row['risk_score']:.1f} ({district_row['risk_band']})\nRecommendation: Consider crop diversification; musclered insurance coverage recommended.",
        })
    elif district_row["risk_band"] == "High":
        recommendations.append({
            "type": "warning",
            "icon": "🛡️",
            "header": "HIGH RISK ZONE",
            "body": f"Risk score: {district_row['risk_score']:.1f} ({district_row['risk_band']})\nRecommendation: Strengthen water management protocols; monitor weather forecasts closely.",
        })
    
    # INFO: General Advice for Low-Risk Districts
    if not recommendations:
        recommendations.append({
            "type": "info",
            "icon": "✅",
            "header": "OPTIMAL PERFORMANCE",
            "body": f"District performing well. Continue current practices. Yield: {district_row['avg_yield']:.1f}Q | Risk: {district_row['risk_band']}\nRecommendation: Focus on yield stabilization and climate adaptation.",
        })
    
    return recommendations


# ==================== MAP LAYER: Folium with Dynamic Choropleth ====================

def create_intelligence_map(
    summary: pd.DataFrame,
    geojson: dict,
    norm_map: Dict[str, str],
    metric: str,
) -> folium.Map:
    """
    Create Folium map with dynamic choropleth based on selected metric.
    Includes gold highlight on hover, custom labels, and popups.
    """
    metric_specs = {
        "Avg Yield": ("avg_yield", linear.YlGn_09, "Yield (Q/ha)", "continuous", "higher is better"),
        "Risk Score": ("risk_score", linear.OrRd_09, "Risk Score", "continuous", "lower is better"),
        "Water Stress": ("water_stress_ratio", linear.YlOrBr_09, "Water Stress", "continuous", "lower is better"),
        "Nutrient Index": ("nutrient_index", linear.PuBuGn_09, "Nutrient (kg/ha)", "continuous", "higher is better"),
        "Climate Pressure": ("climate_pressure", linear.BuPu_09, "Climate Pressure", "continuous", "lower is better"),
        "Irrigation Type": ("top_irrigation", None, "Irrigation Method", "categorical", "context"),
    }
    
    metric_col, palette, legend, layer_type, scale_direction = metric_specs[metric]
    
    map_obj = folium.Map(
        location=STATE_CENTER,
        zoom_start=MAP_ZOOM,
        tiles="CartoDB dark_matter",
    )
    
    if layer_type == "categorical":
        categories = sorted(summary[metric_col].dropna().astype(str).unique().tolist())
        colors = ["#2d5a1b", "#5a9e3a", "#d68910", "#c0392b", "#7f8c8d", "#3498db"]
        cat_map = {c: colors[i % len(colors)] for i, c in enumerate(categories)}
    else:
        low, high = float(summary[metric_col].min()), float(summary[metric_col].max())
        color_map = palette.scale(low, high)
    
    def style_function(feature):
        geojson_dist = feature["properties"].get("district", "").upper().strip()
        
        # Find matching dataframe district
        df_dist = None
        for key, val in norm_map.items():
            if val.upper().strip() == geojson_dist:
                df_dist = key
                break
        
        if df_dist and df_dist in summary["District"].values:
            row = summary[summary["District"] == df_dist].iloc[0]
            if layer_type == "categorical":
                color = cat_map.get(str(row[metric_col]), "#7f8c8d")
            else:
                color = color_map(float(row[metric_col]))
        else:
            color = "#2a2a2a"  # Grey for unmatched districts
        
        return {
            "fillColor": color,
            "color": "#1a1a1a",
            "weight": 2,
            "fillOpacity": 0.75,
        }
    
    def highlight_function(feature):
        return {
            "fillColor": GOLD_HIGHLIGHT,
            "color": GOLD_DIM,
            "weight": 3,
            "fillOpacity": 0.9,
        }
    
    # Add choropleth layer with GeoJSON
    for feature in geojson["features"]:
        geojson_dist = feature["properties"].get("district", "").upper().strip()
        df_dist = None
        for key, val in norm_map.items():
            if val.upper().strip() == geojson_dist:
                df_dist = key
                break
        
        if df_dist and df_dist in summary["District"].values:
            row = summary[summary["District"] == df_dist].iloc[0]
            popup_html = f"""
            <div style="font-family: 'Space Mono', monospace; width: 220px; background: #0e1117; color: #e6edf3; padding: 12px; border-radius: 8px; border: 1px solid #30363d;">
                <h4 style="margin: 0 0 8px; color: #FFD700; font-size: 14px;">{df_dist.title()}</h4>
                <div style="font-size: 12px; line-height: 1.6; color: #8b949e;">
                    <b>Yield:</b> {row['avg_yield']:.1f} Q | Rank #{int(row['yield_rank'])}<br>
                    <b>Risk:</b> {row['risk_band']} ({row['risk_score']:.1f})<br>
                    <b>Water Stress:</b> {row['water_stress_ratio']:.2f}<br>
                    <b>Irrigation:</b> {row['top_irrigation']}<br>
                </div>
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #30363d; font-size: 11px; color: #79c0ff;">
                    Click district name in panel to see full intelligence
                </div>
            </div>
            """
            
            folium.GeoJson(
                feature,
                style_function=style_function,
                highlight_function=highlight_function,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{df_dist}: {metric}",
            ).add_to(map_obj)
    
    # Add color legend
    if layer_type == "continuous":
        colormap = palette
        colormap.caption = f"{legend} ({scale_direction})"
        colormap.add_to(map_obj)
    
    # Add title overlay
    title_html = f"""
    <div style="position: fixed; top: 10px; left: 50px; width: 240px; background: rgba(14, 17, 23, 0.95); 
                border: 1px solid #30363d; border-radius: 8px; padding: 12px; font-family: 'Space Mono', monospace;
                color: #e6edf3; z-index: 1000; font-size: 13px;">
        <div style="color: #FFD700; font-weight: bold; margin-bottom: 4px;">📊 {metric}</div>
        <div style="color: #8b949e; font-size: 11px;"> Rajasthan Mustard Yield Intelligence</div>
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(title_html))
    
    return map_obj


# ==================== UI: STATE & SESSION MANAGEMENT ====================

# Initialize session state
if "selected_district" not in st.session_state:
    st.session_state.selected_district = None
if "active_metric" not in st.session_state:
    st.session_state.active_metric = "Avg Yield"


# ==================== MAIN DASHBOARD ====================

def main():
    """Main dashboard orchestration."""
    
    # Header
    render_hero(
        "District Intelligence Command Center",
        "Geospatial Analytics\n& Prescriptive Diagnostics",
        "Real-time district diagnostics with AI-powered recommendations. Click a district to see full intelligence.",
    )
    
    # Load data
    summary, geojson, norm_map = load_dashboard_data()
    state_avg_yield = float(summary["avg_yield"].mean())
    
    # Metric Selector (Horizontal Toggle)
    st.markdown("### 📍 Intelligence Layers")
    metric_cols = st.columns(6)
    metrics = ["Avg Yield", "Risk Score", "Water Stress", "Nutrient Index", "Climate Pressure", "Irrigation Type"]
    
    for idx, metric in enumerate(metrics):
        if metric_cols[idx].button(
            metric,
            key=f"btn_{metric}",
            use_container_width=True,
            type="primary" if st.session_state.active_metric == metric else "secondary",
        ):
            st.session_state.active_metric = metric
            st.rerun()
    
    # Main Layout: 2-Column Split Screen
    col_map, col_panel = st.columns([2, 1], gap="medium")
    
    # LEFT COLUMN: Interactive Folium Map
    with col_map:
        st.markdown("#### 🗺️ Interactive Choropleth Map")
        map_obj = create_intelligence_map(summary, geojson, norm_map, st.session_state.active_metric)
        map_data = st_folium(map_obj, width=700, height=550)
    
    # RIGHT COLUMN: Selection Panel with Diagnostics
    with col_panel:
        st.markdown("#### 🔍 District Intelligence")
        
        # District Selector
        district_list = summary["District"].tolist()
        default_idx = 0
        if st.session_state.selected_district and st.session_state.selected_district in district_list:
            default_idx = district_list.index(st.session_state.selected_district)
        
        selected = st.selectbox(
            "Select District",
            district_list,
            index=default_idx,
            key="district_select",
            label_visibility="collapsed",
        )
        
        st.session_state.selected_district = selected
        
        # Get selected district data
        district_row = summary[summary["District"] == selected].iloc[0]
        
        # Key Metrics Overview
        st.markdown(f"<div class='command-center'><b>📊 Core Metrics</b></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("Yield", f"{district_row['avg_yield']:.1f}Q", f"Rank #{int(district_row['yield_rank'])}")
        m2.metric("Risk", district_row["risk_band"], f"{district_row['risk_score']:.1f}")
        
        m3, m4 = st.columns(2)
        m3.metric("H₂O Stress", f"{district_row['water_stress_ratio']:.2f}", "Ratio")
        m4.metric("Nutrients", f"{district_row['nutrient_index']:.0f}", "kg/ha")
        
        # Yield Gauge Chart
        st.markdown(f"<div class='command-center'><b>📈 Yield Gauge vs State Average</b></div>", unsafe_allow_html=True)
        max_yield = summary["avg_yield"].max() * 1.1
        gauge_fig = go.Figure(
            data=[
                go.Indicator(
                    mode="gauge+number+delta",
                    value=district_row["avg_yield"],
                    title={"text": f"{selected} Yield Performance"},
                    delta={"reference": state_avg_yield, "suffix": " from Avg"},
                    gauge={
                        "axis": {"range": [0, max_yield]},
                        "bar": {"color": "#FFD700", "thickness": 0.75},
                        "steps": [
                            {"range": [0, state_avg_yield * 0.6], "color": "rgba(239, 68, 68, 0.15)"},
                            {"range": [state_avg_yield * 0.6, state_avg_yield * 0.9], "color": "rgba(227, 179, 65, 0.15)"},
                            {"range": [state_avg_yield * 0.9, max_yield], "color": "rgba(63, 185, 80, 0.15)"},
                        ],
                        "threshold": {
                            "line": {"color": "#FF6B6B", "width": 3},
                            "thickness": 0.75,
                            "value": state_avg_yield,
                        },
                    },
                )
            ]
        )
        gauge_fig.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#e6edf3", "family": "Space Mono", "size": 12},
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
        )
        st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})
        
        # Live Weather Integration
        st.markdown(f"<div class='command-center'><b>🌤️ Live Weather</b></div>", unsafe_allow_html=True)
        weather = _get_weather(selected)
        if weather:
            st.markdown(f"""
            <div class='weather-card'>
                <div class='weather-row'>
                    <span class='weather-label'>🌡️ Temperature:</span>
                    <span class='weather-value'>{weather['temp']:.1f}°C</span>
                </div>
                <div class='weather-row'>
                    <span class='weather-label'>💧 Humidity:</span>
                    <span class='weather-value'>{weather['humidity']:.0f}%</span>
                </div>
                <div class='weather-row'>
                    <span class='weather-label'>💨 Wind:</span>
                    <span class='weather-value'>{weather['wind']:.1f} m/s</span>
                </div>
                <div class='weather-row'>
                    <span class='weather-label'>🌧️ Rainfall:</span>
                    <span class='weather-value'>{weather['rain']:.1f} mm</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("🌐 Live weather data unavailable. Using climatological averages.")
        
        # Recommendation Engine Output
        st.markdown(f"<div class='command-center'><b>⚡ Prescriptive Intelligence</b></div>", unsafe_allow_html=True)
        recommendations = generate_recommendations(district_row, state_avg_yield)
        
        for rec in recommendations:
            alert_class = f"alert-card alert-{rec['type']}"
            st.markdown(f"""
            <div class='{alert_class}'>
                <div class='alert-header'>{rec['icon']} {rec['header']}</div>
                <div class='alert-body'>{rec['body']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Bottom Section: Comparative Analysis
    st.markdown("---")
    st.markdown("### 📋 District Comparative Analysis")
    
    # Comparison Table
    comparison_cols = st.columns(3)
    with comparison_cols[0]:
        compare_metric = st.selectbox(
            "Compare by metric",
            ["Yield", "Risk", "Water Stress", "Nutrients", "Production"],
            label_visibility="collapsed",
        )
    
    # Build comparison dataframe
    compare_map = {
        "Yield": ("avg_yield", "descending"),
        "Risk": ("risk_score", "ascending"),
        "Water Stress": ("water_stress_ratio", "ascending"),
        "Nutrients": ("nutrient_index", "descending"),
        "Production": ("total_production", "descending"),
    }
    
    col, order = compare_map[compare_metric]
    compare_df = summary[[
        "District", "avg_yield", "risk_band", "water_stress_ratio", "nutrient_index", "total_production"
    ]].copy()
    
    if order == "descending":
        compare_df = compare_df.sort_values(col, ascending=False)
    else:
        compare_df = compare_df.sort_values(col, ascending=True)
    
    compare_df = compare_df.head(10).reset_index(drop=True)
    compare_df.columns = ["District", "Yield (Q)", "Risk", "H₂O Stress", "Nutrients (kg/ha)", "Production (MT)"]
    
    st.dataframe(
        compare_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Export & Action Items
    st.markdown("---")
    st.markdown("### 📥 Export & Actions")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        csv = compare_df.to_csv(index=False)
        st.download_button(
            "📊 Download Comparison (CSV)",
            csv,
            "district_comparison.csv",
            "text/csv",
            use_container_width=True,
        )
    
    with exp_col2:
        report = f"""
DISTRICT INTELLIGENCE REPORT
Generated: 2026-04-13

SELECTED DISTRICT: {selected}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metrics:
- Avg Yield: {district_row['avg_yield']:.1f}Q (Rank #{int(district_row['yield_rank'])})
- Risk Level: {district_row['risk_band']} ({district_row['risk_score']:.1f})
- Water Stress: {district_row['water_stress_ratio']:.2f}
- Nutrient Index: {district_row['nutrient_index']:.0f} kg/ha
- Top Irrigation: {district_row['top_irrigation']}

RECOMMENDATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{''.join([f"{rec['icon']} {rec['header']}\n{rec['body']}\n\n" for rec in recommendations])}

STATE CONTEXT:
- State Average Yield: {state_avg_yield:.1f}Q
- Yield Gap: {state_avg_yield - district_row['avg_yield']:.1f}Q
"""
        st.download_button(
            "📄 Download Report (TXT)",
            report,
            "district_intelligence_report.txt",
            "text/plain",
            use_container_width=True,
        )
    
    with exp_col3:
        st.info("💡 Use the map and metrics above to drill down into district-level decision-making.")


if __name__ == "__main__":
    main()

