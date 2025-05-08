import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# Set page title
st.title("Estonian Population Statistics")

# Constants - exactly as in your original code
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

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

# Function to import data - exactly as in your original code
def import_data():
    headers = {
        'Content-Type': 'application/json'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        print("Request successful.")       
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)
        df = pd.DataFrame()  # Return empty DataFrame on error
    return df

# Function to import GeoJSON - modified to load from URL
def import_geojson():
    # URL to a reliable Estonian counties GeoJSON
    geojson_url = "https://raw.githubusercontent.com/okestonia/opendata.riik.ee/master/img/datasets/maakond_20200101.geojson"
    
    try:
        gdf = gpd.read_file(geojson_url)
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON: {str(e)}")
        return None

# Function to get data for year - exactly as in your original code
def get_data_for_year(df, year):
    year_data = df[df.Aasta==year]
    return year_data

# Function to create plot - similar to your original function
def plot(df, gdf, year):
    # Get data for the selected year
    year_data = get_data_for_year(df, year)
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Just plot the GeoJSON for now
    gdf.plot(ax=ax, color='lightblue', edgecolor='black')
    
    plt.title(f'Estonian Counties {year}')
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Sidebar for year selection
st.sidebar.header("Controls")
selected_year = st.sidebar.selectbox(
    "Select Year",
    ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
)

# Load data
df = import_data()

# Show data table
st.write("## Data Table")
if not df.empty:
    year_data = get_data_for_year(df, selected_year)
    st.dataframe(year_data)
else:
    st.write("No data available.")

# Load GeoJSON and show map
gdf = import_geojson()

if gdf is not None:
    st.write("## Map")
    fig = plot(df, gdf, selected_year)
    st.pyplot(fig)
else:
    st.error("Failed to load map data.")
    
    # Provide option to upload GeoJSON file
    uploaded_file = st.file_uploader("Upload GeoJSON file", type=['geojson', 'json'])
    if uploaded_file is not None:
        try:
            gdf = gpd.read_file(uploaded_file)
            st.success("GeoJSON file uploaded successfully!")
            fig = plot(df, gdf, selected_year)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error reading uploaded file: {str(e)}")
