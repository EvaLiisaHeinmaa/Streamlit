import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import os

st.title("Estonian Population Natural Growth by County")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"  # Path to your local geojson file

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

        # --- Debugging: Print columns of the raw data ---
        st.write("Columns in raw data (df):", df.columns.tolist())
        # --- End Debugging ---
        
        return df
    else:
        st.error(f"Failed to retrieve data: {response.status_code}")
        st.write(response.text)
        return None

@st.cache_data
def import_geojson():
    try:
        # Check if file exists
        if not os.path.exists(GEOJSON_FILE):
            st.error(f"GeoJSON file not found: {GEOJSON_FILE}")
            st.info("Make sure the file is in the same directory as your Streamlit app.")
            return None
        
        with st.spinner('Loading geographic data...'):
            gdf = gpd.read_file(GEOJSON_FILE)
            
            # --- Debugging: Print columns of the GeoJSON data ---
            st.write("Columns in GeoJSON (gdf):", gdf.columns.tolist())
            # --- End Debugging ---
            
            return gdf
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def calculate_natural_growth(df):
    # --- Debugging: Check if 'Mehed Loomulik iive' and 'Naised Loomulik iive' exist ---
    if 'Mehed Loomulik iive' not in df.columns or 'Naised Loomulik iive' not in df.columns:
        st.error("Required columns ('Mehed Loomulik iive' or 'Naised Loomulik iive') are missing for natural growth calculation.")
        st.write("Available columns:", df.columns.tolist())
        return None

    # --- End Debugging ---
    
    # Filter for the 'Total' sex (Sugu == 1)
    df_total = df[df['Sugu'] == 1].copy()  # Use .copy() to avoid SettingWithCopyWarning
    
    # Calculate the total natural growth
    df_total.loc[:, "Loomulik iive"] = df_total["Mehed Loomulik iive"] + df_total["Naised Loomulik iive"]
    
    return df_total

def get_data_for_year(df, year):
    if df is not None:
        year_data = df[df.Aasta == year]
        return year_data
    return None

def create_plot(gdf, merged_data, selected_year): # Changed: Pass merged_data directly
    if gdf is None or merged_data is None:
        return None
    
    # --- Debugging: Print columns of the merged data ---
    st.write("Columns in Merged Data:", merged_data.columns.tolist())
    # --- End Debugging ---

    # Check if 'Loomulik iive' exists in merged_data
    if 'Loomulik iive' not in merged_data.columns:
        st.error("The column 'Loomulik iive' is not present in the merged data.")
        st.write("Please check the merge operation and column names.")
        return None
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    merged_data.plot(column='Loomulik iive', 
                     ax=ax,
                     legend=True,
                     cmap='viridis',
                     legend_kwds={'label': "Loomulik iive"})
    
    plt.title(f'Loomulik iive maakonniti aastal {selected_year}')
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Main app flow
df = import_data()
gdf = import_geojson()

if df is not None and gdf is not None:
    # Calculate natural growth
    df_with_growth = calculate_natural_growth(df)
    
    if df_with_growth is None:
        st.error("Failed to calculate natural growth.  Cannot proceed.")
        st.stop()  # Stop execution if calculation fails

    # Display some basic info about the data
    st.subheader("Data Overview")
    st.write(f"Data contains years from {df_with_growth['Aasta'].min()} to {df_with_growth['Aasta'].max()}")
    
    # Show GeoJSON info
    st.write(f"Geographic data loaded with {len(gdf)} counties")
    
    # Year selection
    years = sorted(df_with_growth['Aasta'].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)  # Default to latest year
    
    # Get data for selected year
    data_year = get_data_for_year(df_with_growth, selected_year)

    # Merge the data with the geodataframe
    merged_data = gdf.merge(data_year, left_on='MNIMI', right_on='Maakond', how='left')

    # Create and display the plot
    fig = create_plot(gdf, merged_data, selected_year) # Changed: Pass merged_data
    if fig:
        st.pyplot(fig)
    else:
        st.warning("Unable to create plot with the current data.")
    
    # Show the data for the selected year
    with st.expander("View Data Table"):
        st.dataframe(data_year)
    
    # Add download button for the selected year's data
    csv = data_year.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=f"population_growth_{selected_year}.csv",
        mime="text/csv"
    )
else:
    st.warning("Please make sure all data files are available before proceeding.")
    
    # Debug information
    if gdf is None:
        st.info(f"Current working directory: {os.getcwd()}")
        st.info(f"Files in directory: {os.listdir('.')}")
