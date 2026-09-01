from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_store import build_district_summary, load_clean_df
from utils.ui import apply_theme, render_hero, section_title, style_chart


apply_theme("Risk Alerts | Mustard Yield Intelligence", "⚠")

summary = build_district_summary().copy()
df = load_clean_df().copy()

render_hero(
    "Risk Alerts",
    "Early Warning\nand Intervention Dashboard",
    "Tune the alert threshold and surface the districts that need irrigation, soil, or climate attention right now.",
)

threshold = st.slider("Alert threshold", 0.0, 100.0, float(summary["risk_score"].quantile(0.75)), 0.1)
alerts = summary[summary["risk_score"] >= threshold].sort_values("risk_score", ascending=False)

section_title("Traffic Light Summary")
metric_cols = st.columns(4)
metric_cols[0].metric("Critical", int((summary["risk_band"] == "Critical").sum()))
metric_cols[1].metric("High", int((summary["risk_band"] == "High").sum()))
metric_cols[2].metric("Moderate", int((summary["risk_band"] == "Moderate").sum()))
metric_cols[3].metric("Low", int((summary["risk_band"] == "Low").sum()))

section_title("Risk Distribution")
fig = px.histogram(summary, x="risk_score", color="risk_band", nbins=10)
style_chart(fig, height=320)
st.plotly_chart(fig, use_container_width=True)

section_title("Alert Timeline")
timeline = alerts.copy()
timeline["primary_risk_factor"] = timeline.apply(
    lambda r: "Water Stress" if r["water_stress_ratio"] >= summary["water_stress_ratio"].median() else "Yield Deficit",
    axis=1,
)
timeline["recommended_action"] = timeline.apply(
    lambda r: "Emergency drip irrigation advisory" if r["primary_risk_factor"] == "Water Stress" else "NPK supplementation and soil correction",
    axis=1,
)
timeline_show = timeline[["District", "risk_band", "risk_score", "primary_risk_factor", "recommended_action"]]
st.dataframe(timeline_show, use_container_width=True, hide_index=True)

section_title("Risk Trend Indicator")
season_trend = (
    df.assign(
        water_stress=df["Water Consumption (liters/hectare)"] / (df["Water Availability (liters/hectare)"] + 1),
        nutrient_index=df["Nitrogen Content (kg/ha)"] + df["Phosphorus Content (kg/ha)"] + df["Potassium Content (kg/ha)"],
    )
    .groupby("Season")
    .agg(risk_proxy=("water_stress", "mean"), nutrient_proxy=("nutrient_index", "mean"))
    .reset_index()
)
trend_chart = px.line(season_trend, x="Season", y="risk_proxy", markers=True, title="Seasonal risk proxy")
style_chart(trend_chart, height=280)
st.plotly_chart(trend_chart, use_container_width=True)

direction = "improving" if season_trend["risk_proxy"].iloc[-1] <= season_trend["risk_proxy"].iloc[0] else "worsening"
st.info(f"Risk trend appears {direction} based on seasonal water-stress proxy.")

section_title("Intervention Priority Ranker")
priority = alerts.copy()
priority["yield_gap_ratio"] = (summary["avg_yield"].mean() - priority["avg_yield"]).clip(lower=0) / summary["avg_yield"].mean()
priority["intervention_priority"] = (priority["risk_score"] * 0.6 + priority["yield_gap_ratio"] * 100 * 0.4).round(2)
priority = priority.sort_values("intervention_priority", ascending=False)
st.dataframe(
    priority[["District", "risk_score", "water_stress_ratio", "yield_gap_ratio", "intervention_priority"]],
    use_container_width=True,
    hide_index=True,
)

section_title("Alert Cards")
state_avg = float(summary["avg_yield"].mean())
for _, row in alerts.head(6).iterrows():
    icon = "🔴" if row["risk_band"] == "Critical" else "🟠" if row["risk_band"] == "High" else "🟡"
    primary = "Water Stress" if row["water_stress_ratio"] >= summary["water_stress_ratio"].median() else "Low Yield"
    secondary = "Low Nutrient Index" if row["nutrient_index"] < summary["nutrient_index"].median() else "Climate Pressure"
    predicted = row["avg_yield"] * 0.95
    st.markdown(
        f"""
        **{icon} {row['District'].upper()} - {row['risk_band']}**  
        Water Stress: {row['water_stress_ratio']:.2f} (threshold: {summary['water_stress_ratio'].median():.2f})  
        Nutrient Index: {row['nutrient_index']:.1f} (state avg: {summary['nutrient_index'].mean():.1f})  
        Predicted Yield: {predicted:.1f} Q ({((state_avg - predicted)/state_avg*100):.0f}% below state avg)  
        Primary cause: {primary} | Secondary: {secondary}  
        Recommended Actions:  
        - Issue drip irrigation advisory immediately  
        - Subsidize NPK fertilizer this season  
        - Consider crop insurance enrollment
        """
    )
    st.markdown("---")

section_title("Filtered Table")
st.dataframe(
    alerts[
        ["District", "avg_yield", "water_stress_ratio", "risk_score", "risk_band", "top_irrigation", "top_soil"]
    ].rename(
        columns={
            "avg_yield": "Avg yield",
            "water_stress_ratio": "Water stress",
            "risk_score": "Risk score",
            "risk_band": "Risk band",
            "top_irrigation": "Top irrigation",
            "top_soil": "Top soil",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

section_title("Download Alert Report")
report_lines = [
    "Mustard Risk Alert Summary",
    f"Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}",
    "",
]
for _, row in alerts.iterrows():
    report_lines.append(
        f"{row['District']} | {row['risk_band']} | Risk {row['risk_score']:.1f} | Water stress {row['water_stress_ratio']:.2f} | Action: Drip + NPK support"
    )
report_blob = "\n".join(report_lines)
st.download_button("Download policy alert summary", report_blob.encode("utf-8"), "risk_alert_summary.txt", "text/plain")

