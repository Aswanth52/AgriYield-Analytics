from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from .data_store import load_clean_df


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
MODEL_PATH = MODEL_DIR / "xgb_model.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoders.pkl"
METRICS_PATH = MODEL_DIR / "metrics.pkl"

FEATURE_COLUMNS = [
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
    "District_enc",
    "Season_enc",
    "Soil Type_enc",
    "Irrigation Method_enc",
    "water_stress_ratio",
    "nutrient_index",
    "ph_optimal_dev",
    "climate_index",
]


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["water_stress_ratio"] = frame["Water Consumption (liters/hectare)"] / (
        frame["Water Availability (liters/hectare)"] + 1
    )
    frame["nutrient_index"] = (
        frame["Nitrogen Content (kg/ha)"]
        + frame["Phosphorus Content (kg/ha)"]
        + frame["Potassium Content (kg/ha)"]
    )
    frame["ph_optimal_dev"] = (frame["pH Level"] - 7.0).abs()
    frame["climate_index"] = (frame["rain"] / (frame["temp"] + 1)) * (frame["humidity"] / 100)
    return frame


def _build_encoders(df: pd.DataFrame) -> dict[str, list]:
    return {
        column: sorted(df[column].dropna().astype(str).unique().tolist())
        for column in ["District", "Season", "Soil Type", "Irrigation Method"]
    }


def _encode_with_map(series: pd.Series, values: list) -> pd.Series:
    mapping = {value: idx for idx, value in enumerate(values)}
    return series.astype(str).map(mapping).fillna(0).astype(int)


