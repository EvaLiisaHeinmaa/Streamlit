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
                
                # Debug: Show raw response
                with st.expander("Debug: Raw API Response"):
                    st.text(text[:1000] + "..." if len(text) > 1000 else text)
                
                # Try to parse the CSV
                try:
                    df = pd.read_csv(StringIO(text), sep=',')
                    
                    # Debug: Show dataframe info
                    with st.expander("Debug: DataFrame Info"):
                        st.write(f"Shape: {df.shape}")
                        st.write("Columns:", df.columns.tolist())
                        st.write("First few rows:")
                        st.dataframe(df.head())
                    
                    # Check if we have actual data or just headers
                    if df.shape[0] == 0 or (df.shape[0] == 1 and df.iloc[0].isna().all()):
                        st.warning("The API returned headers but no data rows.")
                        
                        # Try alternative approach - maybe semicolon separator
                        try:
                            df = pd.read_csv(StringIO(text), sep=';')
                            st.success("Successfully parsed data with semicolon separator!")
                        except Exception as e:
                            st.error(f"Alternative parsing also failed: {e}")
                    
                    return df
                
                except Exception as e:
                    st.error(f"Error parsing CSV data: {e}")
                    return pd.DataFrame()
            else:
                st.error(f"Failed with status code: {response.status_code}")
                st.text(response.text)
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Request error: {e}")
            return pd.DataFrame()

# For testing/development - create sample data if API fails
def create_sample_data():
    st.warning("Using SAMPLE DATA for development/testing!")
    
    counties = [
        'Harju maakond', 'Hiiu maakond', 'Ida-Viru maakond', 'Jõgeva maakond',
        'Järva maakond', 'Lääne maakond', 'Lääne-Viru maakond', 'Põlva maakond',
        'Pärnu maakond', 'Rapla maakond', 'Saare maakond', 'Tartu maakond',
        'Valga maakond', 'Viljandi maakond'
    ]
    
    years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    genders = ['Mehed', 'Naised']
    
    # Create sample data
    data = []
    for year in years:
        for county in counties:
            for gender in genders:
                # Generate some realistic-looking data
                # Harju and Tartu positive, others negative
                if county in ['Harju maakond', 'Tartu maakond']:
                    value = np.random.randint(50, 300)
                else:
                    value = np.random.randint(-200, -10)
                
                data.append({
                    'Aasta': year,
                    'Maakond': county,
                    'Sugu': gender,
                    'Loomulik iive': value
                })
    
    return pd.DataFrame(data)

@st.cache_data
def import_geojson():
    try:
        gdf = gpd.read_file(geojson)
        return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def get_data_for_year(df, year):
    year_data = df[df.Aasta == year]
    return year_data

def prepare_map_data(df, gdf, year):
    # Filter data for the selected year
    year_data = get_data_for_year(df, year)
    
    # Aggregate data by county (sum for both genders)
    county_data = year_data.groupby('Maakond')['Loomulik iive'].sum().reset_index()
    
    # Merge with geodata
    merged_data = gdf.merge(county_data, left_on='MNIMI', right_on='Maakond')
    
    return merged_data

def plot_map(merged_data, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Create the choropleth map
    merged_data.plot(
        column='Loomulik iive', 
        ax=ax,
        legend=True,
        cmap='RdYlGn',  # Red-Yellow-Green colormap (negative values in red, positive in green)
        edgecolor='black',
        linewidth=0.5,
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
        
        # If API data is empty or has issues, use sample data for development/testing
        if df.empty or 'Loomulik iive' not in df.columns:
            df = create_sample_data()
        
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
    
    # Prepare data for visualization
    merged_data = prepare_map_data(df, gdf, selected_year)
    
    # Display map
    st.subheader(f"Loomulik iive maakonniti aastal {selected_year}")
    fig = plot_map(merged_data, selected_year)
    st.pyplot(fig)
    
    # Display data table
    st.subheader("Andmed tabelina")
    
    # Get data for the selected year and reshape it for better display
    year_data = get_data_for_year(df, selected_year)
    
    # Pivot the data to show males and females side by side
    pivot_data = year_data.pivot_table(
        index='Maakond', 
        columns='Sugu', 
        values='Loomulik iive'
    ).reset_index()
    
    # Rename columns for clarity
    pivot_data.columns.name = None
    
    # Check if we have the expected column names
    if 'Mehed' in pivot_data.columns and 'Naised' in pivot_data.columns:
        pivot_data = pivot_data.rename(columns={
            'Mehed': 'Mehed (loomulik iive)',
            'Naised': 'Naised (loomulik iive)'
        })
    
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
        value=f"{total_growth:,}".replace(',', ' '),
        delta=None
    )
    
    # Add data source information
    if 'sample_data' in locals() and sample_data:
        st.caption("Andmeallikas: NÄIDISANDMED (mitte päris andmed)")
    else:
        st.caption("Andmeallikas: Statistikaamet (RV032)")

if __name__ == "__main__":
    main()
