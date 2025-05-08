import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json

# Set page configuration
st.set_page_config(
    page_title="Estonian Counties Map",
    page_icon="🇪🇪",
    layout="wide"
)

# Estonia counties GeoJSON URL from a reliable source
ESTONIA_COUNTIES_URL = "https://raw.githubusercontent.com/okestonia/Estonian-Open-Geodata/master/geojson/maakond.geojson"

def get_estonia_counties_geojson():
    """Fetch Estonia counties GeoJSON from GitHub"""
    try:
        response = requests.get(ESTONIA_COUNTIES_URL)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch GeoJSON: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching GeoJSON: {e}")
        return None

def display_estonia_counties_map():
    # Get the GeoJSON data
    counties_geojson = get_estonia_counties_geojson()
    
    if not counties_geojson:
        st.error("Could not load Estonia counties data")
        return None
    
    # Create a map centered on Estonia
    m = folium.Map(location=[58.5953, 25.0136], zoom_start=7, tiles='CartoDB positron')
    
    # Add the counties layer
    folium.GeoJson(
        counties_geojson,
        name='Estonia Counties',
        style_function=lambda feature: {
            'fillColor': '#3186cc',
            'color': 'black',
            'weight': 2,
            'dashArray': '5, 5',
            'fillOpacity': 0.4,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['MNIMI'],
            aliases=['County:'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# Main app
def main():
    st.title("Eesti Maakonnad (Estonian Counties)")
    st.write("Interactive map showing all Estonian counties")
    
    # Display the map
    map_obj = display_estonia_counties_map()
    if map_obj:
        folium_static(map_obj, width=1000, height=600)

if __name__ == "__main__":
    main()