def _train_bundle(df: pd.DataFrame, encoder_map: dict[str, list]) -> dict:
    frame = _prepare_frame(df)
    frame["District_enc"] = _encode_with_map(frame["District"], encoder_map["District"])
    frame["Season_enc"] = _encode_with_map(frame["Season"], encoder_map["Season"])
    frame["Soil Type_enc"] = _encode_with_map(frame["Soil Type"], encoder_map["Soil Type"])
    frame["Irrigation Method_enc"] = _encode_with_map(frame["Irrigation Method"], encoder_map["Irrigation Method"])

    X = frame[FEATURE_COLUMNS]
    y = frame["Yield (quintals)"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=240,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring="r2", n_jobs=1)
    bundle = {
        "model": model,
        "encoder_map": encoder_map,
        "metrics": {
            "r2": float(r2_score(y_test, preds)),
            "mae": float(mean_absolute_error(y_test, preds)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
            "cv_r2": float(cv_scores.mean()),
            "cv_r2_std": float(cv_scores.std()),
        },
        "feature_importance": (
            pd.DataFrame(
                {
                    "feature": FEATURE_COLUMNS,
                    "importance": model.feature_importances_,
                }
            )
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        ),
    }
    return bundle


def _save_bundle(bundle: dict) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(bundle["model"], f)
        with open(ENCODER_PATH, "wb") as f:
            pickle.dump(bundle["encoder_map"], f)
        with open(METRICS_PATH, "wb") as f:
            pickle.dump(bundle["metrics"], f)
    except Exception:
        pass


@st.cache_resource(show_spinner=True)
def get_model_bundle() -> dict:
    df = load_clean_df()
    encoder_map = _build_encoders(df)

    if MODEL_PATH.exists() and ENCODER_PATH.exists() and METRICS_PATH.exists():
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            with open(ENCODER_PATH, "rb") as f:
                encoder_map = pickle.load(f)
            with open(METRICS_PATH, "rb") as f:
                metrics = pickle.load(f)
            frame = _prepare_frame(df)
            frame["District_enc"] = _encode_with_map(frame["District"], encoder_map["District"])
            frame["Season_enc"] = _encode_with_map(frame["Season"], encoder_map["Season"])
            frame["Soil Type_enc"] = _encode_with_map(frame["Soil Type"], encoder_map["Soil Type"])
            frame["Irrigation Method_enc"] = _encode_with_map(frame["Irrigation Method"], encoder_map["Irrigation Method"])
            X = frame[FEATURE_COLUMNS]
            bundle = {
                "model": model,
                "encoder_map": encoder_map,
                "metrics": metrics,
                "feature_importance": (
                    pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": getattr(model, "feature_importances_", np.zeros(len(FEATURE_COLUMNS)))})
                    .sort_values("importance", ascending=False)
                    .reset_index(drop=True)
                ),
            }
            return bundle
        except Exception:
            pass

    bundle = _train_bundle(df, encoder_map)
    _save_bundle(bundle)
    return bundle


def _encode_scalar(value: str, choices: list) -> int:
    try:
        return choices.index(value)
    except ValueError:
        return 0


def make_prediction_row(
    *,
    district: str,
    season: str,
    soil_type: str,
    irrigation_method: str,
    pH: float,
    organic_matter: float,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temp: float,
    rain: float,
    humidity: float,
    wind_speed: float,
    water_consumption: float,
    water_availability: float,
    area: float,
) -> pd.DataFrame:
    bundle = get_model_bundle()
    encoder_map = bundle["encoder_map"]

    row = pd.DataFrame(
        [
            {
                "pH Level": pH,
                "Organic Matter (%)": organic_matter,
                "Nitrogen Content (kg/ha)": nitrogen,
                "Phosphorus Content (kg/ha)": phosphorus,
                "Potassium Content (kg/ha)": potassium,
                "temp": temp,
                "rain": rain,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "Water Consumption (liters/hectare)": water_consumption,
                "Water Availability (liters/hectare)": water_availability,
                "Area (hectares)": area,
                "District_enc": _encode_scalar(district, encoder_map["District"]),
                "Season_enc": _encode_scalar(season, encoder_map["Season"]),
                "Soil Type_enc": _encode_scalar(soil_type, encoder_map["Soil Type"]),
                "Irrigation Method_enc": _encode_scalar(irrigation_method, encoder_map["Irrigation Method"]),
                "water_stress_ratio": water_consumption / (water_availability + 1),
                "nutrient_index": nitrogen + phosphorus + potassium,
                "ph_optimal_dev": abs(pH - 7.0),
                "climate_index": (rain / (temp + 1)) * (humidity / 100),
            }
        ]
    )
    return row[FEATURE_COLUMNS]


def predict_yield(row: pd.DataFrame) -> float:
    bundle = get_model_bundle()
    return float(bundle["model"].predict(row)[0])


def predict_from_inputs(**kwargs) -> float:
    return predict_yield(make_prediction_row(**kwargs))


def get_feature_importance() -> pd.DataFrame:
    return get_model_bundle()["feature_importance"].copy()


def get_metrics() -> dict:
    return get_model_bundle()["metrics"].copy()


def get_encoder_options() -> dict[str, list[str]]:
    return get_model_bundle()["encoder_map"].copy()


@st.cache_data(show_spinner=False)
def build_shap_values(sample_size: int = 200) -> dict:
    try:
        import shap
    except Exception as exc:  # pragma: no cover - optional dependency fallback
        return {"available": False, "error": str(exc)}

    bundle = get_model_bundle()
    df = _prepare_frame(load_clean_df())
    encoders = bundle["encoder_map"]
    df["District_enc"] = _encode_with_map(df["District"], encoders["District"])
    df["Season_enc"] = _encode_with_map(df["Season"], encoders["Season"])
    df["Soil Type_enc"] = _encode_with_map(df["Soil Type"], encoders["Soil Type"])
    df["Irrigation Method_enc"] = _encode_with_map(df["Irrigation Method"], encoders["Irrigation Method"])
    X = df[FEATURE_COLUMNS]
    sample = X.sample(min(sample_size, len(X)), random_state=42)

    explainer = shap.TreeExplainer(bundle["model"])
    shap_values = explainer(sample)
    return {
        "available": True,
        "sample": sample,
        "values": shap_values,
        "base_value": explainer.expected_value,
    }
