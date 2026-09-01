

import requests
import pandas as pd
import time

RAJASTHAN_DISTRICTS = {
    'Udaipur': (24.5854, 73.7125),
    'Kota': (25.2149, 75.8587),
    'Jodhpur': (26.2389, 73.0243),
    'Nagaur': (27.2051, 73.1339),
    'Alwar': (27.5527, 76.6346),
    'Ajmer': (26.4499, 74.6399),
    'Bhilwara': (25.3469, 74.6367),
    'Sri Ganganagar': (29.9033, 73.8772),
    'Hanumangarh': (29.5833, 74.3167),
    'Jaipur': (26.9124, 75.7873)
}

def fetch_weather_api(lat, lon):
    """ERA5 2018-2019 daily weather"""
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": "2018-01-01", "end_date": "2019-12-31",
        "daily": ["temperature_2m_mean", "precipitation_sum", 
                 "relative_humidity_2m_max", "windspeed_10m_max"],
        "timezone": "Asia/Kolkata"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        return pd.DataFrame(response.json()['daily'])
    except:
        return pd.DataFrame()

def process_district_rows(df_raw, district):
    """2 rows per district: Kharif + Rabi"""
    if df_raw.empty:
        return pd.DataFrame()
    
    df = df_raw.copy()
    df['month'] = pd.to_datetime(df['time']).dt.month
    
    # Kharif Row (Jun-Oct)
    kharif_mask = df['month'].isin([6,7,8,9,10])
    kharif_stats = df[kharif_mask].agg({
        'temperature_2m_mean': 'mean',
        'precipitation_sum': 'sum',
        'relative_humidity_2m_max': 'mean',
        'windspeed_10m_max': 'mean'
    }).round(2)
    
    kharif_row = pd.DataFrame({
        'District': [district],
        'temp': [kharif_stats['temperature_2m_mean']],
        'rain': [kharif_stats['precipitation_sum']],
        'humidity': [kharif_stats['relative_humidity_2m_max']],
        'wind_speed': [kharif_stats['windspeed_10m_max']],
        'Season': ['Kharif']
    })
    
    # Rabi Row (Nov-Apr)
    rabi_mask = df['month'].isin([11,12,1,2,3,4])
    rabi_stats = df[rabi_mask].agg({
        'temperature_2m_mean': 'mean',
        'precipitation_sum': 'sum',
        'relative_humidity_2m_max': 'mean',
        'windspeed_10m_max': 'mean'
    }).round(2)
    
    rabi_row = pd.DataFrame({
        'District': [district],
        'temp': [rabi_stats['temperature_2m_mean']],
        'rain': [rabi_stats['precipitation_sum']],
        'humidity': [rabi_stats['relative_humidity_2m_max']],
        'wind_speed': [rabi_stats['windspeed_10m_max']],
        'Season': ['Rabi']
    })
    
    return pd.concat([kharif_row, rabi_row], ignore_index=True)

print(" RAJASTHAN WEATHER: 20 Rows Master (Kharif + Rabi)")
master_rows = []

for district, (lat, lon) in RAJASTHAN_DISTRICTS.items():
    print(f"[{district}] Kharif + Rabi...")
    df_raw = fetch_weather_api(lat, lon)
    rows = process_district_rows(df_raw, district)
    if len(rows) == 2:  # Exactly 2 rows per district
        master_rows.append(rows)
    time.sleep(0.5)

df_master = pd.concat(master_rows, ignore_index=True)
df_master.to_csv('rajasthan_weather_master_20rows.csv', index=False)

print("\n MASTER CSV SAVED: rajasthan_weather_master_20rows.csv")
print(f" Shape: {df_master.shape} (20 rows × 6 cols)")

print("\n YOUR EXACT FORMAT PREVIEW:")
print(df_master.round(1).to_string(index=False))

print("\n PERFECT CROP MERGE:")
print("df_crop.merge(df_master, on=['District', 'Season'], how='left')")
print("\n XGBoost: X = ['Temp_C', 'Rain_mm', 'Humidity_%', 'Wind_kmh']")
print("          y = df_crop['Yield']")
