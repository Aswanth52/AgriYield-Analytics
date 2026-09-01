# 🗺️ District Intelligence Command Center - Complete Guide

## Overview

The **District Intelligence Command Center** is a professional geospatial analytics dashboard for mustard yield prediction and resource management in Rajasthan. It combines **GIS (Geospatial Information Systems)**, **advanced UI/UX design**, and **agronomic intelligence** into a single unified experience.

---

## 🎯 Core Features

### 1. **6-Layer Intelligence Map**
A dynamic choropleth map with multiple intelligence layers that can be toggled via button controls:

#### Metric Layers:
| Layer | Color Palette | Interpretation | Best For |
|-------|---------------|-----------------|----------|
| **Avg Yield** | YlGn_09 (Yellow→Green) | Higher is better | Performance tracking |
| **Risk Score** | OrRd_09 (Orange→Red) | Lower is better | Risk management |
| **Water Stress** | YlOrBr_09 (Yellow→Brown) | Lower is better | Irrigation planning |
| **Nutrient Index** | PuBuGn_09 (Purple→Green) | Higher is better | Soil management |
| **Climate Pressure** | BuPu_09 (Blue→Purple) | Lower is better | Climate adaptation |
| **Irrigation Type** | Categorical | Context-dependent | Resource allocation |

