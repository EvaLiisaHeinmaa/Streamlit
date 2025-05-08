import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(
    page_title="Estonian Population Data Visualization",
    page_icon="🇪🇪",
    layout="wide"
)

# Constants
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_URL = "https://gitlab.com/nutiteq/maakonnad/-/raw/master/maakonnad.geojson"

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
    """Fetch data from Statistikaamet API"""
    headers = {'Content-Type': 'application/json'}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text), sep=';')
        
        # Rename value column if needed
        if 'value' in df.columns:
            df = df.rename(columns={'value': 'Loomulik iive'})
        
        # Convert year to numeric
        if 'Aasta' in df.columns:
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
        
        # Convert value to numeric
        if 'Loomulik iive' in df.columns:
            df['Loomulik iive'] = pd.to_numeric(df['Loomulik iive'], errors='coerce')
        
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

def import_geojson():
    """Load GeoJSON from GitLab URL"""
    try:
        gdf = gpd.read_file(GEOJSON_URL)
        return gdf
    except Exception as e:
        st.error(f"Failed to load GeoJSON: {e}")
        return None

def get_data_for_year(df, year):
    """Filter data for specific year"""
    return df[df.Aasta == year]

def plot(gdf, data_for_year):
    """Create map visualization"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Group by county to get total for both genders
    county_data = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
    
    # Merge with GeoJSON
    merged = gdf.merge(county_data, left_on='MNIMI', right_on='Maakond', how='left')
    
    # Plot the map
    merged.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='RdYlGn',  # Red-Yellow-Green colormap
        edgecolor='black',
        linewidth=0.5,
        legend_kwds={
            'label': "Loomulik iive (sündide ja surmade vahe)",
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        }
    )
    
    plt.title(f'Loomulik iive maakonniti aastal {data_for_year.Aasta.iloc[0]}', fontsize=16)
    plt.axis('off')  # Hide axis
    plt.tight_layout()
    
    return fig

# Main app
def main():
    st.title("Eesti Loomulik Iive Maakonniti")
    st.write("Sündide ja surmade vahe visualiseerimine Eesti maakondades aastate lõikes.")
    
    # Load data
    with st.spinner("Loading data..."):
        df = import_data()
        gdf = import_geojson()
    
    if df.empty or gdf is None:
        st.error("Failed to load required data.")
        return
    
    # Sidebar for controls
    st.sidebar.header("Seaded")
    
    # Year selection
    available_years = sorted(df['Aasta'].unique())
    selected_year = st.sidebar.selectbox("Vali aasta:", available_years, index=len(available_years)-1)
    
    # Get data for selected year
    data_for_year = get_data_for_year(df, selected_year)
    
    # Display map
    st.subheader(f"Loomulik iive maakonniti aastal {selected_year}")
    fig = plot(gdf, data_for_year)
    st.pyplot(fig)
    
    # Display data table
    st.subheader("Andmed tabelina")
    st.dataframe(data_for_year, use_container_width=True)
    
    # Add data source information
    st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()
