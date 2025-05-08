import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

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

geojson = "maakonnad.geojson"

@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)

    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"Failed with status code: {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(geojson)

def get_data_for_year(df, year):
    return df[df["Aasta"] == year]

def main():
    st.title("Loomulik iive maakonniti")

    year = st.selectbox("Vali aasta", list(range(2014, 2024)))

    df = import_data()
    gdf = import_geojson()

    year_df = get_data_for_year(df, year)
    
    # Rename or adjust merge column names as needed
    merged = gdf.merge(year_df, left_on="MNIMI", right_on="Maakond", how="left")  # Adjust this if needed

    st.subheader(f"Loomulik iive {year}")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    merged.plot(column="Loomulik iive", ax=ax, legend=True, cmap="viridis", legend_kwds={"label": "Loomulik iive"})
    plt.axis("off")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
