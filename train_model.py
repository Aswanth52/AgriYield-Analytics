"""
Rajasthan Mustard Crop Yield Prediction
Target: Yield (quintals)
Models: Random Forest, Gradient Boosting, Ridge (ensemble)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

# ─── 1. LOAD DATA ────────────────────────────────────────────────────────────
df = pd.read_csv('/mnt/user-data/uploads/output_file1.csv')
print(f"Dataset: {df.shape[0]:,} rows × {df.shape[1]} cols")

# ─── 2. FEATURE ENGINEERING ──────────────────────────────────────────────────
# Water stress ratio
df['water_stress_ratio'] = df['Water Consumption (liters/hectare)'] / (df['Water Availability (liters/hectare)'] + 1)

# Soil nutrient index
df['nutrient_index'] = (df['Nitrogen Content (kg/ha)'] + 
                         df['Phosphorus Content (kg/ha)'] + 
                         df['Potassium Content (kg/ha)'])

# pH deviation from optimal (6.5-7.5 is ideal for mustard)
df['ph_optimal_dev'] = abs(df['pH Level'] - 7.0)

# Climate comfort index for mustard
df['climate_index'] = df['rain'] / (df['temp'] + 1) * df['humidity'] / 100

# ─── 3. ENCODE CATEGORICALS ──────────────────────────────────────────────────
le_dict = {}
for col in ['District', 'Season', 'Soil Type', 'Irrigation Method']:
    le = LabelEncoder()
    df[col + '_enc'] = le.fit_transform(df[col])
    le_dict[col] = le

# ─── 4. DEFINE FEATURES & TARGET ─────────────────────────────────────────────
FEATURES = [
    # Soil
    'pH Level', 'Organic Matter (%)', 
    'Nitrogen Content (kg/ha)', 'Phosphorus Content (kg/ha)', 'Potassium Content (kg/ha)',
    # Weather
    'temp', 'rain', 'humidity', 'wind_speed',
    # Water
    'Water Consumption (liters/hectare)', 'Water Availability (liters/hectare)',
    # Farm
    'Area (hectares)',
    # Categorical (encoded)
    'District_enc', 'Season_enc', 'Soil Type_enc', 'Irrigation Method_enc',
    # Engineered
    'water_stress_ratio', 'nutrient_index', 'ph_optimal_dev', 'climate_index'
]

TARGET = 'Yield (quintals)'

X = df[FEATURES]
y = df[TARGET]

# ─── 5. TRAIN/TEST SPLIT ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

# ─── 6. MODELS ───────────────────────────────────────────────────────────────
models = {
    'Random Forest': RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        random_state=42
    ),
    'Ridge Regression': Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=1.0))
    ])
}

# ─── 7. TRAIN & EVALUATE ─────────────────────────────────────────────────────
def evaluate(model, X_tr, X_te, y_tr, y_te, name):
    model.fit(X_tr, y_tr)
    preds = model.predict(X_te)
    
    r2 = r2_score(y_te, preds)
    mae = mean_absolute_error(y_te, preds)
    rmse = np.sqrt(mean_squared_error(y_te, preds))
    
    # Cross-val R²
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_r2 = cross_val_score(model, X_tr, y_tr, cv=cv, scoring='r2').mean()
    
    print(f"\n{'─'*40}")
    print(f"  {name}")
    print(f"  R²:       {r2:.4f}  (CV R²: {cv_r2:.4f})")
    print(f"  MAE:      {mae:.3f} quintals")
    print(f"  RMSE:     {rmse:.3f} quintals")
    return {'model': model, 'r2': r2, 'mae': mae, 'rmse': rmse, 'cv_r2': cv_r2, 'preds': preds}

print("\n" + "="*40)
print("  MODEL TRAINING & EVALUATION")
print("="*40)

results = {}
for name, model in models.items():
    results[name] = evaluate(model, X_train, X_test, y_train, y_test, name)

# ─── 8. BEST MODEL & FEATURE IMPORTANCE ─────────────────────────────────────
best_name = max(results, key=lambda k: results[k]['r2'])
best = results[best_name]
print(f"\n{'='*40}")
print(f"  BEST MODEL: {best_name}")
print(f"  Test R²: {best['r2']:.4f} | MAE: {best['mae']:.3f}")
print("="*40)

# Feature importance (tree-based models)
if best_name in ['Random Forest', 'Gradient Boosting']:
    fi = pd.Series(best['model'].feature_importances_, index=FEATURES)
    fi = fi.sort_values(ascending=False)
    print("\n  Top 10 Feature Importances:")
    for feat, imp in fi.head(10).items():
        bar = '█' * int(imp * 100)
        print(f"  {feat:<35} {imp:.4f}  {bar}")

# ─── 9. SAVE PREDICTIONS ─────────────────────────────────────────────────────
test_df = X_test.copy()
test_df['Actual_Yield'] = y_test.values
test_df['Predicted_Yield'] = best['preds'].round(3)
test_df['Error'] = (test_df['Predicted_Yield'] - test_df['Actual_Yield']).round(3)
test_df['District'] = df.loc[X_test.index, 'District'].values
test_df['Season'] = df.loc[X_test.index, 'Season'].values
test_df['Crop'] = df.loc[X_test.index, 'Crop'].values

output_cols = ['District', 'Season', 'Crop', 'Actual_Yield', 'Predicted_Yield', 'Error']
test_df[output_cols].to_csv('/mnt/user-data/outputs/predictions.csv', index=False)
print("\n  Predictions saved to predictions.csv")

# ─── 10. SUMMARY TABLE ───────────────────────────────────────────────────────
print("\n" + "="*55)
print(f"  {'MODEL':<25} {'R²':>8} {'CV R²':>8} {'MAE':>8} {'RMSE':>8}")
print("="*55)
for name, r in results.items():
    marker = " ◄ BEST" if name == best_name else ""
    print(f"  {name:<25} {r['r2']:>8.4f} {r['cv_r2']:>8.4f} {r['mae']:>8.3f} {r['rmse']:>8.3f}{marker}")
print("="*55)
print("\nDone!")
