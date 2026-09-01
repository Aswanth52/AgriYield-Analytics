import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# LOAD CLEAN DATASET
# ============================================================
df = pd.read_csv("rajasthan_mustard_clean.csv")

print("Dataset Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nBasic Info:")
df.info()

print("\nFirst 5 rows:")
print(df.head())

print("\nBasic Statistics:")
print(df.describe())

print("\nMissing Values:")
print(df.isnull().sum())

# ============================================================
# 1. YIELD DISTRIBUTION
# ============================================================
plt.figure(figsize=(10, 5))
sns.histplot(df['Yield (quintals)'], bins=40, kde=True, color='steelblue')
plt.xlabel('Yield (quintals/ha)', fontsize=13, fontweight='bold')
plt.ylabel('Frequency', fontsize=13, fontweight='bold')
plt.title('Distribution of Mustard Yield', fontsize=16, fontweight='bold')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_yield_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. AVERAGE YIELD BY DISTRICT
# ============================================================
plt.figure(figsize=(12, 8))
district_yield = df.groupby('District')['Yield (quintals)'].mean().sort_values().reset_index()
bars = plt.barh(district_yield['District'], district_yield['Yield (quintals)'],
                color='steelblue', alpha=0.9, edgecolor='darkblue')
plt.xlabel('Average Mustard Yield (quintals/ha)', fontsize=13, fontweight='bold')
plt.ylabel('District', fontsize=13, fontweight='bold')
plt.title('Average Mustard Yield by District', fontsize=16, fontweight='bold')
for i, v in enumerate(district_yield['Yield (quintals)']):
    plt.text(v + 0.1, i, f'{v:.1f}', va='center', fontweight='bold', fontsize=9)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('chart_district_yield.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 3. YIELD BY SEASON (BOX PLOT)
# ============================================================
plt.figure(figsize=(8, 6))
sns.boxplot(x='Season', y='Yield (quintals)', data=df, palette='Set2')
plt.title('Yield Distribution by Season', fontsize=14, fontweight='bold')
plt.xlabel('Season', fontsize=12, fontweight='bold')
plt.ylabel('Yield (quintals)', fontsize=12, fontweight='bold')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_yield_by_season.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 4. YIELD BY IRRIGATION METHOD (VIOLIN PLOT)
# ============================================================
plt.figure(figsize=(10, 6))
sns.violinplot(x='Irrigation Method', y='Yield (quintals)', data=df, palette='Pastel1')
plt.title('Yield Distribution by Irrigation Method', fontsize=14, fontweight='bold')
plt.xlabel('Irrigation Method', fontsize=12, fontweight='bold')
plt.ylabel('Yield (quintals)', fontsize=12, fontweight='bold')
plt.xticks(rotation=30)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_yield_by_irrigation.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 5. YIELD BY SOIL TYPE (BOX PLOT)
# ============================================================
plt.figure(figsize=(12, 6))
df.boxplot(column='Yield (quintals)', by='Soil Type', rot=45,
           patch_artist=True,
           boxprops=dict(facecolor='skyblue', color='black'),
           medianprops=dict(color='red', linewidth=2),
           whiskerprops=dict(color='black', linewidth=1.5),
           capprops=dict(color='black', linewidth=1.5))
plt.title('Yield Distribution by Soil Type', fontsize=14, fontweight='bold')
plt.suptitle('')
plt.xlabel('Soil Type', fontsize=12, fontweight='bold')
plt.ylabel('Yield (quintals)', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_yield_by_soiltype.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 6. SOIL FEATURES vs YIELD (Scatter + Trend)
# ============================================================
soil_num_features = [
    'pH Level',
    'Organic Matter (%)',
    'Nitrogen Content (kg/ha)',
    'Phosphorus Content (kg/ha)',
    'Potassium Content (kg/ha)'
]

fig, axes = plt.subplots(3, 2, figsize=(14, 15))
axes = axes.flatten()

for i, feature in enumerate(soil_num_features):
    sns.regplot(
        data=df,
        x=feature,
        y='Yield (quintals)',
        ax=axes[i],
        scatter_kws={'alpha': 0.1, 's': 10, 'color': 'steelblue'},
        line_kws={'color': 'red', 'lw': 2}
    )
    axes[i].set_title(f'Impact of {feature} on Yield', fontsize=13, fontweight='bold')
    axes[i].set_xlabel(feature, fontsize=11)
    axes[i].set_ylabel('Yield (quintals)', fontsize=11)
    axes[i].grid(True, linestyle='--', alpha=0.4)

fig.delaxes(axes[-1])
fig.suptitle('Soil Chemical Composition vs. Crop Yield', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_soil_vs_yield.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 7. WEATHER FEATURES vs YIELD
# ============================================================
weather_features = ['temp', 'rain', 'humidity', 'wind_speed']
weather_labels = ['Temperature (°C)', 'Rainfall (mm)', 'Humidity (%)', 'Wind Speed (km/h)']

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, (feature, label) in enumerate(zip(weather_features, weather_labels)):
    sns.regplot(
        data=df,
        x=feature,
        y='Yield (quintals)',
        ax=axes[i],
        scatter_kws={'alpha': 0.1, 's': 10, 'color': 'darkorange'},
        line_kws={'color': 'darkblue', 'lw': 2}
    )
    axes[i].set_title(f'{label} vs Yield', fontsize=13, fontweight='bold')
    axes[i].set_xlabel(label, fontsize=11)
    axes[i].set_ylabel('Yield (quintals)', fontsize=11)
    axes[i].grid(True, linestyle='--', alpha=0.4)

fig.suptitle('Weather Features vs. Crop Yield', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_weather_vs_yield.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 8. WATER FEATURES vs YIELD
# ============================================================
water_features = ['Water Consumption (liters/hectare)', 'Water Availability (liters/hectare)']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for i, feature in enumerate(water_features):
    x = df[feature].values
    y = df['Yield (quintals)'].values
    axes[i].scatter(x, y, alpha=0.2, color='skyblue', s=10)
    m, b = np.polyfit(x, y, 1)
    axes[i].plot(sorted(x), sorted(m * np.array(x) + b), color='red', linewidth=2)
    axes[i].set_xlabel(feature, fontsize=11, fontweight='bold')
    axes[i].set_ylabel('Yield (quintals)', fontsize=11, fontweight='bold')
    axes[i].set_title(f'{feature} vs Yield', fontsize=12, fontweight='bold')
    axes[i].grid(alpha=0.3)

plt.suptitle('Water Features vs Yield', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_water_vs_yield.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 9. CORRELATION HEATMAP
# ============================================================
num_cols = df.select_dtypes(include='float64').columns.tolist()
corr = df[num_cols].corr()

plt.figure(figsize=(12, 9))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            linewidths=0.5, annot_kws={'size': 9})
plt.title('Correlation Heatmap of Numerical Features', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()

# Print highly correlated pairs
print("\nHighly correlated feature pairs (|correlation| >= 0.5):")
for i in range(len(corr.columns)):
    for j in range(i + 1, len(corr.columns)):
        val = corr.iloc[i, j]
        if abs(val) >= 0.5:
            print(f"  {corr.columns[i]}  <-->  {corr.columns[j]} :  {val:.2f}")

# ============================================================
# 10. SEASON-WISE YIELD CONTRIBUTION BY DISTRICT (Area Chart)
# ============================================================
season_district = df.groupby(['District', 'Season'])['Yield (quintals)'].mean().unstack()
season_district.plot(kind='area', stacked=True, figsize=(14, 6), colormap='Set2', alpha=0.7)
plt.xlabel('District', fontsize=12, fontweight='bold')
plt.ylabel('Average Yield (quintals)', fontsize=12, fontweight='bold')
plt.title('Season-wise Yield Contribution by District', fontsize=14, fontweight='bold')
plt.xticks(rotation=45)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_season_district_area.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 11. DISTRIBUTIONS OF ALL NUMERICAL FEATURES (Histogram + KDE)
# ============================================================
num_features_all = [
    'Area (hectares)', 'Yield (quintals)',
    'pH Level', 'Organic Matter (%)',
    'Nitrogen Content (kg/ha)', 'Phosphorus Content (kg/ha)',
    'Potassium Content (kg/ha)',
    'Water Consumption (liters/hectare)', 'Water Availability (liters/hectare)',
    'temp', 'rain', 'humidity', 'wind_speed'
]

n_cols = 3
n_rows = (len(num_features_all) + n_cols - 1) // n_cols
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 4))
axes = axes.flatten()

for i, col in enumerate(num_features_all):
    sns.histplot(df[col], bins=30, kde=True, ax=axes[i], color='steelblue')
    axes[i].set_xlabel(col, fontsize=10)
    axes[i].set_ylabel('Frequency', fontsize=10)
    axes[i].set_title(f'Distribution of {col}', fontsize=11, fontweight='bold')

for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

plt.suptitle('Histogram + KDE of All Numerical Features', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('chart_all_distributions.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 12. CATEGORY VALUE COUNTS
# ============================================================
cat_cols = ['District', 'Season', 'Soil Type', 'Irrigation Method']
print("\nCategorical Feature Value Counts:")
for col in cat_cols:
    print(f"\n{col}:")
    print(df[col].value_counts())

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("EDA SUMMARY")
print("="*60)
print(f"Total Rows       : {len(df):,}")
print(f"Total Features   : {df.shape[1]}")
print(f"Yield Range      : {df['Yield (quintals)'].min():.2f} - {df['Yield (quintals)'].max():.2f} quintals")
print(f"Mean Yield       : {df['Yield (quintals)'].mean():.2f} quintals")
print(f"Std Dev Yield    : {df['Yield (quintals)'].std():.2f} quintals")
print(f"Districts        : {df['District'].nunique()}")
print(f"Seasons          : {df['Season'].nunique()} ({', '.join(df['Season'].unique())})")
print(f"Soil Types       : {df['Soil Type'].nunique()}")
print(f"Irrigation Types : {df['Irrigation Method'].nunique()}")
print("="*60)
print("\nTop correlations with Yield:")
yield_corr = corr['Yield (quintals)'].drop('Yield (quintals)').abs().sort_values(ascending=False)
print(yield_corr.head(8))