**Interactive Elements:**
- 🎯 **Click to Select**: Click any district on the map to view full intelligence
- 🌟 **Gold Hover Effect**: Hover over districts for visual feedback (#FFD700 gold highlight)
- 📍 **Dark Popups**: Hover popups show yield rank, risk, water stress, and irrigation type
- 🎨 **Color Legend**: Automatic legend overlay for all continuous metrics

---

### 2. **Split-Screen Command Panel**

#### Left Column: Interactive Folium Map
- CartoDB Dark Matter tiles for premium aesthetic
- Full responsive zoom and pan
- GeoJSON boundaries from DataMeet Rajasthan
- District label overlays with Space Mono font

#### Right Column: District Intelligence Dashboard
Contains the following sections when a district is selected:

##### **Core Metrics (4-Metric Grid)**
- **Yield**: District average yield in quintals with rank position
- **Risk**: Risk band classification (Low/Moderate/High/Critical) with score
- **H₂O Stress**: Water stress ratio for irrigation planning
- **Nutrients**: Nutrient index (kg/ha) for soil management

##### **Yield Gauge Chart**
- **Plotly Gauge** comparing district yield vs. state average
- **Color Zones**: Red (poor), Yellow (moderate), Green (optimal)
- **Reference Line**: State average marked for quick comparison
- **Y-Scale**: Dynamic based on state min/max values

##### **Live Weather Integration**
- 🌡️ **Temperature**: Real-time data from OpenWeatherMap API
- 💧 **Humidity**: Current humidity percentage
- 💨 **Wind Speed**: Wind velocity in m/s
- 🌧️ **Rainfall**: Precipitation data with fallback to climatological averages

##### **Prescriptive Intelligence Alerts**
AI-powered recommendation cards with color coding:

**4 Alert Types:**

1. **🛑 CRITICAL (Red)**
   - Water stress > 0.7
   - Risk band = Critical
   - Urgent action required

2. **⚠️ WARNING (Yellow)**
   - Yield gap (district < 80% state average)
   - Nutrient index below optimal
   - Risk band = High
   - Action needed soon

3. **ℹ️ INFO (Blue)**
   - General advisories for normal conditions
   - Best practices for performing districts

4. **✅ OPTIMAL (Green)**
   - Low-risk, high-performing districts
   - Outperformance alerts

**Example Alert:**
```
⚠️ HIGH WATER STRESS
━━━━━━━━━━━━━━━━━━━━━━
Water stress ratio: 0.82 (Critical)
Recommendation: Implement drip irrigation subsidy program immediately.
```

---

### 3. **District Comparative Analysis**

**Bottom Section Features:**

#### Comparison Metric Selector
Choose from:
- **Yield**: Average yield comparison
- **Risk**: Risk score ranking
- **Water Stress**: Water stress ratio comparison
- **Nutrients**: Nutrient index comparison
- **Production**: Total production ranking

#### Top-10 Ranking Table
- Sorted by selected metric (ascending or descending)
- Displays key columns for each district:
  - District Name
  - Avg Yield (Q)
  - Risk Band Classification
  - H₂O Stress Ratio
  - Nutrient Index (kg/ha)
  - Production (Metric Tons)

#### Export Functions
1. **📊 Download Comparison (CSV)**
   - Exports top-10 districts table
   - Use in Excel or data analysis tools

2. **📄 Download Report (TXT)**
   - Full intelligence summary for selected district
   - Includes all metrics and recommendations
   - Plain-text format for email/documentation

---

## 🚀 User Workflow

### Step 1: Load Dashboard
```
URL: http://localhost:8501/2_District_Heatmap
```

### Step 2: Choose Intelligence Layer
Click one of the 6 metric buttons at the top:
- Map choropleth updates instantly
- Color legend updates
- Previous selection preserved

### Step 3: Select District
**Option A - Dropdown**: Use the "Select District" dropdown in right panel
**Option B - Click Map**: Click any district on the map to select

### Step 4: Review Intelligence
- View core metrics grid (4 values)
- Check yield gauge chart
- Read live weather
- Review recommendations (1-4 alert cards)

### Step 5: Analyze Comparatively
- Scroll to bottom section
- Choose comparison metric
- Review top-10 ranking table

### Step 6: Export & Share
- Download CSV for analysis
- Download TXT report for stakeholders

---

## 📊 Data Architecture

### Data Flow
```
Load Clean Data (rajasthan_mustard_clean.xlsx)
         ↓
Build District Summary (groupby aggregation)
         ↓
Fetch GeoJSON (DataMeet Rajasthan official boundaries)
         ↓
Normalize District Names (matching & cleaning)
         ↓
Create Folium Map (choropleth with normalization)
         ↓
Generate Recommendations (alert logic engine)
         ↓
Render UI (split-screen command center)
```

### District Summary Metrics
| Metric | Calculation | Use Case |
|--------|-------------|----------|
| `avg_yield` | Mean of Yield (quintals) | Primary KPI |
| `risk_score` | Weighted (45% water + 35% yield + 20% climate) | Risk management |
| `water_stress_ratio` | Water Consumption / Water Availability | Irrigation planning |
| `nutrient_index` | NPK (Nitrogen + Phosphorus + Potassium) kg/ha | Soil management |
| `climate_pressure` | 45% temp + 55% wind | Climate adaptation |
| `risk_band` | Quantile-based classification (Low/Moderate/High/Critical) | Quick interpretation |

### GeoJSON Normalization Strategy
```python
# Step 1: Extract district names from both sources
df_districts = df["District"].str.upper().str.strip().unique()
geojson_districts = [f["properties"]["district"].upper().strip() 
                     for f in geojson["features"]]

# Step 2: Exact matching
mapping = {geojson_dist: df_dist 
           for geojson_dist in geojson_districts
           for df_dist in df_districts
           if geojson_dist == df_dist}

# Step 3: Handle case/whitespace variations
# Step 4: Fallback to partial string matching for unmatched

# Step 5: Grey out unmatched districts on map
```

---

## 🎨 Design System

### Color Palette
```css
/* Dark Theme */
--primary-bg: #0e1117;        /* Almost black Streamlit dark */
--secondary-bg: #161b22;      /* Slightly lighter */
--text-primary: #e6edf3;      /* Light cyan */
--text-secondary: #8b949e;    /* Medium grey */

/* Accents */
--gold: #FFD700;              /* Hover highlight & accent */
--gold-dim: #D4AF37;          /* Border & dim state */

/* Status Colors */
--success: #3fb950;           /* Green: optimal */
--warning: #e3b341;           /* Yellow: needs attention */
--danger: #ef4444;            /* Red: critical */
--info: #79c0ff;              /* Blue: informational */
```

### Typography
- **Font Family**: Space Mono (monospace)
- **Dashboard Title**: 16px bold, gold color
- **Metric Labels**: 14px secondary color
- **Alert Headers**: 13px bold primary color
- **Alert Body**: 12px secondary color, 1.4 line-height

### Component Styling
- **Command Center Boxes**: 12px margin, 1px border (#30363d), rounded corners
- **Alert Cards**: 8px padding, border-left accent stripe, subtle background
- **Weather Cards**: Blue accent (#79c0ff), 2-column layout
- **Metric Grid**: 2 columns, responsive spacing

---

## ⚙️ Technical Implementation

### Installation & Dependencies
```bash
pip install streamlit folium streamlit-folium plotly pandas requests branca

# Optional: For weather data
export OPENWEATHERMAP_API_KEY="your_api_key"
```

### Key Functions

#### `_fetch_geojson_from_datameet()` → dict
Fetches official Rajasthan district boundaries from DataMeet GitHub.
- **URL**: `https://raw.githubusercontent.com/datameet/maps/master/Districts/rajasthan.geojson`
- **Fallback**: Generates synthetic boundaries from DISTRICT_CENTERS dict
- **Error Handling**: 15-second timeout, graceful fallback

#### `_normalize_district_names(df, geojson)` → Dict[str, str]
Creates bidirectional mapping between DataFrame and GeoJSON district names.
- Case-insensitive matching
- Whitespace trimming
- Partial string matching for variations
- Returns mapping dict for use in style functions

#### `generate_recommendations(district_row, state_avg_yield)` → list[Dict]
Automated recommendation logic engine.
- 4 thresholds for alerts
- Returns list of alert dictionaries with type, icon, header, body
- Icons: ⚠️ 🧪 🧬 🛡️ ✅

#### `create_intelligence_map(summary, geojson, norm_map, metric)` → folium.Map
Renders interactive Folium map with selected metric layer.
- Dynamic color assignment based on metric
- Hover highlight with gold color
- Custom dark-themed popups
- Color legend overlay

#### `_get_weather(district: str)` → Dict[str, Any] | None
Fetches real-time weather from OpenWeatherMap API.
- Returns: temp, humidity, wind, rain, condition
- 10-second timeout
- Returns None if API unavailable

### Performance Considerations
- **GeoJSON Caching**: `@st.cache_data` with no spinner
- **Weather Caching**: 30-minute TTL recommended
- **Map Rendering**: ~2-3 seconds initial load, ~1 second layer toggle
- **Memory**: ~50MB for full dashboard state

---

## 📋 Recommendation Logic Rules

### Rule 1: Water Stress Alert
```python
IF district_row["water_stress_ratio"] > 0.7:
    ALERT("HIGH WATER STRESS", "Implement drip irrigation subsidy program immediately")
```

### Rule 2: Yield Gap Alert
```python
IF district_row["avg_yield"] < (state_avg_yield * 0.80):
    gap = state_avg_yield - district_row["avg_yield"]
    ALERT("SOIL CORRECTION NEEDED", "NPK supplementation + soil pH optimization")
```

### Rule 3: Nutrient Deficiency
```python
IF district_row["nutrient_index"] < 100:
    ALERT("NUTRIENT INDEX LOW", "Integrated Nutrient Management (INM) program")
```

### Rule 4: Risk Band Alert
```python
IF district_row["risk_band"] == "Critical":
    ALERT("RISK MITIGATION URGENT", "Consider crop diversification; crop insurance recommended")
ELIF district_row["risk_band"] == "High":
    ALERT("HIGH RISK ZONE", "Strengthen water management; monitor weather closely")
```

### Rule 5: Optimal Performance
```python
IF no_alerts_generated:
    INFO("OPTIMAL PERFORMANCE", "Continue current practices; focus on stabilization")
```

---

## 🔧 Configuration & Customization

### Thresholds (in code)
```python
WATER_STRESS_THRESHOLD = 0.7         # Alert if > this value
YIELD_PERFORMANCE_THRESHOLD = 0.80   # Alert if < 80% of state avg
NUTRIENT_INDEX_MIN = 100             # Alert if below this
```

### API Configuration
```python
# Optional: Set OpenWeatherMap API key
export OPENWEATHERMAP_API_KEY="your_key_here"

# Or add to Streamlit secrets:
# .streamlit/secrets.toml
# openweathermap_api_key = "your_key_here"
```

### Map Configuration
```python
STATE_CENTER = (26.8, 74.6)  # Rajasthan center
MAP_ZOOM = 6.4               # Default zoom level
FONT_FAMILY = "Space Mono"   # Monospace for technical feel
```

---

## 📱 Responsive Design

### Desktop (1920+ px width)
- 2-column map (2:1 ratio) + panel side-by-side
- Full map interactivity
- All metrics visible without scrolling

### Laptop (1366 px width)
- Slightly compressed map, panel remains full-width
- May require scrolling for recommendations

### Tablet (768 px width)
- Full-width map, stacked panel below
- Minimal horizontal scrolling

---

## 🐛 Troubleshooting

### Grey Districts on Map
**Problem**: Some districts appear grey (colored grey instead of correct color)
**Solution**: Check `_normalize_district_names()` output. Run:
```python
# In Python console
from utils.data_store import build_district_summary
df_districts = build_district_summary()
print(df_districts['District'].unique())
```

### Weather Card Shows "Unavailable"
**Problem**: Live weather not displaying
**Solutions**:
1. Check OpenWeatherMap API key is set correctly
2. Verify district name is correct (e.g., "Jaipur" not "Jaipur District")
3. Check network connectivity
4. System will auto-fallback to climatological averages

### Map Not Rendering
**Problem**: Folium map not showing in streamlit
**Solution**:
1. Ensure `streamlit-folium` is installed: `pip install streamlit-folium`
2. Try refreshing browser (Ctrl+R)
3. Check for zoom level being too extreme (MAP_ZOOM should be 4-8 for state)

### Recommendations Not Showing
**Problem**: Alert cards not displaying in panel
**Solution**:
1. Check district was selected (dropdown value changed)
2. Verify `generate_recommendations()` returns non-empty list
3. Check CSS is loading: Inspect browser DevTools → Elements → Look for style tags

---

## 📚 Advanced Usage

### Integrating Additional Data Sources
To add more metrics to the map:

1. **Add column to district summary** in `utils/data_store.py`:
```python
summary["my_metric"] = summary["some_column"].apply(my_function)
```

2. **Add to metric_specs** in `create_intelligence_map()`:
```python
metric_specs["My Metric"] = (
    "my_metric",                  # Column name
    linear.RdYlGn_09,            # Branca colormap
    "My Metric (units)",         # Legend label
    "continuous",                # Layer type
    "higher is better"           # Interpretation
)
```

3. **Test**: Button should appear on dashboard

### Custom Recommendation Logic
Modify `generate_recommendations()` function:
```python
def generate_recommendations(district_row, state_avg_yield):
    recommendations = []
    
    # Add custom rule
    if district_row["my_metric"] > threshold:
        recommendations.append({
            "type": "warning",
            "icon": "🎯",
            "header": "MY ALERT",
            "body": "My recommendation text"
        })
    
    return recommendations
```

### Filtering by Season
The system includes season context but doesn't filter by live season. To add:
```python
import datetime
current_month = datetime.datetime.now().month
is_rabi = 10 <= current_month or current_month <= 3  # Oct-Mar
is_kharif = 4 <= current_month <= 9                  # Apr-Sep
```

---

## 📞 Support & Notes

### Data Quality Assumptions
- Clean data source: `rajasthan_mustard_clean.xlsx`
- All districts have valid coordinates in DISTRICT_CENTERS
- GeoJSON from DataMeet matches 10 districts in Rajasthan dataset

### Future Enhancements
1. **3D Topographic Map**: Pydeck extrusion with yield as height
2. **Time-Series Analysis**: Historical trends per district
3. **Scenario Simulator**: What-if analysis with policy sliders
4. **PDF Reports**: Styled exports with logos
5. **Mobile App**: React Native companion app

### Version History
- **v1.0** (2026-04-13): Initial release with 6 layers, recommendations, weather, and analytics
- **Future**: 3D maps, prediction overlays, temporal views

---

## 📄 License & Attribution

**Data Sources**:
- District Boundaries: DataMeet Rajasthan GeoJSON
- Weather Data: OpenWeatherMap API
- Yield Data: Rajasthan agricultural datasets

**Technology**:
- Streamlit: Web app framework
- Folium: Interactive maps
- Plotly: Charts and gauges
- Branca: Color mapping for geospatial data

---

**Created**: April 13, 2026  
**Last Updated**: April 13, 2026  
**Status**: Production Ready ✅
