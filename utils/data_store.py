from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "rajasthan_mustard_clean.xlsx"
MODEL_READY_PATH = ROOT / "rajasthan_mustard_model_ready (1).xlsx"
PRODUCTION_PATH = ROOT / "Rajasthan_Dataset" / "crop_production_data.csv"
WATER_PATH = ROOT / "Rajasthan_Dataset" / "water_usage_data.csv"
SOIL_PATH = ROOT / "Rajasthan_Dataset" / "soil_analysis_data.csv"
PRICE_PATH = ROOT / "Rajasthan_Dataset" / "crop_price_data.csv"

DISTRICT_CENTERS = {
    "Ajmer": (26.4499, 74.6399),
    "Alwar": (27.5523, 76.6346),
    "Bhilwara": (25.3470, 74.6400),
    "Hanumangarh": (29.5818, 74.3290),
    "Jaipur": (26.9124, 75.7873),
    "Jodhpur": (26.2389, 73.0243),
    "Kota": (25.2138, 75.8648),
    "Nagaur": (27.2001, 73.7333),
    "Sri Ganganagar": (29.9038, 73.8772),
    "Udaipur": (24.5854, 73.7125),
}


@st.cache_data(show_spinner=False)
def load_clean_df() -> pd.DataFrame:
    return pd.read_excel(CLEAN_PATH)


@st.cache_data(show_spinner=False)
def load_model_ready_df() -> pd.DataFrame:
    return pd.read_excel(MODEL_READY_PATH)


@st.cache_data(show_spinner=False)
def load_supporting_frames() -> dict[str, pd.DataFrame]:
    return {
        "production": pd.read_csv(PRODUCTION_PATH),
        "water": pd.read_csv(WATER_PATH),
        "soil": pd.read_csv(SOIL_PATH),
        "prices": pd.read_csv(PRICE_PATH),
    }


def _mode_value(series: pd.Series):
    mode = series.dropna().mode()
    return mode.iloc[0] if not mode.empty else None


def _normalize(series: pd.Series) -> pd.Series:
    low = series.min()
    high = series.max()
    if np.isclose(high, low):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - low) / (high - low)


@st.cache_data(show_spinner=False)
def build_district_summary() -> pd.DataFrame:
    df = load_clean_df()

    summary = (
        df.groupby("District")
        .agg(
            sample_count=("Yield (quintals)", "size"),
            avg_yield=("Yield (quintals)", "mean"),
            median_yield=("Yield (quintals)", "median"),
            yield_std=("Yield (quintals)", "std"),
            total_production=("Production (metric tons)", "sum"),
            avg_area=("Area (hectares)", "mean"),
            total_area=("Area (hectares)", "sum"),
            avg_pH=("pH Level", "mean"),
            avg_organic=("Organic Matter (%)", "mean"),
            avg_nitrogen=("Nitrogen Content (kg/ha)", "mean"),
            avg_phosphorus=("Phosphorus Content (kg/ha)", "mean"),
            avg_potassium=("Potassium Content (kg/ha)", "mean"),
            avg_water_use=("Water Consumption (liters/hectare)", "mean"),
            avg_water_avail=("Water Availability (liters/hectare)", "mean"),
            avg_temp=("temp", "mean"),
            avg_rain=("rain", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_wind=("wind_speed", "mean"),
            top_soil=("Soil Type", _mode_value),
            top_irrigation=("Irrigation Method", _mode_value),
            top_season=("Season", _mode_value),
        )
        .reset_index()
    )

    summary["yield_per_hectare"] = summary["total_production"] / summary["total_area"].replace(0, np.nan)
    summary["yield_per_hectare"] = summary["yield_per_hectare"].fillna(0)
    summary["nutrient_index"] = summary["avg_nitrogen"] + summary["avg_phosphorus"] + summary["avg_potassium"]
    summary["water_stress_ratio"] = summary["avg_water_use"] / summary["avg_water_avail"].replace(0, np.nan)
    summary["water_stress_ratio"] = summary["water_stress_ratio"].replace([np.inf, -np.inf], np.nan).fillna(0)
    summary["climate_pressure"] = summary["avg_temp"] * 0.45 + summary["avg_wind"] * 0.55

    yield_component = 1 - _normalize(summary["avg_yield"])
    water_component = _normalize(summary["water_stress_ratio"])
    climate_component = _normalize(summary["climate_pressure"])
    summary["risk_score"] = (
        100 * (0.45 * water_component + 0.35 * yield_component + 0.20 * climate_component)
    ).round(1)

    q1, q2, q3 = summary["risk_score"].quantile([0.25, 0.5, 0.75]).tolist()

    def band(score: float) -> str:
        if score >= q3:
            return "Critical"
        if score >= q2:
            return "High"
        if score >= q1:
            return "Moderate"
        return "Low"

    summary["risk_band"] = summary["risk_score"].apply(band)
    summary["yield_rank"] = summary["avg_yield"].rank(ascending=False, method="dense").astype(int)
    summary["production_rank"] = summary["total_production"].rank(ascending=False, method="dense").astype(int)
    summary["district_label"] = summary["District"]
    return summary.sort_values("avg_yield", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def build_correlation_frame() -> pd.DataFrame:
    df = load_clean_df().copy()
    df["water_stress_ratio"] = df["Water Consumption (liters/hectare)"] / (df["Water Availability (liters/hectare)"] + 1)
    df["nutrient_index"] = (
        df["Nitrogen Content (kg/ha)"]
        + df["Phosphorus Content (kg/ha)"]
        + df["Potassium Content (kg/ha)"]
    )
    df["ph_optimal_dev"] = (df["pH Level"] - 7.0).abs()
    df["climate_index"] = (df["rain"] / (df["temp"] + 1)) * (df["humidity"] / 100)
    return df.select_dtypes(include=[np.number]).copy()


@st.cache_data(show_spinner=False)
def build_price_summary() -> pd.DataFrame:
    prices = load_supporting_frames()["prices"].copy()
    prices["Date"] = pd.to_datetime(prices["Date"], errors="coerce")
    mustard = prices[prices["Crop"].str.contains("Mustard", case=False, na=False)].copy()
    if mustard.empty:
        mustard = prices.copy()

    district_prices = (
        mustard.sort_values("Date")
        .groupby("District")
        .agg(
            avg_price=("Price (INR/quintal)", "mean"),
            latest_price=("Price (INR/quintal)", "last"),
            min_price=("Price (INR/quintal)", "min"),
            max_price=("Price (INR/quintal)", "max"),
            records=("Price (INR/quintal)", "size"),
        )
        .reset_index()
        .sort_values("latest_price", ascending=False)
    )
    return district_prices


def district_to_point(district: str) -> tuple[float, float]:
    return DISTRICT_CENTERS.get(district, (26.5, 74.5))


@st.cache_data(show_spinner=False)
def build_district_geojson() -> dict:
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
                "properties": {
                    "district": district,
                    "center_lat": lat,
                    "center_lon": lon,
                },
                "geometry": {"type": "Polygon", "coordinates": coordinates},
            }
        )
    return {"type": "FeatureCollection", "features": features}


@st.cache_data(show_spinner=False)
def district_click_lookup() -> pd.DataFrame:
    summary = build_district_summary().copy()
    summary["lat"] = summary["District"].map(lambda d: district_to_point(d)[0])
    summary["lon"] = summary["District"].map(lambda d: district_to_point(d)[1])
    return summary

