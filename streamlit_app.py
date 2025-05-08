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

# The correct raw URL for the GitHub Gist
GEOJSON_URL = "https://gist.githubusercontent.com/nutiteq/1ab8f24f9a6ad2bb47da/raw/maakonnad.geojson"

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
        
        # Convert year to numeric
        if 'Aasta' in df.columns:
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
        
        # Convert value to numeric
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.rename(columns={'value': 'Loomulik iive'})
        
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

def import_geojson():
    """Load GeoJSON from GitHub Gist URL with better error handling"""
    try:
        # First try direct read
        try:
            gdf = gpd.read_file(GEOJSON_URL)
            return gdf
        except:
            # If direct read fails, try downloading with requests first
            response = requests.get(GEOJSON_URL)
            if response.status_code == 200:
                # Save to a temporary file and read from there
                with open('temp_counties.geojson', 'w') as f:
                    f.write(response.text)
                gdf = gpd.read_file('temp_counties.geojson')
                return gdf
            else:
                # If that fails too, use a hardcoded simplified GeoJSON
                st.warning(f"Failed to download GeoJSON: {response.status_code}. Using embedded data.")
                
                # Simplified GeoJSON for Estonian counties
                counties_geojson = {
                    "type": "FeatureCollection",
                    "features": [
                        {"type": "Feature", "properties": {"MNIMI": "Harju maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[24.5, 59.5], [24.5, 59.0], [24.0, 59.0], [24.0, 59.5], [24.5, 59.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Hiiu maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[22.5, 59.0], [22.5, 58.7], [22.0, 58.7], [22.0, 59.0], [22.5, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Ida-Viru maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[27.5, 59.5], [27.5, 59.0], [27.0, 59.0], [27.0, 59.5], [27.5, 59.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Jõgeva maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[26.5, 59.0], [26.5, 58.5], [26.0, 58.5], [26.0, 59.0], [26.5, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Järva maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[25.5, 59.0], [25.5, 58.5], [25.0, 58.5], [25.0, 59.0], [25.5, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Lääne maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[23.5, 59.0], [23.5, 58.5], [23.0, 58.5], [23.0, 59.0], [23.5, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Lääne-Viru maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[26.0, 59.5], [26.0, 59.0], [25.5, 59.0], [25.5, 59.5], [26.0, 59.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Põlva maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[27.0, 58.5], [27.0, 58.0], [26.5, 58.0], [26.5, 58.5], [27.0, 58.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Pärnu maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[24.5, 58.5], [24.5, 58.0], [24.0, 58.0], [24.0, 58.5], [24.5, 58.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Rapla maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[24.5, 59.0], [24.5, 58.5], [24.0, 58.5], [24.0, 59.0], [24.5, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Saare maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[23.0, 58.5], [23.0, 58.0], [22.0, 58.0], [22.0, 58.5], [23.0, 58.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Tartu maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[27.0, 59.0], [27.0, 58.5], [26.5, 58.5], [26.5, 59.0], [27.0, 59.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Valga maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[26.5, 58.0], [26.5, 57.5], [26.0, 57.5], [26.0, 58.0], [26.5, 58.0]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Viljandi maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[25.5, 58.5], [25.5, 58.0], [25.0, 58.0], [25.0, 58.5], [25.5, 58.5]]]}},
                        {"type": "Feature", "properties": {"MNIMI": "Võru maakond"}, "geometry": {"type": "Polygon", "coordinates": [[[27.5, 58.0], [27.5, 57.5], [27.0, 57.5], [27.0, 58.0], [27.5, 58.0]]]}}
                    ]
                }
                
                # Save to a temporary file and read from there
                with open('temp_counties.geojson', 'w') as f:
                    json.dump(counties_geojson, f)
                
                gdf = gpd.read_file('temp_counties.geojson')
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
    
    # Merge with GeoJSON - the county name field in this GeoJSON is 'MNIMI'
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
    
    # Create pivot table with gender breakdown if possible
    if 'Sugu' in data_for_year.columns:
        pivot_data = data_for_year.pivot_table(
            index='Maakond', 
            columns='Sugu', 
            values='Loomulik iive',
            aggfunc='sum'
        ).reset_index()
        
        pivot_data.columns.name = None
        
        # Add total column
        county_totals = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
        pivot_data = pivot_data.merge(county_totals, on='Maakond')
        pivot_data = pivot_data.rename(columns={'Loomulik iive': 'Kokku'})
        
        # Sort by total
        pivot_data = pivot_data.sort_values('Kokku', ascending=False)
        
        st.dataframe(pivot_data, use_container_width=True)
    else:
        st.dataframe(data_for_year, use_container_width=True)
    
    # Add data source information
    st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()
