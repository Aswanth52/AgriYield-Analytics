from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

from utils.data_store import build_district_summary, load_clean_df
from utils.modeling import predict_from_inputs
from utils.ui import apply_theme, render_hero, section_title


apply_theme("Farmer Advisory | Mustard Yield Intelligence", "👨‍🌾")

df = load_clean_df()
summary = build_district_summary().set_index("District")
state_avg_yield = float(df["Yield (quintals)"].mean())
MSP = 5650


def fetch_weather(district: str) -> dict | None:
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
            "rain": float(data.get("rain", {}).get("1h", 0.0)),
            "humidity": float(data["main"]["humidity"]),
            "wind_speed": float(data["wind"]["speed"]),
        }
    except Exception:
        return None


render_hero(
    "Farmer Advisory",
    "Smart Advisory\nPrescriptive Yield Engine",
    "Get district-aware predictions, what-if gains, soil and irrigation guidance, and profitability estimates in one advisory flow.",
)

district = st.selectbox("District", summary.index.tolist(), index=0)
district_defaults = summary.loc[district]
rows = df[df["District"] == district]

default_season = rows["Season"].mode().iat[0]
default_soil = rows["Soil Type"].mode().iat[0]
default_irrigation = rows["Irrigation Method"].mode().iat[0]

weather = fetch_weather(district)
if weather:
    st.success("Live weather fetched from OpenWeatherMap and used to prefill the form.")
else:
    st.info("No weather API key found, so the form uses district dataset averages as defaults.")

base_cols = st.columns(4)
base_cols[0].metric("District avg yield", f"{district_defaults['avg_yield']:.1f}")
base_cols[1].metric("State avg yield", f"{state_avg_yield:.1f}")
base_cols[2].metric("Risk band", district_defaults["risk_band"])
base_cols[3].metric("Top irrigation", district_defaults["top_irrigation"])

col1, col2 = st.columns(2)
with col1:
    season = st.selectbox("Season", sorted(df["Season"].unique()), index=sorted(df["Season"].unique()).index(default_season), help="Choose the season for advisory output.")
    soil_type = st.selectbox("Soil type", sorted(df["Soil Type"].unique()), index=sorted(df["Soil Type"].unique()).index(default_soil), help="Select the soil texture observed in your field.")
    irrigation_method = st.selectbox(
        "Irrigation method",
        sorted(df["Irrigation Method"].unique()),
        index=sorted(df["Irrigation Method"].unique()).index(default_irrigation),
        help="Current water delivery method used by the farmer.",
    )
    area = st.slider("Area (hectares)", float(df["Area (hectares)"].quantile(0.05)), float(df["Area (hectares)"].quantile(0.95)), float(rows["Area (hectares)"].median()), help="Total farm area under mustard.")
    pH = st.slider("pH level", 4.5, 9.5, float(rows["pH Level"].median()), 0.01, help="Mustard performs best near neutral pH around 6.5-7.0.")
    organic_matter = st.slider("Organic matter (%)", 0.1, 6.0, float(rows["Organic Matter (%)"].median()), 0.01, help="Higher organic matter improves moisture retention and nutrient availability.")
    if pH < 6.0 or pH > 7.5:
        st.error("pH zone: Red (outside ideal range 6.0-7.5)")
    else:
        st.success("pH zone: Green (within ideal range)")

