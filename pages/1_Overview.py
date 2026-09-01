from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_store import build_district_summary, load_clean_df
from utils.modeling import get_feature_importance, get_metrics
from utils.ui import apply_theme, render_hero, section_title, style_chart


apply_theme("Overview | Mustard Yield Intelligence", "🌾")

df = load_clean_df()


def _summary_from_frame(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        frame.groupby("District")
        .agg(
            avg_yield=("Yield (quintals)", "mean"),
            total_production=("Production (metric tons)", "sum"),
            total_area=("Area (hectares)", "sum"),
            avg_water_use=("Water Consumption (liters/hectare)", "mean"),
            avg_water_avail=("Water Availability (liters/hectare)", "mean"),
            avg_temp=("temp", "mean"),
            avg_wind=("wind_speed", "mean"),
            avg_nitrogen=("Nitrogen Content (kg/ha)", "mean"),
            avg_phosphorus=("Phosphorus Content (kg/ha)", "mean"),
            avg_potassium=("Potassium Content (kg/ha)", "mean"),
        )
        .reset_index()
    )
    grouped["yield_per_hectare"] = grouped["total_production"] / grouped["total_area"].replace(0, 1)
    grouped["water_stress_ratio"] = grouped["avg_water_use"] / grouped["avg_water_avail"].replace(0, 1)
    grouped["water_stress_ratio"] = grouped["water_stress_ratio"].replace([float("inf"), float("-inf")], 0).fillna(0)
    grouped["nutrient_index"] = grouped["avg_nitrogen"] + grouped["avg_phosphorus"] + grouped["avg_potassium"]
    grouped["climate_pressure"] = grouped["avg_temp"] * 0.45 + grouped["avg_wind"] * 0.55
    grouped["risk_score"] = (
        100
        * (
            0.45 * (grouped["water_stress_ratio"] - grouped["water_stress_ratio"].min()) / (grouped["water_stress_ratio"].max() - grouped["water_stress_ratio"].min() + 1e-9)
            + 0.35 * (1 - (grouped["avg_yield"] - grouped["avg_yield"].min()) / (grouped["avg_yield"].max() - grouped["avg_yield"].min() + 1e-9))
            + 0.20 * (grouped["climate_pressure"] - grouped["climate_pressure"].min()) / (grouped["climate_pressure"].max() - grouped["climate_pressure"].min() + 1e-9)
        )
    ).round(1)
    q1, q2, q3 = grouped["risk_score"].quantile([0.25, 0.5, 0.75]).tolist()
    grouped["risk_band"] = grouped["risk_score"].apply(lambda s: "Critical" if s >= q3 else "High" if s >= q2 else "Moderate" if s >= q1 else "Low")
    return grouped.sort_values("avg_yield", ascending=False).reset_index(drop=True)


season_choice = st.radio("Season filter", ["All", "Rabi", "Kharif"], horizontal=True)
if season_choice == "All":
    filtered_df = df.copy()
else:
    filtered_df = df[df["Season"].str.lower() == season_choice.lower()].copy()
summary = _summary_from_frame(filtered_df) if not filtered_df.empty else build_district_summary()
metrics = get_metrics()
corr_frame = filtered_df.select_dtypes(include=["number"]).copy()
corr = corr_frame.corr(numeric_only=True) if not corr_frame.empty else pd.DataFrame()
fi = get_feature_importance().head(10)

render_hero(
    "Overview",
    "Rajasthan Mustard\nIntelligence Dashboard",
    f"Real data from {len(filtered_df):,} records across {summary.shape[0]} districts. "
    f"The dashboard stays synchronized with the same cached local model bundle, so every page uses the same analytics.",
)

cols = st.columns(5)
cols[0].metric("Districts", summary.shape[0])
cols[1].metric("Rows", f"{len(filtered_df):,}")
cols[2].metric("Average yield", f"{filtered_df['Yield (quintals)'].mean():.1f}")
cols[3].metric("Best district", summary.iloc[0]["District"])
cols[4].metric("Test R²", f"{metrics['r2']:.3f}")
st.caption(f"Model confidence indicator: expected error range around ±{metrics['mae']:.2f} quintals (MAE).")

left, right = st.columns([1.12, 0.88])

