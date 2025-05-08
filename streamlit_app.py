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

# Functions
@st.cache_data
def import_data():
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'text/csv'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    with st.spinner('Fetching data from Statistikaamet...'):
        try:
            response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
            
            if response.status_code == 200:
                st.success("Data successfully retrieved!")
                text = response.content.decode('utf-8-sig')
                
                # Try to parse the CSV
                try:
                    # First try with comma separator
                    df = pd.read_csv(StringIO(text), sep=',')
                    
                    # If that didn't work well, try with semicolon
                    if df.shape[1] <= 1:
                        df = pd.read_csv(StringIO(text), sep=';')
                    
                    # Clean up column names (remove any whitespace)
                    df.columns = df.columns.str.strip()
                    
                    # Show dataframe info in an expander
                    with st.expander("Data Preview"):
                        st.write(f"Shape: {df.shape}")
                        st.write("Columns:", df.columns.tolist())
                        st.dataframe(df.head())
                    
                    # Convert value column to numeric if needed
                    if 'value' in df.columns:
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    
                    return df
                
                except Exception as e:
                    st.error(f"Error parsing CSV data: {e}")
                    st.text(text[:1000])  # Show part of the raw text to help debug
                    return pd.DataFrame()
            else:
                st.error(f"Failed with status code: {response.status_code}")
                st.text(response.text)
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Request error: {e}")
            return pd.DataFrame()

@st.cache_data
def import_geojson():
    try:
        gdf = gpd.read_file(geojson)
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def process_data(df):
    """Process the raw data from the API into a usable format"""
    # Check the structure of the dataframe
    if 'value' in df.columns:
        # Typical structure from Statistikaamet API
        # Rename columns for clarity
        column_mapping = {}
        
        # Map dimension columns based on what's available
        for col in df.columns:
            if 'aasta' in col.lower():
                column_mapping[col] = 'Aasta'
            elif 'maakond' in col.lower():
                column_mapping[col] = 'Maakond'
            elif 'sugu' in col.lower():
                column_mapping[col] = 'Sugu'
        
        # Add value column mapping
        if 'value' in df.columns:
            column_mapping['value'] = 'Loomulik iive'
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert year to numeric if it's not already
        if 'Aasta' in df.columns:
            df['Aasta'] = pd.to_numeric(df['Aasta'], errors='coerce')
        
        # Convert value to numeric
        if 'Loomulik iive' in df.columns:
            df['Loomulik iive'] = pd.to_numeric(df['Loomulik iive'], errors='coerce')
    
    return df

def get_data_for_year(df, year):
    """Filter data for a specific year"""
    year_data = df[df.Aasta == year]
    return year_data

def prepare_map_data(df, gdf, year):
    """Prepare data for mapping by merging with geodata"""
    # Filter data for the selected year
    year_data = get_data_for_year(df, year)
    
    # Aggregate data by county (sum for both genders)
    county_data = year_data.groupby('Maakond')['Loomulik iive'].sum().reset_index()
    
    # Debug the county names
    with st.expander("Debug County Names"):
        st.write("GeoJSON county names:", gdf['MNIMI'].tolist())
        st.write("Data county names:", county_data['Maakond'].tolist())
    
    # Try to match county names between datasets
    # First, create a mapping dictionary for common variations
    county_mapping = {
        'Harju maakond': 'Harju maakond',
        'Hiiu maakond': 'Hiiu maakond',
        'Ida-Viru maakond': 'Ida-Viru maakond',
        'Jõgeva maakond': 'Jõgeva maakond',
        'Järva maakond': 'Järva maakond',
        'Lääne maakond': 'Lääne maakond',
        'Lääne-Viru maakond': 'Lääne-Viru maakond',
        'Põlva maakond': 'Põlva maakond',
        'Pärnu maakond': 'Pärnu maakond',
        'Rapla maakond': 'Rapla maakond',
        'Saare maakond': 'Saare maakond',
        'Tartu maakond': 'Tartu maakond',
        'Valga maakond': 'Valga maakond',
        'Viljandi maakond': 'Viljandi maakond',
        'Võru maakond': 'Võru maakond',
        # Add variations without "maakond"
        'Harju': 'Harju maakond',
        'Hiiu': 'Hiiu maakond',
        'Ida-Viru': 'Ida-Viru maakond',
        'Jõgeva': 'Jõgeva maakond',
        'Järva': 'Järva maakond',
        'Lääne': 'Lääne maakond',
        'Lääne-Viru': 'Lääne-Viru maakond',
        'Põlva': 'Põlva maakond',
        'Pärnu': 'Pärnu maakond',
        'Rapla': 'Rapla maakond',
        'Saare': 'Saare maakond',
        'Tartu': 'Tartu maakond',
        'Valga': 'Valga maakond',
        'Viljandi': 'Viljandi maakond',
        'Võru': 'Võru maakond'
    }
    
    # Map county names in the data to match GeoJSON
    county_data['Maakond_mapped'] = county_data['Maakond'].map(county_mapping)
    
    # Use the mapped names for merging
    merged_data = gdf.merge(county_data, left_on='MNIMI', right_on='Maakond_mapped', how='left')
    
    return merged_data

