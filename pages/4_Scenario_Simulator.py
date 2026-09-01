from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from utils.data_store import build_district_summary, build_price_summary, load_clean_df, load_supporting_frames
from utils.modeling import predict_from_inputs
from utils.ui import apply_theme, render_hero, section_title, style_chart


apply_theme("Operations Console | Mustard Yield Intelligence", "🧠")

df = load_clean_df()
summary = build_district_summary().copy()
summary_index = summary.set_index("District")
prices = build_price_summary()
price_frames = load_supporting_frames()["prices"].copy()
price_frames["Date"] = pd.to_datetime(price_frames["Date"], errors="coerce")
mustard_prices = price_frames[price_frames["Crop"].str.contains("Mustard", case=False, na=False)].copy()
monthly_prices = (
    mustard_prices.dropna(subset=["Date"])
    .assign(month=lambda x: x["Date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month")
    .agg(avg_price=("Price (INR/quintal)", "mean"))
    .reset_index()
    .sort_values("month")
)
summary["modelled_yield"] = summary.apply(
    lambda row: predict_from_inputs(
        district=row["District"],
        season=row["top_season"],
        soil_type=row["top_soil"],
        irrigation_method=row["top_irrigation"],
        pH=float(row["avg_pH"]),
        organic_matter=float(row["avg_organic"]),
        nitrogen=float(row["avg_nitrogen"]),
        phosphorus=float(row["avg_phosphorus"]),
        potassium=float(row["avg_potassium"]),
        temp=float(row["avg_temp"]),
        rain=float(row["avg_rain"]),
        humidity=float(row["avg_humidity"]),
        wind_speed=float(row["avg_wind"]),
        water_consumption=float(row["avg_water_use"]),
        water_availability=float(row["avg_water_avail"]),
        area=float(row["avg_area"]),
    ),
    axis=1,
)

render_hero(
    "Operations Console",
    "Scenario, Allocation\nand Policy in One View",
    "Use the sliders to test a yield scenario, then switch to district ranking and policy signals without leaving the page. Everything is driven by the same local data bundle.",
)

top_cols = st.columns(4)
top_cols[0].metric("Districts", summary.shape[0])
top_cols[1].metric("Average yield", f"{summary['avg_yield'].mean():.1f}")
top_cols[2].metric("Critical districts", int((summary['risk_band'] == 'Critical').sum()))
top_cols[3].metric("Highest price district", prices.iloc[0]["District"] if not prices.empty else "n/a")

district = st.selectbox("District", summary_index.index.tolist())
season = st.selectbox("Season", sorted(df["Season"].unique()))
base_rows = df[(df["District"] == district) & (df["Season"] == season)]
if base_rows.empty:
    base_rows = df[df["District"] == district]
baseline = base_rows.iloc[0]

left, right = st.columns(2)

with left:
    section_title("Baseline")
    st.write("This is the actual record used as the starting point.")
    st.dataframe(
        pd.DataFrame([baseline[[
            "pH Level",
            "Organic Matter (%)",
            "Nitrogen Content (kg/ha)",
            "Phosphorus Content (kg/ha)",
            "Potassium Content (kg/ha)",
            "temp",
            "rain",
            "humidity",
            "wind_speed",
            "Water Consumption (liters/hectare)",
            "Water Availability (liters/hectare)",
            "Area (hectares)",
            "Yield (quintals)",
        ]]]),
        use_container_width=True,
        hide_index=True,
    )

with right:
    section_title("Scenario Controls")
    pH = st.slider("pH level", 4.5, 9.5, float(baseline["pH Level"]), 0.01)
    organic_matter = st.slider("Organic matter (%)", 0.1, 6.0, float(baseline["Organic Matter (%)"]), 0.01)
    nitrogen = st.slider("Nitrogen (kg/ha)", 0.0, float(df["Nitrogen Content (kg/ha)"].quantile(0.99)), float(baseline["Nitrogen Content (kg/ha)"]), 0.1)
    phosphorus = st.slider("Phosphorus (kg/ha)", 0.0, float(df["Phosphorus Content (kg/ha)"].quantile(0.99)), float(baseline["Phosphorus Content (kg/ha)"]), 0.1)
    potassium = st.slider("Potassium (kg/ha)", 0.0, float(df["Potassium Content (kg/ha)"].quantile(0.99)), float(baseline["Potassium Content (kg/ha)"]), 0.1)
    temp = st.slider("Temperature", float(df["temp"].min()), float(df["temp"].max()), float(baseline["temp"]), 0.1)
    rain = st.slider("Rainfall", float(df["rain"].min()), float(df["rain"].max()), float(baseline["rain"]), 0.1)
    humidity = st.slider("Humidity", float(df["humidity"].min()), float(df["humidity"].max()), float(baseline["humidity"]), 0.1)
    wind_speed = st.slider("Wind speed", float(df["wind_speed"].min()), float(df["wind_speed"].max()), float(baseline["wind_speed"]), 0.1)
    water_consumption = st.slider("Water consumption", float(df["Water Consumption (liters/hectare)"].min()), float(df["Water Consumption (liters/hectare)"].max()), float(baseline["Water Consumption (liters/hectare)"]), 1.0)
    water_availability = st.slider("Water availability", float(df["Water Availability (liters/hectare)"].min()), float(df["Water Availability (liters/hectare)"].max()), float(baseline["Water Availability (liters/hectare)"]), 1.0)
    area = st.slider("Area (hectares)", float(df["Area (hectares)"].min()), float(df["Area (hectares)"].max()), float(baseline["Area (hectares)"]), 1.0)

scenario_yield = predict_from_inputs(
    district=district,
    season=season,
    soil_type=baseline["Soil Type"],
    irrigation_method=baseline["Irrigation Method"],
    pH=pH,
    organic_matter=organic_matter,
    nitrogen=nitrogen,
    phosphorus=phosphorus,
    potassium=potassium,
    temp=temp,
    rain=rain,
    humidity=humidity,
    wind_speed=wind_speed,
    water_consumption=water_consumption,
    water_availability=water_availability,
    area=area,
)
baseline_yield = float(baseline["Yield (quintals)"])

scenario_b_shift = st.slider("Scenario B uplift (%) for nutrients", -20, 40, 10, 1)
scenario_b_ph = st.slider("Scenario B target pH", 5.5, 7.5, 6.75, 0.05)
scenario_b_irrigation = st.selectbox("Scenario B irrigation", sorted(df["Irrigation Method"].unique()), index=sorted(df["Irrigation Method"].unique()).index("Drip") if "Drip" in sorted(df["Irrigation Method"].unique()) else 0)
scenario_b_yield = predict_from_inputs(
    district=district,
    season=season,
    soil_type=baseline["Soil Type"],
    irrigation_method=scenario_b_irrigation,
    pH=scenario_b_ph,
    organic_matter=organic_matter,
    nitrogen=nitrogen * (1 + scenario_b_shift / 100),
    phosphorus=phosphorus * (1 + scenario_b_shift / 100),
    potassium=potassium * (1 + scenario_b_shift / 100),
    temp=temp,
    rain=rain,
    humidity=humidity,
    wind_speed=wind_speed,
    water_consumption=water_consumption,
    water_availability=water_availability,
    area=area,
)

section_title("Scenario Comparison")
compare = st.columns(3)
compare[0].metric("Scenario A", f"{scenario_yield:.2f}")
compare[1].metric("Scenario B", f"{scenario_b_yield:.2f}")
compare[2].metric("B - A", f"{scenario_b_yield - scenario_yield:+.2f}")
st.metric("A vs baseline", f"{scenario_yield - baseline_yield:+.2f}")

bar = go.Figure(
    data=[
        go.Bar(name="Baseline", x=["Yield"], y=[baseline_yield], marker_color="#2d5a1b"),
        go.Bar(name="Scenario A", x=["Yield"], y=[scenario_yield], marker_color="#5a9e3a"),
        go.Bar(name="Scenario B", x=["Yield"], y=[scenario_b_yield], marker_color="#c0392b"),
    ]
)
style_chart(bar, height=320)
bar.update_layout(barmode="group", margin=dict(l=10, r=10, t=20, b=10), title="Yield delta visual")
st.plotly_chart(bar, use_container_width=True)

if st.button("Best Case Scenario"):
    best_case = predict_from_inputs(
        district=district,
        season=season,
        soil_type=baseline["Soil Type"],
        irrigation_method="Drip" if "Drip" in df["Irrigation Method"].values else baseline["Irrigation Method"],
        pH=6.75,
        organic_matter=max(float(df["Organic Matter (%)"].quantile(0.9)), organic_matter),
        nitrogen=max(float(df["Nitrogen Content (kg/ha)"].quantile(0.9)), nitrogen),
        phosphorus=max(float(df["Phosphorus Content (kg/ha)"].quantile(0.9)), phosphorus),
        potassium=max(float(df["Potassium Content (kg/ha)"].quantile(0.9)), potassium),
        temp=temp,
        rain=rain,
        humidity=humidity,
        wind_speed=wind_speed,
        water_consumption=water_consumption,
        water_availability=max(water_availability, float(df["Water Availability (liters/hectare)"].quantile(0.8))),
        area=area,
    )
    st.success(f"Best-case estimate: {best_case:.2f} quintals ({best_case - scenario_yield:+.2f} vs Scenario A)")

impact = pd.DataFrame(
    [
        {"Field": "pH Level", "Baseline": baseline["pH Level"], "Scenario": pH},
        {"Field": "Organic Matter (%)", "Baseline": baseline["Organic Matter (%)"], "Scenario": organic_matter},
        {"Field": "Nitrogen Content (kg/ha)", "Baseline": baseline["Nitrogen Content (kg/ha)"], "Scenario": nitrogen},
        {"Field": "Phosphorus Content (kg/ha)", "Baseline": baseline["Phosphorus Content (kg/ha)"], "Scenario": phosphorus},
        {"Field": "Potassium Content (kg/ha)", "Baseline": baseline["Potassium Content (kg/ha)"], "Scenario": potassium},
        {"Field": "temp", "Baseline": baseline["temp"], "Scenario": temp},
        {"Field": "rain", "Baseline": baseline["rain"], "Scenario": rain},
        {"Field": "humidity", "Baseline": baseline["humidity"], "Scenario": humidity},
        {"Field": "wind_speed", "Baseline": baseline["wind_speed"], "Scenario": wind_speed},
        {"Field": "Water Consumption (liters/hectare)", "Baseline": baseline["Water Consumption (liters/hectare)"], "Scenario": water_consumption},
        {"Field": "Water Availability (liters/hectare)", "Baseline": baseline["Water Availability (liters/hectare)"], "Scenario": water_availability},
        {"Field": "Area (hectares)", "Baseline": baseline["Area (hectares)"], "Scenario": area},
    ]
)
impact["Delta"] = impact["Scenario"] - impact["Baseline"]
st.dataframe(impact, use_container_width=True, hide_index=True)

ranked_impact = impact.reindex(impact["Delta"].abs().sort_values(ascending=False).index)
section_title("Ranked Impact Drivers")
st.dataframe(ranked_impact[["Field", "Delta"]], use_container_width=True, hide_index=True)

section_title("District Allocation")
rank_metric = st.selectbox(
    "Rank by",
    ["avg_yield", "total_production", "risk_score", "water_stress_ratio", "yield_per_hectare"],
    format_func=lambda x: {
        "avg_yield": "Average yield",
        "total_production": "Total production",
        "risk_score": "Risk score",
        "water_stress_ratio": "Water stress",
        "yield_per_hectare": "Yield per hectare",
    }[x],
)

ascending = rank_metric in {"risk_score", "water_stress_ratio"}
ranked = summary.sort_values(rank_metric, ascending=ascending).reset_index(drop=True)
ranked["yield_gap"] = (ranked["modelled_yield"] - ranked["avg_yield"]).clip(lower=0)

left, right = st.columns(2)
with left:
    section_title("Risk vs Yield")
    fig = px.scatter(
        ranked,
        x="avg_yield",
        y="risk_score",
        size="total_production",
        color="risk_band",
        hover_name="District",
        color_discrete_map={"Low": "#2d5a1b", "Moderate": "#8fb87a", "High": "#d68910", "Critical": "#c0392b"},
    )
    style_chart(fig, height=360)
    st.plotly_chart(fig, use_container_width=True)

    section_title("Sortable District Table")
    st.dataframe(
        ranked[
            [
                "District",
                "avg_yield",
                "yield_per_hectare",
                "total_production",
                "water_stress_ratio",
                "risk_score",
                "risk_band",
                "top_irrigation",
                "top_soil",
            ]
        ].rename(
            columns={
                "avg_yield": "Avg yield",
                "yield_per_hectare": "Yield per hectare",
                "total_production": "Total production",
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

with right:
    section_title("Allocation Priorities")
    priorities = ranked.head(5)[["District", "risk_score", "water_stress_ratio", "avg_yield", "risk_band"]].copy()
    priorities["Action"] = priorities.apply(
        lambda row: (
            "Prioritise irrigation support"
            if row["risk_score"] >= summary["risk_score"].quantile(0.75)
            else "Monitor nutrient balance"
        ),
        axis=1,
    )
    st.dataframe(priorities, use_container_width=True, hide_index=True)

    csv = ranked.to_csv(index=False).encode("utf-8")
    st.download_button("Download ranking CSV", csv, "district_ranking.csv", "text/csv")

section_title("Resource Allocation Simulator")
budget_cols = st.columns(2)
gov_budget = budget_cols[0].number_input("Government budget (crore INR)", min_value=1.0, value=50.0, step=1.0)
per_district_cost = budget_cols[1].number_input("Per district drip cost (crore INR)", min_value=1.0, value=5.0, step=1.0)
district_slots = max(1, int(gov_budget // per_district_cost))
allocation = ranked.sort_values(["yield_gap", "risk_score"], ascending=[False, False]).head(district_slots).copy()
allocation["projected_yield_gain_q"] = (allocation["yield_gap"] * 0.6).round(2)
allocation["projected_prod_gain_tons"] = (allocation["projected_yield_gain_q"] * allocation["total_area"] / 10).round(1)
st.info(f"Allocate to {district_slots} district(s) for maximum projected impact under current budget.")
st.dataframe(
    allocation[["District", "risk_score", "yield_gap", "projected_yield_gain_q", "projected_prod_gain_tons"]],
    use_container_width=True,
    hide_index=True,
)

section_title("Priority Matrix")
matrix = px.scatter(
    ranked,
    x="risk_score",
    y="yield_gap",
    size="total_production",
    color="risk_band",
    hover_name="District",
    title="Risk score vs yield gap",
)
style_chart(matrix, height=380)
matrix.add_vline(x=ranked["risk_score"].median(), line_dash="dash", line_color="#1a2e1a")
matrix.add_hline(y=ranked["yield_gap"].median(), line_dash="dash", line_color="#1a2e1a")
st.plotly_chart(matrix, use_container_width=True)
plan_csv = allocation.to_csv(index=False).encode("utf-8")
st.download_button("Download action plan CSV", plan_csv, "allocation_action_plan.csv", "text/csv")

section_title("Policy Signals")
policy_cols = st.columns(4)
policy_cols[0].metric("State avg yield", f"{df['Yield (quintals)'].mean():.1f}")
policy_cols[1].metric("State total production", f"{df['Production (metric tons)'].sum():,.0f}")
policy_cols[2].metric("Highest price district", prices.iloc[0]["District"] if not prices.empty else "n/a")
policy_cols[3].metric("Critical districts", int((summary["risk_band"] == "Critical").sum()))

policy_left, policy_right = st.columns(2)

with policy_left:
    section_title("Modelled District Outlook")
    fig = px.bar(
        summary.sort_values("modelled_yield", ascending=True),
        x="modelled_yield",
        y="District",
        orientation="h",
        color="risk_band",
        color_discrete_map={"Low": "#2d5a1b", "Moderate": "#8fb87a", "High": "#d68910", "Critical": "#c0392b"},
    )
    style_chart(fig, height=360)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        summary[["District", "avg_yield", "modelled_yield", "total_production", "risk_score", "risk_band"]].rename(
            columns={
                "avg_yield": "Avg yield",
                "modelled_yield": "Modelled yield",
                "total_production": "Total production",
                "risk_score": "Risk score",
                "risk_band": "Risk band",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

with policy_right:
    section_title("MSP vs Mandi Price Trend")
    if not monthly_prices.empty:
        fig2 = px.line(
            monthly_prices,
            x="month",
            y="avg_price",
            markers=True,
            title="Monthly average mustard price",
        )
        fig2.add_hline(y=5650, line_dash="dot", line_color="#c0392b", annotation_text="MSP 5650")
        style_chart(fig2, height=360)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No mustard price records found in the local dataset.")

    section_title("Policy Actions")
    actions = summary.sort_values(["risk_score", "avg_yield"], ascending=[False, True]).head(5)[
        ["District", "risk_score", "water_stress_ratio", "avg_yield", "modelled_yield"]
    ].copy()
    actions["Policy suggestion"] = actions.apply(
        lambda row: "Water-saving intervention" if row["water_stress_ratio"] > summary["water_stress_ratio"].median() else "Maintain monitoring",
        axis=1,
    )
    st.dataframe(actions, use_container_width=True, hide_index=True)

section_title("Season-wise Production Forecast")
season_profiles = (
    df.groupby(["District", "Season"])
    .agg(
        pH=("pH Level", "mean"),
        organic=("Organic Matter (%)", "mean"),
        n=("Nitrogen Content (kg/ha)", "mean"),
        p=("Phosphorus Content (kg/ha)", "mean"),
        k=("Potassium Content (kg/ha)", "mean"),
        temp=("temp", "mean"),
        rain=("rain", "mean"),
        humidity=("humidity", "mean"),
        wind=("wind_speed", "mean"),
        wc=("Water Consumption (liters/hectare)", "mean"),
        wa=("Water Availability (liters/hectare)", "mean"),
        area=("Area (hectares)", "mean"),
        soil=("Soil Type", lambda s: s.mode().iat[0]),
        irrigation=("Irrigation Method", lambda s: s.mode().iat[0]),
    )
    .reset_index()
)
season_profiles["predicted_yield"] = season_profiles.apply(
    lambda r: predict_from_inputs(
        district=r["District"],
        season=r["Season"],
        soil_type=r["soil"],
        irrigation_method=r["irrigation"],
        pH=float(r["pH"]),
        organic_matter=float(r["organic"]),
        nitrogen=float(r["n"]),
        phosphorus=float(r["p"]),
        potassium=float(r["k"]),
        temp=float(r["temp"]),
        rain=float(r["rain"]),
        humidity=float(r["humidity"]),
        wind_speed=float(r["wind"]),
        water_consumption=float(r["wc"]),
        water_availability=float(r["wa"]),
        area=float(r["area"]),
    ),
    axis=1,
)
season_forecast = season_profiles.groupby("Season", as_index=False).agg(forecast_yield=("predicted_yield", "mean"))
season_chart = px.bar(season_forecast, x="Season", y="forecast_yield", color="Season", title="Forecasted average yield by season")
style_chart(season_chart, height=320)
st.plotly_chart(season_chart, use_container_width=True)

section_title("District Yield Gap: Actual vs Potential")
gap_df = summary.copy()
gap_df["potential_yield"] = (gap_df["modelled_yield"] * 1.15).round(2)
gap_df["yield_gap"] = (gap_df["potential_yield"] - gap_df["avg_yield"]).round(2)
gap_chart = px.bar(gap_df.sort_values("yield_gap", ascending=False), x="District", y=["avg_yield", "potential_yield"], barmode="group")
style_chart(gap_chart, height=380)
st.plotly_chart(gap_chart, use_container_width=True)

section_title("Drip Intervention Projection")
bottom3 = gap_df.sort_values("avg_yield").head(3).copy()
bottom3["projected_gain_tons"] = ((bottom3["potential_yield"] - bottom3["avg_yield"]) * bottom3["total_area"] / 10).round(1)
st.dataframe(bottom3[["District", "avg_yield", "potential_yield", "projected_gain_tons"]], use_container_width=True, hide_index=True)
st.success(f"Projected state production increase if drip best practices applied in bottom 3 districts: {bottom3['projected_gain_tons'].sum():,.1f} metric tons")