with left:
    section_title("Yield Ranking")
    top10 = summary.head(10).sort_values("avg_yield", ascending=True)
    fig = px.bar(
        top10,
        x="avg_yield",
        y="District",
        orientation="h",
        color="risk_band",
        color_discrete_map={"Low": "#2d5a1b", "Moderate": "#8fb87a", "High": "#d68910", "Critical": "#c0392b"},
        text=top10["avg_yield"].round(1),
    )
    style_chart(fig, height=390)
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    section_title("Correlation Heatmap")
    if not corr.empty:
        interpretation = []
        for y in corr.columns:
            row = []
            for x in corr.columns:
                value = float(corr.loc[y, x])
                strength = "high" if abs(value) >= 0.8 else "moderate" if abs(value) >= 0.5 else "low"
                row.append(f"{y} and {x} are {abs(value)*100:.0f}% correlated ({strength})")
            interpretation.append(row)
        corr_fig = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale="YlGn",
                zmin=-1,
                zmax=1,
                customdata=interpretation,
                hovertemplate="Corr: %{z:.2f}<br>%{customdata}<extra></extra>",
                hoverongaps=False,
            )
        )
        style_chart(corr_fig, height=420)
        corr_fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(corr_fig, use_container_width=True)
    else:
        st.info("Correlation matrix unavailable for current filter.")

    section_title("Yield Distribution")
    hist = px.histogram(
        filtered_df,
        x="Yield (quintals)",
        color="District",
        nbins=24,
        barmode="overlay",
        opacity=0.55,
    )
    style_chart(hist, height=360)
    hist.update_layout(margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
    st.plotly_chart(hist, use_container_width=True)

with right:
    section_title("Model Metrics")
    metric_cards = st.columns(2)
    metric_cards[0].metric("R²", f"{metrics['r2']:.3f}")
    metric_cards[1].metric("MAE", f"{metrics['mae']:.2f}")
    metric_cards = st.columns(2)
    metric_cards[0].metric("RMSE", f"{metrics['rmse']:.2f}")
    if metrics.get("cv_r2") is not None:
        metric_cards[1].metric("CV R²", f"{metrics['cv_r2']:.3f}")
    else:
        metric_cards[1].metric("CV R²", "cached")

    st.markdown("**Top district**")
    st.write(f"{summary.iloc[0]['District']} with {summary.iloc[0]['avg_yield']:.1f} quintals/ha")
    st.markdown("**Highest risk district**")
    worst = summary.sort_values("risk_score", ascending=False).iloc[0]
    st.write(f"{worst['District']} with risk score {worst['risk_score']:.1f}")
    st.markdown("**Average rainfall**")
    st.write(f"{filtered_df['rain'].mean():.1f} mm")

    section_title("Feature Importance")
    fi_fig = px.bar(
        fi.sort_values("importance", ascending=True),
        x="importance",
        y="feature",
        orientation="h",
        color="importance",
        color_continuous_scale="YlGn",
    )
    style_chart(fi_fig, height=360)
    fi_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fi_fig, use_container_width=True)

section_title("District Comparison")
compare_cols = st.columns(2)
d1 = compare_cols[0].selectbox("District A", summary["District"].tolist(), key="d1")
d2 = compare_cols[1].selectbox("District B", summary["District"].tolist(), index=min(1, len(summary) - 1), key="d2")
r1 = summary.set_index("District").loc[d1]
r2 = summary.set_index("District").loc[d2]
c1, c2 = st.columns(2)
c1.dataframe(pd.DataFrame([r1[["avg_yield", "yield_per_hectare", "total_production", "water_stress_ratio", "nutrient_index", "risk_score", "risk_band"]]]), use_container_width=True)
c2.dataframe(pd.DataFrame([r2[["avg_yield", "yield_per_hectare", "total_production", "water_stress_ratio", "nutrient_index", "risk_score", "risk_band"]]]), use_container_width=True)

section_title("District Intelligence Table")
display = summary[
    [
        "District",
        "avg_yield",
        "yield_per_hectare",
        "total_production",
        "water_stress_ratio",
        "nutrient_index",
        "risk_score",
        "risk_band",
    ]
].rename(
    columns={
        "avg_yield": "Avg yield",
        "yield_per_hectare": "Yield/ha",
        "total_production": "Total production",
        "water_stress_ratio": "Water stress",
        "nutrient_index": "Nutrient index",
        "risk_score": "Risk score",
        "risk_band": "Risk band",
    }
)
st.dataframe(display, use_container_width=True, hide_index=True)
csv = display.to_csv(index=False).encode("utf-8")
st.download_button("Export district summary CSV", csv, "district_summary_overview.csv", "text/csv")