with col2:
    if weather:
        temp = st.slider("Temperature (°C)", 0.0, 50.0, weather["temp"], 0.1, help="Current/expected daytime temperature.")
        rain = st.slider("Rainfall", 0.0, float(df["rain"].max()), weather["rain"], 0.1, help="Expected rainfall input for advisory scenario.")
        humidity = st.slider("Humidity (%)", 0.0, 100.0, weather["humidity"], 0.1, help="Relative humidity in percentage.")
        wind_speed = st.slider("Wind speed", 0.0, 25.0, weather["wind_speed"], 0.1, help="Higher wind can increase moisture loss.")
    else:
        temp = st.slider("Temperature (°C)", float(df["temp"].quantile(0.05)), float(df["temp"].quantile(0.95)), float(rows["temp"].median()), 0.1, help="Current/expected daytime temperature.")
        rain = st.slider("Rainfall", float(df["rain"].quantile(0.05)), float(df["rain"].quantile(0.95)), float(rows["rain"].median()), 0.1, help="Expected rainfall input for advisory scenario.")
        humidity = st.slider("Humidity (%)", float(df["humidity"].quantile(0.05)), float(df["humidity"].quantile(0.95)), float(rows["humidity"].median()), 0.1, help="Relative humidity in percentage.")
        wind_speed = st.slider("Wind speed", float(df["wind_speed"].quantile(0.05)), float(df["wind_speed"].quantile(0.95)), float(rows["wind_speed"].median()), 0.1, help="Higher wind can increase moisture loss.")
    water_consumption = st.slider(
        "Water consumption",
        float(df["Water Consumption (liters/hectare)"].quantile(0.05)),
        float(df["Water Consumption (liters/hectare)"].quantile(0.95)),
        float(rows["Water Consumption (liters/hectare)"].median()),
        1.0,
        help="Amount of water being consumed by current irrigation setup.",
    )
    water_availability = st.slider(
        "Water availability",
        float(df["Water Availability (liters/hectare)"].quantile(0.05)),
        float(df["Water Availability (liters/hectare)"].quantile(0.95)),
        float(rows["Water Availability (liters/hectare)"].median()),
        1.0,
        help="Estimated water available for the current season.",
    )

nitrogen = st.slider("Nitrogen (kg/ha)", float(df["Nitrogen Content (kg/ha)"].quantile(0.05)), float(df["Nitrogen Content (kg/ha)"].quantile(0.95)), float(rows["Nitrogen Content (kg/ha)"].median()), 0.1, help="Nitrogen is a key driver for vegetative growth.")
phosphorus = st.slider("Phosphorus (kg/ha)", float(df["Phosphorus Content (kg/ha)"].quantile(0.05)), float(df["Phosphorus Content (kg/ha)"].quantile(0.95)), float(rows["Phosphorus Content (kg/ha)"].median()), 0.1, help="Phosphorus supports root development and flowering.")
potassium = st.slider("Potassium (kg/ha)", float(df["Potassium Content (kg/ha)"].quantile(0.05)), float(df["Potassium Content (kg/ha)"].quantile(0.95)), float(rows["Potassium Content (kg/ha)"].median()), 0.1, help="Potassium improves stress tolerance and grain filling.")

predict = st.button("Predict yield")

