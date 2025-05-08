import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Estonian Population Data Visualization",
    page_icon="🇪🇪",
    layout="wide"
)

# Constants
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

# Multiple GeoJSON sources to try
GEOJSON_URLS = [
    "https://raw.githubusercontent.com/okestonia/Estonian-Open-Geodata/master/geojson/maakond.geojson",
    "https://raw.githubusercontent.com/buildig/EHAK/master/geojson/maakond.geojson",
    "https://raw.githubusercontent.com/buildig/Estonian-Open-Geodata/master/geojson/maakond.geojson"
]

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

# Create sample data in case API fails
def create_sample_data():
    counties = [
        "Harju maakond", "Hiiu maakond", "Ida-Viru maakond", "Jõgeva maakond",
        "Järva maakond", "Lääne maakond", "Lääne-Viru maakond", "Põlva maakond",
        "Pärnu maakond", "Rapla maakond", "Saare maakond", "Tartu maakond",
        "Valga maakond", "Viljandi maakond", "Võru maakond"
    ]
    
    genders = ["Mehed", "Naised"]
    years = list(range(2014, 2024))
    
    data = []
    for year in years:
        for county in counties:
            for gender in genders:
                # Generate some realistic-looking data
                value = np.random.randint(-100, 100) if county != "Harju maakond" else np.random.randint(0, 500)
                data.append({
                    'Aasta': year,
                    'Maakond': county,
                    'Sugu': gender,
                    'Loomulik iive': value
                })
    
    return pd.DataFrame(data)

def import_data():
    """Fetch data from Statistikaamet API with robust error handling"""
    try:
        headers = {'Content-Type': 'application/json'}
        parsed_payload = json.loads(JSON_PAYLOAD_STR)
        response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
        
        if response.status_code == 200:
            text = response.content.decode('utf-8-sig')
            
            # Try different separators
            try:
                df = pd.read_csv(StringIO(text), sep=';')
            except:
                try:
                    df = pd.read_csv(StringIO(text), sep=',')
                except:
                    st.warning("Could not parse API response. Using sample data instead.")
                    return create_sample_data()
            
            # Display raw data for debugging
            with st.expander("Raw API Response"):
                st.text(text[:1000] + "..." if len(text) > 1000 else text)
                st.dataframe(df)
            
            # Check if we have the expected columns
            if 'Aasta' not in df.columns:
                # Try to identify year column
                for col in df.columns:
                    if col.lower() in ['aasta', 'year', 'time']:
                        df = df.rename(columns={col: 'Aasta'})
                        break
            
            if 'Maakond' not in df.columns:
                # Try to identify county column
                for col in df.columns:
                    if col.lower() in ['maakond', 'county', 'region']:
                        df = df.rename(columns={col: 'Maakond'})
                        break
            
            if 'Sugu' not in df.columns:
                # Try to identify gender column
                for col in df.columns:
                    if col.lower() in ['sugu', 'gender', 'sex']:
                        df = df.rename(columns={col: 'Sugu'})
                        break
            
            # Identify value column
            value_col = None
            for col in df.columns:
                if col.lower() in ['value', 'loomulik iive', 'natural increase']:
                    value_col = col
                    break
            
            if value_col:
                df = df.rename(columns={value_col: 'Loomulik iive'})
            
            # If we still don't have the required columns, use sample data
            if 'Aasta' not in df.columns or 'Maakond' not in df.columns or 'Loomulik iive' not in df.columns:
                st.warning("API response doesn't contain required columns. Using sample data instead.")
                return create_sample_data()
            
            # Convert to numeric
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
            df['Loomulik iive'] = pd.to_numeric(df['Loomulik iive'], errors='coerce')
            
            return df
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            st.write(response.text)
            return create_sample_data()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return create_sample_data()

