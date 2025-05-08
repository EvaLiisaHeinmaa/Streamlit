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

def get_data_for_year(df, year):
    if df is not None:
        year_data = df[df.Aasta == year]
        return year_data
    return None

def create_plot(gdf, data_year, selected_year):
    if gdf is None or data_year is None:
        return None
    
    # --- Debugging: Print columns before merging (already there) ---
    st.write("Columns in GeoDataFrame (gdf):", gdf.columns.tolist())
    st.write("Columns in Year Data (data_year):", data_year.columns.tolist())
    # --- End Debugging ---
    
    # --- Debugging: Print unique values in merge columns ---
    if 'Maakond' in data_year.columns:
        st.write("Unique 'Maakond' values in data_year:", data_year['Maakond'].unique())
    else:
        st.warning("'Maakond' column not found in data_year.")
        
    if 'MNIMI' in gdf.columns:
        st.write("Unique 'MNIMI' values in gdf:", gdf['MNIMI'].unique())
    else:
         st.warning("'MNIMI' column not found in gdf.")
         
    # Check for a potential county code column in gdf (e.g., 'MKOOD')
    # You might need to change 'MKOOD' to the actual column name in your geojson
    geojson_code_column = None
    for col in gdf.columns:
        # Look for columns that might contain county codes (e.g., 'MKOOD', 'code', 'id')
        if 'kod' in col.lower() or 'code' in col.lower() or 'id' in col.lower():
             st.write(f"Found potential code column in gdf: '{col}'")
             st.write(f"Unique values in '{col}':", gdf[col].unique())
             geojson_code_column = col # Assume the first one found is the correct one for now
             break # Stop after finding one potential code column
             
    # --- End Debugging ---
    
    # Determine the correct column to merge on in the GeoJSON
    # Prioritize merging on a code column if it exists and matches the data's 'Maakond' codes
    merge_left_on = 'MNIMI' # Default to name
    if geojson_code_column:
         # Check if the values look like the codes from the API data (e.g., '39', '44')
         # This is a heuristic check, you might need to adjust it
         sample_values = gdf[geojson_code_column].dropna().astype(str).unique()[:5]
         st.write(f"Sample values from potential geojson code column '{geojson_code_column}': {sample_values}")
         
         # Simple check: are sample values numeric strings and relatively short?
         if all(v.isdigit() and len(v) <= 3 for v in sample_values):
              st.info(f"Using geojson column '{geojson_code_column}' for merging based on sample values.")
              merge_left_on = geojson_code_column
         else:
              st.warning(f"Values in potential geojson code column '{geojson_code_column}' don't look like API codes. Sticking with 'MNIMI' for merge.")


    # Perform the merge
    # Ensure 'Maakond' is treated as string in data_year for consistent merging with potential string codes in geojson
    if 'Maakond' in data_year.columns:
        data_year['Maakond'] = data_year['Maakond'].astype(str)
        
    st.write(f"Attempting merge: left_on='{merge_left_on}', right_on='Maakond'")
    merged_data = gdf.merge(data_year, left_on=merge_left_on, right_on='Maakond', how='left')
    
    # --- Debugging: Print column names after merging (already there) ---
    st.write("Columns in Merged Data:", merged_data.columns.tolist())
    # --- End Debugging ---
    
    # Check if 'Loomulik iive' exists in merged_data
    # --- Debugging: Check for the value column ---
    value_column_name = None
    # Look for a column that is likely the value column (numeric, not Aasta, Maakond, Sugu, geometry)
    potential_value_cols = [col for col in merged_data.columns if merged_data[col].dtype in ['int64', 'float64'] and col not in ['Aasta', 'Sugu']]
    
    st.write("Potential value columns in merged data:", potential_value_cols)
    
    # Assuming the value column is one of these potential columns
    # You might need to manually identify the correct one based on the printout
    # Let's assume the first potential numeric column that isn't Aasta/Sugu is the one
    if potential_value_cols:
        value_column_name = potential_value_cols[0]
        st.info(f"Assuming '{value_column_name}' is the value column for plotting.")
    else:
        st.error("Could not identify a numeric value column for plotting in the merged data.")
        return None
    # --- End Debugging ---


    if value_column_name not in merged_data.columns:
        st.error(f"The column '{value_column_name}' (identified as value column) is not present in the merged data.")
        st.write("Please check the merge operation and column names.")
        return None
        
    # Also check if the assumed value column is all NaNs after merge (indicates merge failure)
    if merged_data[value_column_name].isnull().all():
         st.warning(f"The value column '{value_column_name}' contains only missing values after the merge. This might indicate a problem with the merge keys or the data.")
         st.dataframe(merged_data[['Maakond', merge_left_on, value_column_name]].head()) # Show sample merge results


    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Use the identified value_column_name for plotting
    merged_data.plot(column=value_column_name, 
                     ax=ax,
                     legend=True,
                     cmap='viridis',
                     legend_kwds={'label': "Loomulik iive"}) # Keep the label as is for now
    
    plt.title(f'Loomulik iive maakonniti aastal {selected_year}')
    plt.axis('off')
    plt.tight_layout()
    
    return fig

# Main app flow
df = import_data()
gdf = import_geojson()

if df is not None and gdf is not None:
    # Display some basic info about the data
    st.subheader("Data Overview")
    st.write(f"Data contains years from {df['Aasta'].min()} to {df['Aasta'].max()}")
    
    # Show GeoJSON info
    st.write(f"Geographic data loaded with {len(gdf)} counties")
    
    # Year selection
    years = sorted(df['Aasta'].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)  # Default to latest year
    
    # Get data for selected year
    data_year = get_data_for_year(df, selected_year)
    
    # Create and display the plot
    fig = create_plot(gdf, data_year, selected_year)
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
