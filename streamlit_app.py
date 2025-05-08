import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
from urllib.request import urlopen

# Set page configuration
st.set_page_config(
    page_title="Estonian Population Data Visualization",
    page_icon="🇪🇪",
    layout="wide"
)

# Constants
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_URL = "https://raw.githubusercontent.com/buildig/EHAK/master/geojson/maakond.geojson"

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
        
        try:
            df = pd.read_csv(StringIO(text), sep=';')
        except:
            df = pd.read_csv(StringIO(text), sep=',')
        
        # Rename columns if needed
        if 'value' in df.columns:
            df = df.rename(columns={'value': 'Loomulik iive'})
        
        for col in df.columns:
            if 'aasta' in col.lower():
                df = df.rename(columns={col: 'Aasta'})
            elif 'maakond' in col.lower():
                df = df.rename(columns={col: 'Maakond'})
            elif 'sugu' in col.lower():
                df = df.rename(columns={col: 'Sugu'})
        
        # Convert to numeric
        if 'Aasta' in df.columns:
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
        if 'Loomulik iive' in df.columns:
            df['Loomulik iive'] = pd.to_numeric(df['Loomulik iive'], errors='coerce')
        
        return df
    else:
        st.error(f"API request failed: {response.status_code}")
        return pd.DataFrame()

def import_geojson():
    """Load GeoJSON data from URL"""
    try:
        with urlopen(GEOJSON_URL) as response:
            gdf = gpd.read_file(response)
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

def get_data_for_year(df, year):
    """Filter data for specific year"""
    return df[df.Aasta == year]

def plot(gdf, data_for_year):
    """Create map visualization"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Group by county to get total for both genders
    county_data = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
    
    # Find the county name field in GeoJSON
    county_field = None
    for field in ['MNIMI', 'name', 'ONIMI']:
        if field in gdf.columns:
            county_field = field
            break
    
    if county_field is None:
        st.error("Could not identify county name field in GeoJSON")
        return fig
    
    # Create county name mapping
    county_mapping = {}
    for county in gdf[county_field]:
        clean_name = county.replace(' maakond', '') if isinstance(county, str) else county
        county_mapping[clean_name] = county
        county_mapping[county] = county
    
    # Add mapped column
    county_data['Maakond_mapped'] = county_data['Maakond'].map(lambda x: county_mapping.get(x, x))
    
    # Merge with GeoJSON
    merged = gdf.merge(county_data, left_on=county_field, right_on='Maakond_mapped', how='left')
    
    # Plot the map
    merged.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='RdYlGn',
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
    
    plt.title(f'Loomulik iive maakonniti aastal {data_for_year.Aasta.iloc[0]}', fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Main app
def main():
    st.title("Eesti Loomulik Iive Maakonniti")
    st.write("Sündide ja surmade vahe visualiseerimine Eesti maakondades aastate lõikes.")
    
    # Load data
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
    
    # Add total statistic
    total_growth = data_for_year['Loomulik iive'].sum()
    st.metric(
        label="Eesti loomulik iive kokku", 
        value=f"{total_growth:,.0f}".replace(',', ' '),
        delta=None
    )
    
    # Add data source information
    st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()