def plot_map(merged_data, year):
    """Create a choropleth map visualization"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Check if we have data to plot
    if 'Loomulik iive' not in merged_data.columns or merged_data['Loomulik iive'].isna().all():
        ax.text(0.5, 0.5, 'No data available for this year', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        plt.axis('off')
        return fig
    
    # Find the min and max values for consistent color scale
    vmin = merged_data['Loomulik iive'].min()
    vmax = merged_data['Loomulik iive'].max()
    
    # Ensure the color scale is centered at zero
    abs_max = max(abs(vmin), abs(vmax))
    vmin = -abs_max
    vmax = abs_max
    
    # Create the choropleth map
    merged_data.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='RdYlGn',  # Red-Yellow-Green colormap (negative values in red, positive in green)
        edgecolor='black',
        linewidth=0.5,
        vmin=vmin,
        vmax=vmax,
        missing_kwds={'color': 'lightgrey', 'label': 'No data'},
        legend_kwds={
            'label': "Loomulik iive (sündide ja surmade vahe)",
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        }
    )
    
    plt.title(f'Loomulik iive maakonniti aastal {year}', fontsize=16)
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
    
    # Process the data
    df = process_data(df)
    
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
    
    # Prepare data for visualization
    merged_data = prepare_map_data(df, gdf, selected_year)
    
    # Display map
    st.subheader(f"Loomulik iive maakonniti aastal {selected_year}")
    fig = plot_map(merged_data, selected_year)
    st.pyplot(fig)
    
    # Display data table
    st.subheader("Andmed tabelina")
    
    # Get data for the selected year
    year_data = get_data_for_year(df, selected_year)
    
    # Check if we have gender information
    if 'Sugu' in year_data.columns:
        # Pivot the data to show males and females side by side
        try:
            pivot_data = year_data.pivot_table(
                index='Maakond', 
                columns='Sugu', 
                values='Loomulik iive',
                aggfunc='sum'
            ).reset_index()
            
            # Rename columns for clarity
            pivot_data.columns.name = None
            
            # Add total column
            county_totals = year_data.groupby('Maakond')['Loomulik iive'].sum().reset_index()
            pivot_data = pivot_data.merge(county_totals, on='Maakond')
            pivot_data = pivot_data.rename(columns={'Loomulik iive': 'Kokku'})
            
            # Sort by total natural growth
            pivot_data = pivot_data.sort_values('Kokku', ascending=False)
            
            # Display the table
            st.dataframe(pivot_data, use_container_width=True)
            
            # Add some statistics
            total_growth = pivot_data['Kokku'].sum()
            st.metric(
                label="Eesti loomulik iive kokku", 
                value=f"{total_growth:,.0f}".replace(',', ' '),
                delta=None
            )
        except Exception as e:
            st.error(f"Error creating pivot table: {e}")
            st.dataframe(year_data, use_container_width=True)
    else:
        # Just show the raw data for the year
        st.dataframe(year_data, use_container_width=True)
    
    # Add data source information
    st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()