if predict:
    predicted_yield = predict_from_inputs(
        district=district,
        season=season,
        soil_type=soil_type,
        irrigation_method=irrigation_method,
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

    baseline = float(district_defaults["avg_yield"])
    delta = predicted_yield - baseline
    score = district_defaults["risk_score"]
    pct_vs_district = (predicted_yield - baseline) / max(baseline, 1e-9) * 100
    pct_vs_state = (predicted_yield - state_avg_yield) / max(state_avg_yield, 1e-9) * 100

    def _yield_category(y: float) -> str:
        if y < baseline * 0.85:
            return "Poor"
        if y < baseline * 1.0:
            return "Average"
        if y < baseline * 1.12:
            return "Good"
        return "Excellent"

    category = _yield_category(predicted_yield)

    section_title("Yield Prediction Card")
    top = st.columns(4)
    top[0].metric("Predicted yield", f"{predicted_yield:.2f} quintals")
    top[1].metric("Vs district avg", f"{pct_vs_district:+.1f}%")
    top[2].metric("Vs state avg", f"{pct_vs_state:+.1f}%")
    top[3].metric("Yield category", category)

    def _predict_variant(**override) -> float:
        args = dict(
            district=district,
            season=season,
            soil_type=soil_type,
            irrigation_method=irrigation_method,
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
        args.update(override)
        return predict_from_inputs(**args)

    drip_yield = _predict_variant(irrigation_method="Drip")
    ph_yield = _predict_variant(pH=6.75)
    npk_yield = _predict_variant(nitrogen=nitrogen * 1.2, phosphorus=phosphorus * 1.2, potassium=potassium * 1.2)
    all_yield = _predict_variant(
        irrigation_method="Drip",
        pH=6.75,
        nitrogen=nitrogen * 1.2,
        phosphorus=phosphorus * 1.2,
        potassium=potassium * 1.2,
    )

    section_title("What If Simulator")
    what_if = pd.DataFrame(
        [
            {"Change": "Switch to Drip", "Predicted Yield": drip_yield, "Gain": drip_yield - predicted_yield},
            {"Change": "Correct pH to 6.75", "Predicted Yield": ph_yield, "Gain": ph_yield - predicted_yield},
            {"Change": "Increase NPK by 20%", "Predicted Yield": npk_yield, "Gain": npk_yield - predicted_yield},
            {"Change": "All changes combined", "Predicted Yield": all_yield, "Gain": all_yield - predicted_yield},
        ]
    )
    what_if["Predicted Yield"] = what_if["Predicted Yield"].round(2)
    what_if["Gain"] = what_if["Gain"].round(2)
    st.dataframe(what_if, use_container_width=True, hide_index=True)

    section_title("Soil Health Advisory")
    def _traffic(value: float, low: float, high: float) -> str:
        if value < low:
            return "Red"
        if value > high:
            return "Yellow"
        return "Green"

    soil_rows = []
    soil_rows.append({"Parameter": "pH", "Value": round(pH, 2), "Status": _traffic(pH, 6.0, 7.5), "Advice": f"Your pH is {pH:.2f}. Apply sulfur @ 20kg/hectare if above 7.5." if pH > 7.5 else "pH is acceptable for mustard."})
    soil_rows.append({"Parameter": "Nitrogen", "Value": round(nitrogen, 1), "Status": _traffic(nitrogen, rows["Nitrogen Content (kg/ha)"].quantile(0.35), rows["Nitrogen Content (kg/ha)"].quantile(0.75)), "Advice": "Increase nitrogen dose in split application if below district median."})
    soil_rows.append({"Parameter": "Phosphorus", "Value": round(phosphorus, 1), "Status": _traffic(phosphorus, rows["Phosphorus Content (kg/ha)"].quantile(0.35), rows["Phosphorus Content (kg/ha)"].quantile(0.75)), "Advice": "Add phosphorus through basal dose if low."})
    soil_rows.append({"Parameter": "Potassium", "Value": round(potassium, 1), "Status": _traffic(potassium, rows["Potassium Content (kg/ha)"].quantile(0.35), rows["Potassium Content (kg/ha)"].quantile(0.75)), "Advice": "Add muriate of potash if potassium is low."})
    st.dataframe(pd.DataFrame(soil_rows), use_container_width=True, hide_index=True)

    section_title("Irrigation Advisory")
    water_stress = water_consumption / max(water_availability, 1.0)
    if irrigation_method.lower() == "rainfed" and water_stress > summary["water_stress_ratio"].quantile(0.75):
        st.warning("Switch to Drip Irrigation. Estimated yield improvement can be around 15-20% in high water-stress conditions.")
    elif irrigation_method.lower() == "canal" and area >= float(df["Area (hectares)"].median()):
        st.info("Consider Sprinkler in large fields to improve water efficiency and uniform application.")
    else:
        st.success("Current irrigation setup is acceptable. Track water stress regularly.")

    section_title("General Advice")
    if predicted_yield < baseline:
        st.warning("This scenario is below the district average. Focus on irrigation efficiency, nutrient balance, and pH correction.")
    elif delta > 5:
        st.success("This setup performs better than the local district baseline. Keep the current water and nutrient balance steady.")
    else:
        st.info("This scenario is close to the district average. Small changes in water or nutrients could improve stability.")

    if score >= summary["risk_score"].quantile(0.75):
        st.error(f"{district} is already in a higher risk band ({district_defaults['risk_band']}). Watch water stress closely.")

    section_title("Profitability Estimate")
    estimated_revenue = predicted_yield * area * MSP
    method_multiplier = {"Drip": 1.0, "Sprinkler": 0.95, "Canal": 0.9, "Rainfed": 0.8}
    cost_per_hectare = 16000 * method_multiplier.get(irrigation_method, 1.0)
    estimated_cost = cost_per_hectare * area
    net_profit = estimated_revenue - estimated_cost
    pcols = st.columns(3)
    pcols[0].metric("Expected revenue", f"Rs {estimated_revenue:,.0f}")
    pcols[1].metric("Estimated cost", f"Rs {estimated_cost:,.0f}")
    pcols[2].metric("Net profit", f"Rs {net_profit:,.0f}")

    advisory_table = pd.DataFrame(
        [
            {
                "District": district,
                "Baseline yield": baseline,
                "Predicted yield": predicted_yield,
                "Delta": delta,
                "Risk score": score,
                "Risk band": district_defaults["risk_band"],
                "Top irrigation": district_defaults["top_irrigation"],
                "Top soil": district_defaults["top_soil"],
            }
        ]
    )
    st.dataframe(advisory_table, use_container_width=True, hide_index=True)

