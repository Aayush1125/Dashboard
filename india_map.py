import streamlit as st
import plotly.express as px
import pandas as pd
import json
import requests

def show_india_timelapse_map(df, geojson_data, metric_title="Value"):
    """
    Generates and displays an animated choropleth map of India.

    Args:
        df (pd.DataFrame): DataFrame with columns 'State', 'Year', 'Value'.
        geojson_data (dict): GeoJSON data for Indian states.
        metric_title (str): Title for the metric being displayed (e.g., "Production").
    """
    if df.empty:
        st.warning("No data available for the selected criteria to display on the India map.")
        return

    title = f"{metric_title} Over Time in India"

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.sort_values(by='Year')

    fig = px.choropleth(
        df,
        geojson=geojson_data,
        locations="State",
        featureidkey="properties.NAME_1",
        color="Value",
        hover_name="State",
        animation_frame="Year",
        color_continuous_scale="YlOrRd",
        title=title,
        scope="asia",
    )

    fig.update_geos(
        visible=False,
        fitbounds="locations",
        center={"lat": 20.5937, "lon": 78.9629},
        projection_scale=5
    )

    fig.update_layout(
        coloraxis_colorbar=dict(title="Value"),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

def load_geojson():
    geojson_url = "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson"
    try:
        response = requests.get(geojson_url)
        response.raise_for_status()
        geojson_data = response.json()
        if not geojson_data or 'features' not in geojson_data or not geojson_data['features']:
            st.error("GeoJSON data is invalid or empty.")
            return None
        if 'properties' not in geojson_data['features'][0] or 'ST_NM' not in geojson_data['features'][0]['properties']:
            st.error("GeoJSON features do not contain the expected 'ST_NM' property. Please check the GeoJSON source.")
            return None
        return geojson_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching GeoJSON: {e}")
        return None
    except json.JSONDecodeError:
        st.error("Error decoding GeoJSON data. The file might be corrupted or not in valid JSON format.")
