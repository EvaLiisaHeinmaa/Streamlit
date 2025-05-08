import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

st.title("Estonian Population Natural Growth by County")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

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
    """Fetch data from Statistics Estonia API"""
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
        return df
    else:
        st.error(f"Failed to retrieve data: {response.status_code}")
        st.write(response.text)
        return None

@st.cache_data
def import_geojson():
    """Load GeoJSON file"""
    try:
        with st.spinner('Loading geographic data...'):
            gdf = gpd.read_file(GEOJSON_FILE)
            return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def get_data_for_year(df, year):
    """Filter data for a specific year"""
    if df is not None:
        year_data = df[df.Aasta == year]
        return year_data
    return None

def create_plot(df, year):
    """Create a choropleth map for the selected year"""
    if df is None or len(df) == 0:
        return None
        
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    df.plot(column='Loomulik iive', 
            ax=ax,
            legend=True,
            cmap='viridis',
            legend_kwds={'label': "Loomulik iive"})
    
    plt.title(f'Loomulik iive maakonniti aastal {year}')
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Main app flow
df = import_data()
gdf = import_geojson()

if df is not None and gdf is not None:
    # Merge the data with the geodataframe
    merged_data = gdf.merge(df, left_on='MNIMI', right_on='Maakond')
    
    # Calculate the total natural growth
    merged_data["Loomulik iive"] = merged_data["Mehed Loomulik iive"] + merged_data["Naised Loomulik iive"]
    
    # Display some basic info about the data
    st.subheader("Data Overview")
    st.write(f"Data contains years from {merged_data['Aasta'].min()} to {merged_data['Aasta'].max()}")
    st.write(f"Geographic data loaded with {len(gdf)} counties")
    
    # Year selection
    years = sorted(merged_data['Aasta'].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)  # Default to latest year
    
    # Get data for selected year
    year_data = get_data_for_year(merged_data, selected_year)
    
    # Create and display the plot
    fig = create_plot(year_data, selected_year)
    if fig:
        st.pyplot(fig)
    else:
        st.warning("No data available for the selected year.")
    
    # Show the data for the selected year
    with st.expander("View Data Table"):
        st.dataframe(year_data)
    
    # Add download button for the selected year's data
    csv = year_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=f"population_growth_{selected_year}.csv",
        mime="text/csv"
    )
else:
    st.warning("Please make sure all data files are available before proceeding.")
