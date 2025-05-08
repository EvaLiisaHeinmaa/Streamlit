import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from urllib.request import urlopen

# Set page configuration
st.set_page_config(
    page_title="Estonian Population Data Visualization",
    page_icon="🇪🇪",
    layout="wide"
)

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

# Alternative GeoJSON URL if local file doesn't work
GEOJSON_URL = "https://raw.githubusercontent.com/okestonia/opendata.riik.ee/master/datasets/maakond/maakond.geojson"
LOCAL_GEOJSON = "maakonnad.geojson"

def import_data():
    """Fetch data from Statistikaamet API"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        st.success("Data successfully retrieved!")
        text = response.content.decode('utf-8-sig')
        
        # Try different separators
        try:
            df = pd.read_csv(StringIO(text), sep=';')
        except:
            try:
                df = pd.read_csv(StringIO(text), sep=',')
            except Exception as e:
                st.error(f"Failed to parse CSV: {e}")
                st.text(text[:1000])  # Show part of the text for debugging
                return pd.DataFrame()
        
        # Rename columns to match expected format
        if 'value' in df.columns:
            df = df.rename(columns={'value': 'Loomulik iive'})
        
        # Find and rename year column
        for col in df.columns:
            if 'aasta' in col.lower():
                df = df.rename(columns={col: 'Aasta'})
            elif 'maakond' in col.lower():
                df = df.rename(columns={col: 'Maakond'})
            elif 'sugu' in col.lower():
                df = df.rename(columns={col: 'Sugu'})
        
        # Convert year to numeric
        if 'Aasta' in df.columns:
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
        
        # Convert value to numeric
        if 'Loomulik iive' in df.columns:
            df['Loomulik iive'] = pd.to_numeric(df['Loomulik iive'], errors='coerce')
        
        return df
    else:
        st.error(f"Failed with status code: {response.status_code}")
        st.text(response.text)
        return pd.DataFrame()

def import_geojson():
    """Load GeoJSON data from local file or URL"""
    try:
        # First try to load from local file
        if os.path.exists(LOCAL_GEOJSON):
            gdf = gpd.read_file(LOCAL_GEOJSON)
            st.success("Loaded GeoJSON from local file")
        else:
            # If local file doesn't exist, try to load from URL
            st.warning(f"Local GeoJSON file '{LOCAL_GEOJSON}' not found. Trying to load from URL...")
            with urlopen(GEOJSON_URL) as response:
                gdf = gpd.read_file(response)
            st.success("Loaded GeoJSON from URL")
        
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

def get_data_for_year(df, year):
    """Filter data for specific year"""
    year_data = df[df.Aasta == year]
    return year_data

def plot(gdf, data_for_year):
    """Create map visualization"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Prepare data for mapping
    # Group by county to get total for both genders
    county_data = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
    
    # Create a mapping dictionary for county names
    county_mapping = {}
    
    # Check what field in GeoJSON contains county names
    county_field = None
    for field in ['MNIMI', 'name', 'NAME', 'County', 'COUNTY', 'maakond', 'MAAKOND']:
        if field in gdf.columns:
            county_field = field
            break
    
    if county_field is None:
        st.error("Could not identify county name field in GeoJSON")
        st.write("Available fields:", gdf.columns.tolist())
        return fig
    
    # Create mapping based on county field
    for county in gdf[county_field]:
        # Remove "maakond" suffix if present for matching
        clean_name = county.replace(' maakond', '') if isinstance(county, str) else county
        county_mapping[clean_name] = county
        county_mapping[county] = county  # Also keep original
    
    # Add mapping for counties with or without "maakond" suffix
    for county in county_data['Maakond']:
        if isinstance(county, str):
            if ' maakond' in county:
                base_name = county.replace(' maakond', '')
                county_mapping[base_name] = county
            else:
                county_mapping[f"{county} maakond"] = county
    
    # Create a new column with mapped names
    county_data['Maakond_mapped'] = county_data['Maakond'].map(lambda x: county_mapping.get(x, x))
    
    # Merge with GeoJSON
    merged = gdf.merge(county_data, left_on=county_field, right_on='Maakond_mapped', how='left')
    
    # Plot the map
    merged.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='RdYlGn',  # Red-Yellow-Green colormap
        edgecolor='black',
        linewidth=0.5,
        missing_kwds={'color': 'lightgrey', 'label': 'No data'},
        legend_kwds={
            'label': "Loomulik iive (sündide ja surmade vahe)",
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        }
    )
    
    plt.title('Loomulik iive maakonniti', fontsize=16)
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
        st.error("Failed to load required data. Please check your data sources.")
        return
    
    # Sidebar for controls
    st.sidebar.header("Seaded")
    
    # Year selection
    available_years = sorted(df['Aasta'].unique())
    selected_year = st.sidebar.selectbox("Vali aasta:", available_years, index=len(available_years)-1)
    
    # Display info about natural growth
    st.sidebar.subheader("Mis on loomulik iive?")
    st.sidebar.info(
        "Loomulik iive on sündide ja surmade vahe. "
        "Positiivne väärtus näitab, et sünde on rohkem kui surmasid. "
        "Negatiivne väärtus näitab, et surmasid on rohkem kui sünde."
    )
    
    # Get data for selected year
    data_for_year = get_data_for_year(df, selected_year)
    
    # Display map
    st.subheader(f"Loomulik iive maakonniti aastal {selected_year}")
    fig = plot(gdf, data_for_year)
    st.pyplot(fig)
    
    # Display data table
    st.subheader("Andmed tabelina")
    
    # Check if we have gender information
    if 'Sugu' in data_for_year.columns:
        # Create a pivot table with gender breakdown
        pivot_data = data_for_year.pivot_table(
            index='Maakond', 
            columns='Sugu', 
            values='Loomulik iive',
            aggfunc='sum'
        ).reset_index()
        
        # Rename columns for clarity
        pivot_data.columns.name = None
        
        # Add total column
        county_totals = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
        pivot_data = pivot_data.merge(county_totals, on='Maakond')
        pivot_data = pivot_data.rename(columns={'Loomulik iive': 'Kokku'})
        
        # Sort by total natural growth
        pivot_data = pivot_data.sort_values('Kokku', ascending=False)
        
        # Display the table
        st.dataframe(pivot_data, use_container_width=True)
    else:
        # Just display the raw data
        st.dataframe(data_for_year, use_container_width=True)
    
    # Add some statistics
    try:
        total_growth = data_for_year['Loomulik iive'].sum()
        st.metric(
            label="Eesti loomulik iive kokku", 
            value=f"{total_growth:,.0f}".replace(',', ' '),
            delta=None
        )
    except:
        st.warning("Could not calculate total natural growth")
    
    # Add data source information
    st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()
