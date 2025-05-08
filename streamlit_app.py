
import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# Set page title
st.title("Estonian Population Statistics")

# Constants - exactly as in your original code
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

# Function to import data from Statistics Estonia
def import_data():
    headers = {
        'Content-Type': 'application/json'
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    
    with st.spinner("Fetching data from Statistics Estonia..."):
        response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        st.success("Data successfully fetched!")
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        st.text(response.text)
        return pd.DataFrame()

# Function to get data for year
def get_data_for_year(df, year):
    year_data = df[df.Aasta==year]
    return year_data

# Function to create plot
def plot(df, gdf, year):
    if df.empty or gdf is None:
        st.error("Cannot create plot: missing data or GeoJSON")
        return None
    
    # Get data for the selected year
    year_data = get_data_for_year(df, year)
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Try to find a meaningful column to plot
    if 'Loomulik iive' in year_data.columns:
        # Group by county to get one value per county
        county_data = year_data.groupby('Maakond')['Loomulik iive'].sum().reset_index()
        
        # Create a mapping dictionary for county codes to names
        county_mapping = {
            "39": "Hiiu maakond",
            "44": "Ida-Viru maakond",
            "49": "Jõgeva maakond",
            "51": "Järva maakond",
            "57": "Lääne maakond",
            "59": "Lääne-Viru maakond",
            "65": "Põlva maakond",
            "67": "Pärnu maakond",
            "70": "Rapla maakond",
            "74": "Saare maakond",
            "78": "Tartu maakond",
            "82": "Valga maakond",
            "84": "Viljandi maakond",
            "86": "Võru maakond"
        }
        
        # Try to find the county name column in the GeoJSON
        county_col = None
        for col in gdf.columns:
            if col.lower() in ['maakond', 'county', 'name', 'mnimi', 'maakonna_nimi']:
                county_col = col
                break
        
        if county_col:
            # Create a copy of the GeoJSON for merging
            merged_gdf = gdf.copy()
            
            # Add county names to our data
            county_data['CountyName'] = county_data['Maakond'].map(county_mapping)
            
            # Display county names for debugging
            st.write("County mapping:")
            st.dataframe(county_data[['Maakond', 'CountyName']])
            
            # Display GeoJSON county names for debugging
            st.write(f"GeoJSON county names (column: {county_col}):")
            st.dataframe(gdf[county_col])
            
            # Try to merge with GeoJSON
            try:
                # Standardize county names for joining
                merged_gdf['MergeKey'] = merged_gdf[county_col].str.lower().str.strip()
                county_data['MergeKey'] = county_data['CountyName'].str.lower().str.strip()
                
                # Join the data
                merged_gdf = merged_gdf.merge(county_data, on='MergeKey', how='left')
                
                # Plot with data
                merged_gdf.plot(
                    column='Loomulik iive',
                    ax=ax,
                    legend=True,
                    cmap='viridis',
                    edgecolor='black',
                    legend_kwds={'label': "Loomulik iive"}
                )
                
                plt.title(f'Loomulik iive maakonniti aastal {year}')
            except Exception as e:
                st.error(f"Error merging data: {str(e)}")
                # Fall back to basic map
                gdf.plot(ax=ax, color='lightblue', edgecolor='black')
                plt.title(f'Estonian Counties {year}')
        else:
            # Fall back to basic map
            gdf.plot(ax=ax, color='lightblue', edgecolor='black')
            plt.title(f'Estonian Counties {year}')
    else:
        # Just plot the GeoJSON without data
        gdf.plot(ax=ax, color='lightblue', edgecolor='black')
        plt.title(f'Estonian Counties {year}')
    
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Sidebar for year selection
st.sidebar.header("Controls")
selected_year = st.sidebar.selectbox(
    "Select Year",
    ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
)

# File uploader for GeoJSON
uploaded_file = st.sidebar.file_uploader("Upload GeoJSON file", type=['geojson', 'json'])

# Load GeoJSON from uploaded file
gdf = None
if uploaded_file is not None:
    try:
        gdf = gpd.read_file(uploaded_file)
        st.sidebar.success("GeoJSON file loaded successfully!")
        
        # Show GeoJSON info
        st.sidebar.write(f"GeoJSON contains {len(gdf)} features")
        st.sidebar.write(f"Columns: {', '.join(gdf.columns)}")
    except Exception as e:
        st.sidebar.error(f"Error loading GeoJSON: {str(e)}")

# Load data from API
if st.sidebar.button("Load Data from API"):
    df = import_data()
    
    # Store in session state
    st.session_state.df = df
elif 'df' in st.session_state:
    df = st.session_state.df
else:
    df = pd.DataFrame()
    st.warning("Click 'Load Data from API' to fetch data")

# Show data table
st.write("## Data Table")
if not df.empty:
    year_data = get_data_for_year(df, selected_year)
    st.dataframe(year_data)
    
    # Show data info
    st.write(f"Data shape: {year_data.shape}")
    st.write(f"Columns: {', '.join(year_data.columns)}")
else:
    st.write("No data available. Please click 'Load Data from API'.")

# Show map
st.write("## Map")
if gdf is not None:
    if not df.empty:
        fig = plot(df, gdf, selected_year)
        if fig:
            st.pyplot(fig)
    else:
        # Just show the basic map without data
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        gdf.plot(ax=ax, color='lightblue', edgecolor='black')
        plt.title('Estonian Counties')
        plt.axis('off')
        plt.tight_layout()
        st.pyplot(fig)
        st.info("Map shown without data. Load data to see statistics.")
else:
    st.info("Please upload a GeoJSON file to display the map.")

# Add debugging info section
with st.expander("Debug Information"):
    st.write("### Session State")
    st.write(st.session_state)
    
    st.write("### GeoJSON Information")
    if gdf is not None:
        st.write(f"GeoJSON CRS: {gdf.crs}")
        st.write(f"GeoJSON Bounds: {gdf.total_bounds}")
        st.write("GeoJSON Sample:")
        st.dataframe(gdf.head(2))
    
    st.write("### Data Information")
    if not df.empty:
        st.write(f"Data Types: {df.dtypes}")
        st.write("Data Sample:")
        st.dataframe(df.head(5))


df = import_data()
merged_data = gdf.merge(df, left_on='MNIMI', right_on='Maakond') 
merged_data["Loomulik iive"] = merged_data["Mehed Loomulik iive"] + merged_data["Naised Loomulik iive"]
plot(get_data_for_year(merged_data, 2017))