def import_geojson():
    """Try multiple GeoJSON sources"""
    for url in GEOJSON_URLS:
        try:
            st.info(f"Trying to load GeoJSON from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                # Load GeoJSON from response content
                gdf = gpd.read_file(StringIO(response.text))
                st.success(f"Successfully loaded GeoJSON from {url}")
                return gdf
            else:
                st.warning(f"Failed to download GeoJSON from {url}: {response.status_code}")
        except Exception as e:
            st.warning(f"Error loading GeoJSON from {url}: {e}")
    
    # If all URLs fail, create a simple GeoJSON with county names
    st.warning("All GeoJSON sources failed. Creating a simplified version.")
    
    # Create a simple GeoJSON with county names
    counties = [
        "Harju maakond", "Hiiu maakond", "Ida-Viru maakond", "Jõgeva maakond",
        "Järva maakond", "Lääne maakond", "Lääne-Viru maakond", "Põlva maakond",
        "Pärnu maakond", "Rapla maakond", "Saare maakond", "Tartu maakond",
        "Valga maakond", "Viljandi maakond", "Võru maakond"
    ]
    
    # Create a simple GeoDataFrame with county names
    gdf = gpd.GeoDataFrame({
        'MAAKOND': counties,
        'geometry': [None] * len(counties)
    })
    
    return gdf

def get_data_for_year(df, year):
    """Filter data for specific year"""
    return df[df.Aasta == year]

def plot(gdf, data_for_year):
    """Create map visualization with robust error handling"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    try:
        # Group by county to get total for both genders
        county_data = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
        
        # Find the county name field in GeoJSON
        county_field = None
        for field in ['MAAKOND', 'MNIMI', 'name', 'ONIMI', 'maakond']:
            if field in gdf.columns:
                county_field = field
                break
        
        if county_field is None:
            st.error("Could not identify county name field in GeoJSON")
            st.write("Available fields:", gdf.columns.tolist())
            # Plot just the boundaries
            if None not in gdf.geometry.values:
                gdf.plot(ax=ax, edgecolor='black', facecolor='lightgrey')
            return fig
        
        # Create a mapping between county names in data and GeoJSON
        county_mapping = {}
        
        # Clean county names for matching
        for county in county_data['Maakond']:
            clean_county = county.replace(' maakond', '').lower() if isinstance(county, str) else county
            county_mapping[clean_county] = county
        
        for county in gdf[county_field]:
            clean_county = county.replace(' maakond', '').lower() if isinstance(county, str) else county
            if clean_county in county_mapping:
                county_mapping[county] = county_mapping[clean_county]
        
        # Add the mapping as a column to the GeoJSON
        gdf['mapped_county'] = gdf[county_field].apply(
            lambda x: county_mapping.get(x.replace(' maakond', '').lower(), None) 
            if isinstance(x, str) else None
        )
        
        # Merge with GeoJSON
        if None not in gdf.geometry.values:
            merged = gdf.merge(county_data, left_on='mapped_county', right_on='Maakond', how='left')
            
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
        else:
            # If we don't have geometry, create a bar chart instead
            county_data = county_data.sort_values('Loomulik iive')
            county_data.plot(
                kind='barh', 
                x='Maakond', 
                y='Loomulik iive', 
                ax=ax,
                color=county_data['Loomulik iive'].apply(
                    lambda x: 'green' if x > 0 else 'red'
                )
            )
            plt.xlabel('Loomulik iive')
            plt.ylabel('Maakond')
            
    except Exception as e:
        st.error(f"Error creating map: {e}")
        # Create a simple bar chart of the data
        try:
            county_data = data_for_year.groupby('Maakond')['Loomulik iive'].sum().reset_index()
            county_data = county_data.sort_values('Loomulik iive')
            county_data.plot(
                kind='barh', 
                x='Maakond', 
                y='Loomulik iive', 
                ax=ax,
                color=county_data['Loomulik iive'].apply(
                    lambda x: 'green' if x > 0 else 'red'
                )
            )
            plt.xlabel('Loomulik iive')
            plt.ylabel('Maakond')
        except:
            ax.text(0.5, 0.5, "Could not create visualization", 
                   horizontalalignment='center', verticalalignment='center')
    
    plt.title(f'Loomulik iive maakonniti aastal {data_for_year.Aasta.iloc[0]}', fontsize=16)
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
        try:
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
        except:
            st.dataframe(data_for_year, use_container_width=True)
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
