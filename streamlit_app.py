import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

JSON_PAYLOAD_STR =""" {
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39", "44", "49", "51", "57", "59", "65", "67",
          "70", "74", "78", "82", "84", "86"
        ]
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
  "response": { "format": "csv" }
}"""

geojson_file = "maakonnad.geojson"

@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    response = requests.post(STATISTIKAAMETI_API_URL, json=json.loads(JSON_PAYLOAD_STR), headers=headers)

    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.content.decode('utf-8-sig')))
        return df
    else:
        st.error("Failed to fetch data.")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(geojson_file)

def main():
    st.title("Loomulik iive maakonniti")

    df = import_data()
    gdf = import_geojson()

    if df.empty or gdf.empty:
        st.warning("Data not available.")
        return

    # Merge data with geojson
    merged = gdf.merge(df, left_on="MNIMI", right_on="Maakond", how="left")

    # Check column names before plotting
    st.write("Available columns:", merged.columns.tolist())

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    merged.plot(column="Loomulik iive", ax=ax, legend=True,
                cmap="viridis", legend_kwds={"label": "Loomulik iive"})
    plt.axis("off")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
