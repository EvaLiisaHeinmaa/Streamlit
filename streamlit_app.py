import streamlit as st
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from io import StringIO
import json

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_PATH = "maakonnad.geojson"  # Make sure this file is in your GitHub repo

# The API query payload
JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2023"]
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

@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    response = requests.post(STATISTIKAAMETI_API_URL, json=json.loads(JSON_PAYLOAD_STR), headers=headers)
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"API request failed with status code {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(GEOJSON_PATH)

def main():
    st.title("Loomulik iive maakondade lõikes – 2023")

    df = import_data()
    gdf = import_geo_
