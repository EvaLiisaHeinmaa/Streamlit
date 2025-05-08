import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# --- Constants ---
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_PATH = "maakonnad.geojson"

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
    response = requests.post(STATISTIKAAMETI_API_URL, json=json.loads(JSON_PAYLOAD_STR), headers=headers)

    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"API request failed: {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(GEOJSON_PATH)

def get_data_for_year(df, year):
    return df[df["Aasta"] == year]

def plot_map(merged, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    merged.plot(column="Loomulik iive", 
                ax=ax,
                legend=True,
                cmap='viridis',
                legend_kwds={'label': "Loomulik iive"})
    plt.title(f'Loomulik iive maakonniti aastal {year}')
    plt.axis('off')
    plt.tight_layout()
    st.pyplot(fig)

# --- Streamlit App ---
def main():
    st.title("📊 Loomulik iive maakonniti")

    # Load data
    df = import_data()
    gdf = import_geojson()

    # Year selection
    years = sorted(df["Aasta"].unique())
    selected_year = st.selectbox("Vali aasta:", years, index=len(years)-1)

    # Filter for year
    year_df = get_data_for_year(df, selected_year)

    # Merge by 'MNIMI' (must be present in both gdf and df)
    if "MNIMI" not in df.columns or "MNIMI" not in gdf.columns:
        st.error("❌ Veerg 'MNIMI' puudub kas Statistikaameti või geojsoni andmetes.")
        return

    merged = gdf.merge(year_df, on="MNIMI", how="left")

    # Plot
    if "Loomulik iive" not in merged.columns or merged["Loomulik iive"].dropna().empty:
        st.warning("⚠️ 'Loomulik iive' andmed puuduvad selle aasta kohta.")
    else:
        plot_map(merged, selected_year)

if __name__ == "__main__":
    main()
