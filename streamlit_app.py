import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import os

st.title("Estonian Population Natural Growth by County")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"  # Path to your local geojson file

JSON_PAYLOAD_STR = """ {
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014",
          "2015",
          "2016",
          "2017",
          "2018",
          "2019",
          "2020",
          "2021",
          "2022",
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39",
          "44",
          "49",
          "51",
          "57",
          "59",
          "65",
          "67",
          "70",
          "74",
          "78",
          "82",
          "84",
          "86"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": [
          "2",
          "3"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}
"""

@st.cache_data
def import_data():
    headers = {
        'Content-Type': 'application/json'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    with st.spinner('Fetching data from Statistics Estonia...'):
        response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        st.success("Data successfully retrieved!")
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))

        # --- Debugging: Print columns of the raw data ---
        st.write("Columns in raw data (df):", df.columns.tolist())
        st.write("Sample data (first 5 rows):")
        st.dataframe(df.head())
        # --- End Debugging ---
        
        return df
    else:
        st.error(f"Failed to retrieve data: {response.status_code}")
        st.write(response.text)
        return None

@st.cache_data
def import_geojson():
    try:
        # Check if file exists
        if not os.path.exists(GEOJSON_FILE):
            st.error(f"GeoJSON file not found: {GEOJSON_FILE}")
            st.info("Make sure the file is in the same directory as your Streamlit app.")
            return None
        
        with st.spinner('Loading geographic data...'):
            gdf = gpd.read_file(GEOJSON_FILE)
            
            # --- Debugging: Print columns of the GeoJSON data ---
            st.write("Columns in GeoJSON (gdf):", gdf.columns.tolist())
            # --- End Debugging ---
            
            return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def process_data_and_calculate_natural_growth(df):
    """Process the data from Statistics Estonia and calculate natural growth."""
    # First, examine the actual column names to determine the structure
    st.write("Data structure analysis:")
    
    # Check if we have sex
