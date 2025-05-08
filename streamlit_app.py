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
geojson = "maakonnad.geojson"
    
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

def import_geojson():
    try:
        with st.spinner('Loading geographic data...'):
            gdf = gpd.read_file(geojson)
        return gdf
    except Exception as e:
        st.error(f"Error loading geographic data: {str(e)}")
        st.write("Note: If you're having issues with the GeoJSON file, try finding a smaller version.")
        return None

def get_data_for_year(df, year):
    year_data = df[df.Aasta==year]
    return year_data

def create_plot(df, gdf, year):
    # Get data for selected year
    year_data = get_data_for_year(df, year)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Plot the data
    # Note: You may need to adjust this depending on how your data needs to be joined with the GeoJSON
    merged_data = gdf.copy()
    # This is a placeholder - you'll need to adjust how the data is merged with the GeoJSON
    # merged_data = gdf.merge(year_data, left_on='COUNTY_NAME', right_on='Maakond')
    
    merged_data.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='viridis',
        legend_kwds={'label': "Loomulik iive"}
    )
    
    plt.title(f'Loomulik iive maakonniti aastal {year}')
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
st.write("Loading data, please wait...")

df = import_data()

# About the GeoJSON issue
st.write("## About the Map")
st.info("""
Note: This app requires a GeoJSON file for Estonian counties. 
If you're having trouble with a large file, consider:
1. Finding a smaller version of Estonian county boundaries
2. Using a simplification tool like mapshaper.org
3. Using an alternative source like GADM or Natural Earth Data
""")

# Try to load GeoJSON if available
try:
    gdf = import_geojson()
    if gdf is not None:
        st.write("## Population Map")
        fig = create_plot(df, gdf, selected_year)
        st.pyplot(fig)
except Exception as e:
    st.error(f"Could not create map: {str(e)}")
    st.write("Map display is unavailable. Please check your GeoJSON file.")

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
