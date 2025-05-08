import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import json
from io import StringIO

# --- Constants ---
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
@st.cache_data
def import_geojson():
    return gpd.read_file("maakonnad.geojson")

# --- JSON payload to query the API ---
JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": ["39", "44", "49", "51", "57", "59", "65", "67", "70", "74", "78", "82", "84", "86"]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""

# --- Functions ---
@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        return pd.read_csv(StringIO(text))
    else:
        st.error(f"Failed to load data: {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(GEOJSON_URL)

def merge_data(api_df, geo_df, year):
    # Filter and group API data
    year_df = api_df[api_df["Aasta"] == int(year)]
    grouped = year_df.groupby("Maakond")["Loomulik iive"].sum().reset_index()
    grouped["ADM1_NO"] = grouped["Maakond"].astype(int)

    # Prepare GeoJSON and merge
    geo_df["ADM1_NO"] = geo_df["ADM1_NO"].astype(int)
    merged = geo_df.merge(grouped, on="ADM1_NO")
    return merged

def plot_map(gdf, year):
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    gdf.plot(column='Loomulik iive', ax=ax, legend=True, cmap='viridis', edgecolor='black',
             legend_kwds={'label': "Loomulik iive", 'shrink': 0.6})
    ax.set_title(f"Loomulik iive maakonniti ({year})", fontsize=15)
    ax.axis('off')
    st.pyplot(fig)

# --- Streamlit UI ---
st.title("Eesti Statistika: Loomulik iive Maakonniti")

df = import_data()
gdf = import_geojson()

if not df.empty and not gdf.empty:
    year = st.selectbox("Vali aasta:", sorted(df["Aasta"].unique(), reverse=True))
    merged_gdf = merge_data(df, gdf, year)
    plot_map(merged_gdf, year)
else:
    st.warning("Andmete või geoandmete laadimine ebaõnnestus.")
