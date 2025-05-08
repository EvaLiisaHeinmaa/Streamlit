import streamlit as st
import json
import geopandas as gpd
import matplotlib.pyplot as plt
from io import StringIO

# Set page configuration
st.set_page_config(
    page_title="Estonian County Map",
    page_icon="🇪🇪",
    layout="wide"
)

# Simplified GeoJSON for Estonian counties
counties_geojson = """
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"MNIMI": "Harju maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[24.5, 59.5], [24.5, 59.0], [24.0, 59.0], [24.0, 59.5], [24.5, 59.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Hiiu maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[22.5, 59.0], [22.5, 58.7], [22.0, 58.7], [22.0, 59.0], [22.5, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Ida-Viru maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[27.5, 59.5], [27.5, 59.0], [27.0, 59.0], [27.0, 59.5], [27.5, 59.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Jõgeva maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[26.5, 59.0], [26.5, 58.5], [26.0, 58.5], [26.0, 59.0], [26.5, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Järva maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[25.5, 59.0], [25.5, 58.5], [25.0, 58.5], [25.0, 59.0], [25.5, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Lääne maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[23.5, 59.0], [23.5, 58.5], [23.0, 58.5], [23.0, 59.0], [23.5, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Lääne-Viru maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[26.0, 59.5], [26.0, 59.0], [25.5, 59.0], [25.5, 59.5], [26.0, 59.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Põlva maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[27.0, 58.5], [27.0, 58.0], [26.5, 58.0], [26.5, 58.5], [27.0, 58.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Pärnu maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[24.5, 58.5], [24.5, 58.0], [24.0, 58.0], [24.0, 58.5], [24.5, 58.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Rapla maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[24.5, 59.0], [24.5, 58.5], [24.0, 58.5], [24.0, 59.0], [24.5, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Saare maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[23.0, 58.5], [23.0, 58.0], [22.0, 58.0], [22.0, 58.5], [23.0, 58.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Tartu maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[27.0, 59.0], [27.0, 58.5], [26.5, 58.5], [26.5, 59.0], [27.0, 59.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Valga maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[26.5, 58.0], [26.5, 57.5], [26.0, 57.5], [26.0, 58.0], [26.5, 58.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Viljandi maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[25.5, 58.5], [25.5, 58.0], [25.0, 58.0], [25.0, 58.5], [25.5, 58.5]]]
      }
    },
    {
      "type": "Feature",
      "properties": {"MNIMI": "Võru maakond"},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[27.5, 58.0], [27.5, 57.5], [27.0, 57.5], [27.0, 58.0], [27.5, 58.0]]]
      }
    }
  ]
}
"""

def display_map():
    """Display a simple map of Estonian counties"""
    # Parse the GeoJSON string
    geojson_data = json.loads(counties_geojson)
    
    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Plot the map
    gdf.plot(
        ax=ax,
        edgecolor='black',
        facecolor='lightblue',
        linewidth=0.5
    )
    
    # Add county names
    for idx, row in gdf.iterrows():
        # Get the centroid of each county polygon
        centroid = row.geometry.centroid
        # Add the county name at the centroid
        ax.text(centroid.x, centroid.y, row['MNIMI'], 
                fontsize=8, ha='center', va='center')
    
    plt.title('Eesti maakonnad', fontsize=16)
    plt.axis('off')  # Hide axis
    plt.tight_layout()
    
    return fig

# Main app
def main():
    st.title("Eesti Maakonnad")
    st.write("Simplified map of Estonian counties")
    
    # Display map
    fig = display_map()
    st.pyplot(fig)

if __name__ == "__main__":
    main()
