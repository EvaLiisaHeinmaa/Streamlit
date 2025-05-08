import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# Set page title
st.title("Estonian Population Statistics")

# Constants
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_URL = "https://gist.githubusercontent.com/nutiteq/1ab8f24f9a6ad2bb47da/raw/5a1e14a9d7cac15efe885dfa8199664679c6b1ab/maakonnad.geojson"

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
    
def import_data():
    headers = {
        'Content-Type': 'application/json'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    with st.spinner('Fetching data from Statistics Estonia...'):
        response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        st.success("Data successfully loaded!")
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"Failed to load data: {response.status_code}")
        st.text(response.text)
        return pd.DataFrame()

def import_geojson_from_github():
    try:
        with st.spinner('Loading geographic data from GitHub...'):
            # Fetch GeoJSON directly from GitHub Gist
            response = requests.get(GEOJSON_URL)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Read GeoJSON from response content
            gdf = gpd.read_file(StringIO(response.text))
            
            st.success("Map data successfully loaded!")
            return gdf
    except Exception as e:
        st.error(f"Error loading geographic data: {str(e)}")
        return None

def get_data_for_year(df, year):
    year_data = df[df.Aasta==year]
    return year_data

def create_plot(df, gdf, year, metric="Loomulik iive"):
    # Get data for selected year
    year_data = get_data_for_year(df, year)
    
    # Prepare data for merging
    # You'll need to adjust this based on your actual data structure
    # This assumes your GeoJSON has county names that match your data
    
    # Example: Prepare data to merge with GeoJSON
    # First, check the column names in both dataframes
    st.write("GeoJSON columns:", gdf.columns.tolist())
    
    # Create a figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # For demonstration, just plot the GeoJSON counties
    # You'll need to adjust this to merge with your actual data
    gdf.plot(
        ax=ax,
        color='lightblue',
        edgecolor='black'
    )
    
    plt.title(f'Estonian Counties {year}')
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Sidebar for controls
st.sidebar.header("Controls")
selected_year = st.sidebar.selectbox(
    "Select Year",
    ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
)

# Load the data
st.write("## Estonian Population Data")

df = import_data()

# Load GeoJSON from GitHub
gdf = import_geojson_from_github()

# Display map if GeoJSON loaded successfully
if gdf is not None:
    st.write("## Population Map")
    
    # Display the raw GeoJSON data for debugging
    st.write("### GeoJSON Preview (first few rows)")
    st.dataframe(gdf.head())
    
    # Create and display the map
    fig = create_plot(df, gdf, selected_year)
    st.pyplot(fig)

# Display data table
st.write("## Data Table")
if not df.empty:
    year_data = get_data_for_year(df, selected_year)
    st.dataframe(year_data)
else:
    st.write("No data available.")

# Footer
st.write("---")
st.write("Data source: Statistics Estonia")
st.write("Map data: [GitHub Gist by nutiteq](https://gist.github.com/nutiteq/1ab8f24f9a6ad2bb47da)")
