import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv
from world_map import show_world_timelapse_map
import glob

# ... (your existing imports)
from world_map import show_world_timelapse_map
from india_map import show_india_timelapse_map, load_geojson # ADD THIS LINE
import glob
import json # If not already imported
if "selected_pulse_india" not in st.session_state:
    st.session_state.selected_pulse_india = "Tur"

if "selected_season_india" not in st.session_state:
    st.session_state.selected_season_india = "Kharif"

if "selected_type" not in st.session_state:
    st.session_state.selected_type = "Area"

if "india_geojson" not in st.session_state:
    st.session_state.india_geojson = None

if "india_map_full_path" not in st.session_state:
    st.session_state.india_map_full_path = "path/to/your/data.csv"

# Page setup
st.set_page_config(layout="wide", page_title="India FoodCrop Dashboard", page_icon="🌾")

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}
.toggle-container {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 2.5rem 0 1rem;
}
.toggle-button {
    font-size: 2rem;
    padding: 1.2rem 3rem;
    border-radius: 12px;
    border: 2px solid #ccc;
    background-color: white;
    color: black;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
.toggle-button:hover {
    transform: scale(1.1);
    background-color: #f0f0f0;
}
.toggle-button.selected {
    background-color: black;
    color: white;
    transform: scale(1.2);
}
.sidebar-title {
    background-color: white;
    padding: 1rem;
    font-size: 1.3rem;
    font-weight: 700;
    border-radius: 15px;
    margin-bottom: 1rem;
    text-align: center;
    color: #111;
}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# ---------- TOGGLE BUTTONS ----------
st.markdown('<div class="toggle-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("Production", key="prod"):
        st.session_state.selected_type = "Production"
with col2:
    if st.button("Yield", key="yield"):
        st.session_state.selected_type = "Yield"
with col3:
    if st.button("Area", key="area"):
        st.session_state.selected_type = "Area"
st.markdown('</div>', unsafe_allow_html=True)

selected_type = st.session_state.selected_type
if not selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b>, <b>Yield</b>, or <b>Area</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()
# ---------- UNIT LOOKUP ----------
unit_lookup = {
    "Yield": {
        "Oilseeds": "Kg./hectare", "Pulses": "Kg./hectare", "Rice": "Kg./hectare", "Wheat": "Kg./hectare",
        "Coarse Cereals": "Kg./hectare", "Maize": "Kg./hectare", "Fruits": "MT/hectare", "Vegetables": "MT/hectare"
    },
    "Production": {
        "Milk": "Million Tonne", "Meat": "Million Tonne", "Eggs": "Million Numbers", "Sugar and Products": "Lakh Tonne",
        "Fruits": "'000 MT", "Vegetables": "'000 MT", "Foodgrains": "'000 Tonne", "Cereals": "'000 Tonne",
        "Pulses": "'000 Tonne", "Rice": "'000 Tonne", "Wheat": "'000 Tonne", "Coarse Cereals": "'000 Tonne", "Maize": "'000 Tonne"
    },
    "Area": {
        "Foodgrains": "Lakh hectare", "Cereals": "'000 hectare", "Fruits": "'000 hectare", "Oilseeds": "'000 hectare",
        "Pulses": "'000 hectare", "Rice": "'000 hectare", "Vegetables": "'000 hectare", "Wheat": "'000 hectare",
        "Coarse Cereals": "'000 hectare", "Maize": "'000 hectare"
    }
}
unit_conversion_map = {
    "'000 Tonne": {"Million Tonne": 0.001}, "'000 MT": {"Million Tonne": 0.001},
    "'000 hectare": {"Million hectare": 0.001}, "Lakh hectare": {"Million hectare": 0.1},
    "Million Numbers": {"Billion Numbers": 0.001}, "Kg./hectare": {"Tonne/hectare": 0.001}
}

# ---------- HEADER ----------
st.markdown(f"<h1 style='text-align:center;'>🌾 India FoodCrop Data Dashboard</h1>", unsafe_allow_html=True)

# ---------- PATH & PREFIX ----------
prefix_map = {"Production": "prod_", "Yield": "yield_", "Area": "area_"}
prefix = prefix_map[selected_type]
base_path = f"Data/{selected_type}"

# ---------- FOLDERS ----------
available_folders = [f.replace(prefix, "") for f in os.listdir(base_path) if f.startswith(prefix)]

# ---------- CATEGORY HIERARCHY ----------
category_hierarchy = {
    "Agriculture": {
        "Foodgrains": {
            "Cereals": ["Rice", "Wheat", "Cereals"],
            "Foodgrains": ["Foodgrains"],
            "Coarse Cereals": ["Maize", "Coarse Cereals"],
            "Pulses": ["Pulses"]
        },
        "Horticulture": {"Fruits": ["Fruits"], "Vegetables": ["Vegetables"]},
        "Oilseeds": {"Oilseeds": ["Oilseeds"]},
        "Commercial Crops": {"Sugar and Products": ["Sugar and Products"]}
    },
    "Allied Sectors": {
        "Animal Products": {
            "Eggs": ["Eggs"], "Milk": ["Milk"], "Meat": ["Meat"], "Marine and Inland Fish": ["Marine and Inland Fish"]
        }
    }
}

# ---------- SIDEBAR CATEGORY PICKER ----------
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)
    sector = st.selectbox("Main Sector", list(category_hierarchy.keys()))
    sub_sector = st.selectbox("Sub-Sector", list(category_hierarchy[sector].keys()))

    def normalize(name): return name.lower().replace(" ", "").replace("_", "")
    subcat_display_to_folder = {}
    norm_available = {normalize(f): f for f in available_folders}

    for subcat_list in category_hierarchy[sector][sub_sector].values():
        for subcat in subcat_list:
            norm_subcat = normalize(subcat)
            if norm_subcat in norm_available:
                subcat_display_to_folder[subcat] = norm_available[norm_subcat]

    if not subcat_display_to_folder:
        st.error("No data available for selected sub-sector.")
        st.stop()

    category = st.selectbox("Category", list(subcat_display_to_folder.keys()))
    folder_key = subcat_display_to_folder[category]
    folder_name = f"{prefix}{folder_key}"
    folder_path = os.path.join(base_path, folder_name)

# ---------- UNIT CONVERSION PICKER ----------
unit = unit_lookup.get(selected_type, {}).get(category, "")
conversion_options = unit_conversion_map.get(unit, {})
conversion_multiplier = 1.0
if conversion_options:
    chosen_unit = st.sidebar.selectbox("Convert Unit", ["Original"] + list(conversion_options.keys()))
    if chosen_unit != "Original":
        conversion_multiplier = conversion_options[chosen_unit]
        unit = chosen_unit
# ---------- SAFE READ ----------
def safe_read(filename):
    full_path = os.path.join(folder_path, filename)
    return pd.read_csv(full_path) if os.path.exists(full_path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
wg_df = safe_read("wg_report.csv")

# ---------- Apply conversion ----------
if historical_df is not None:
    historical_df["Total"] *= conversion_multiplier

if forecast_df is not None:
    forecast_df.iloc[:, 1:] *= conversion_multiplier

if wg_df is not None and not wg_df.empty:
    wg_df["Value"] *= conversion_multiplier

# ---------- LOGEST GROWTH ----------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, category, conversion_multiplier)
    st.pyplot(fig)

# ---------- FORECAST TIMELINE ----------
if historical_df is not None and forecast_df is not None:
    historical_df = historical_df.rename(columns={"Total": "Value"})
    historical_df["Model"] = "Historical"

    forecast_long_df = forecast_df.melt(id_vars="Year", var_name="Model", value_name="Value")
    forecast_years = sorted(forecast_df["Year"].unique())
    start_year = historical_df["Year"].min()
    end_year = max(forecast_years + [2047])

    timeline_frames = []
    for year in forecast_years:
        hist_temp = historical_df.copy()
        hist_temp["FrameYear"] = year

        forecast_temp = forecast_df[forecast_df["Year"] <= year].copy()
        forecast_temp = forecast_temp.melt(id_vars="Year", var_name="Model", value_name="Value")
        forecast_temp["FrameYear"] = year

        combined = pd.concat([hist_temp[["Year", "Model", "Value", "FrameYear"]],
                              forecast_temp[["Year", "Model", "Value", "FrameYear"]]])

        timeline_frames.append(combined)

    timeline_df = pd.concat(timeline_frames)

    # Axis bounds
    y_min = timeline_df["Value"].min() * 0.95
    y_max = timeline_df["Value"].max() * 1.05
    x_min = timeline_df["Year"].min() - 5
    x_max = 2050

    # Plot
    fig_timeline = px.line(
        timeline_df,
        x="Year",
        y="Value",
        color="Model",
        animation_frame="FrameYear",
        title=f"📊 Forecast Timeline ({unit})",
        markers=True,
        range_y=[y_min, y_max],
        range_x=[x_min, x_max]
    )

    # WG Scatter points
    if wg_df is not None and not wg_df.empty:
        fig_timeline.add_trace(go.Scatter(
            x=wg_df["Year"],
            y=wg_df["Value"],
            mode="markers+text",
            name="WG Report",
            marker=dict(color="red", size=10, symbol="circle"),
            text=wg_df["Scenario"],
            textposition="top center",
            showlegend=True
        ))

    fig_timeline.update_layout(
        yaxis_title=f"Forecast Value ({unit})",
        xaxis_title="Year",
        legend_title="Model"
    )

    st.plotly_chart(fig_timeline, use_container_width=True)
# ---------- WORLD MAP ----------
with st.sidebar:
    st.markdown("### 🌍 World View Map")
    base_world_path = os.path.join("world data", selected_type)
    file_list = glob.glob(os.path.join(base_world_path, "*.csv"))

    available_categories = {
        os.path.basename(f)
        .replace("prod_", "")
        .replace("yield_", "")
        .replace("area_", "")
        .replace("_country.csv", "")
        .replace("_", " ")
        .title(): f
        for f in file_list
    }

    selected_file = None
    selected_world_category = None
    if available_categories:
        selected_world_category = st.selectbox("World Map Category", list(available_categories.keys()))
        selected_file = available_categories[selected_world_category]

# ... (after the WORLD MAP sidebar section)
for feature in india_geojson["features"]:
    feature["properties"]["ST_NM"] = feature["properties"]["NAME_1"]

# ---------- INDIA MAP CONTROLS ----------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🇮🇳 India State-wise Map")

    if 'india_geojson' not in st.session_state:
        st.session_state.india_geojson = load_geojson()

    if st.session_state.india_geojson:
        st.session_state.india_map_food_crop = st.selectbox(
            "Select Food Crop (India Map)",
            ["Pulses"],
            key="india_map_food_crop"
        )

        pulse_options_india = [
            "Arhar", "Gram", "Moong", "Masoor", "Urad", "Moth",
            "Kulthi", "Khesari", "Total Pulses"
        ]
        st.session_state.selected_pulse_india = st.selectbox(
            "Select Pulse (India Map)",
            pulse_options_india,
            key="india_map_pulse"
        )

        season_options_india = ["Kharif", "Rabi", "Total Season"]
        st.session_state.selected_season_india = st.selectbox(
            "Select Season (India Map)",
            season_options_india,
            key="india_map_season"
        )

        india_map_data_path = f"India_Map_Data/{st.session_state.selected_type}"
        sanitized_pulse_name = selected_pulse_india.replace(" ", "_")
        st.session_state.india_map_file_name = f"{sanitized_pulse_name}_{selected_season_india}.csv"
        st.session_state.india_map_full_path = os.path.join(india_map_data_path, india_map_file_name)
    else:
        st.sidebar.error("Could not load GeoJSON for India map. Map functionality will be disabled.")
        st.session_state.india_map_full_path = None
# Ensure this is defined if GeoJSON fails to load

# ---------- MAIN WORLD RENDER ----------
if selected_file:
    df_world = pd.read_csv(selected_file)
    st.subheader(f"🌐 {selected_world_category} {selected_type} Over Time")
    show_world_timelapse_map(df_world, metric_title=f"{selected_world_category} {selected_type}")
elif selected_type:  # Only warn if type was selected but no files
    st.warning("No data files found for selected type.")

# ... (after your existing "MAIN WORLD RENDER" section or another suitable place)

# ---------- INDIA MAP RENDER ----------
st.markdown("---")
#st.subheader(f"🇮🇳 State-wise {selected_pulse_india} - {selected_season_india} ({st.session_state.selected_type})")

st.subheader(f"🇮🇳 State-wise {st.session_state.selected_pulse_india} - {st.session_state.selected_season_india} ({st.session_state.selected_type})")

#if st.session_state.india_geojson and st.session_state.india_map_full_path:
india_geojson = st.session_state.get("india_geojson")
india_map_full_path = st.session_state.get("india_map_full_path")
selected_pulse_india = st.session_state.get("selected_pulse_india")
selected_season_india = st.session_state.get("selected_season_india")
selected_type = st.session_state.get("selected_type")

if india_geojson and india_map_full_path and selected_pulse_india and selected_season_india and selected_type:
    st.subheader(f"🇮🇳 State-wise {selected_pulse_india} - {selected_season_india} ({selected_type})")

    if os.path.exists(india_map_full_path):
        df_india = pd.read_csv(india_map_full_path)
        required_cols = ["State", "Year", "Value"]

        if all(col in df_india.columns for col in required_cols):
            metric_display_title = f"{selected_pulse_india} - {selected_season_india} - {selected_type}"
            show_india_timelapse_map(df_india, india_geojson, metric_title=metric_display_title)
        else:
            st.error(f"Data file '{os.path.basename(india_map_full_path)}' is missing required columns: {required_cols}")
    else:
        st.error(f"File not found: {india_map_full_path}")
else:
    st.info("Please select all required options from the sidebar to view the India map.")

    if os.path.exists(st.session_state.india_map_full_path):
        try:
            df_india = pd.read_csv(st.session_state.india_map_full_path)
            required_cols = ["State", "Year", "Value"]  # No Unit anymore

            if all(col in df_india.columns for col in required_cols):
                metric_display_title = f"{st.session_state.selected_pulse_india} - {st.session_state.selected_season_india} - {st.session_state.selected_type}"
                show_india_timelapse_map(df_india, st.session_state.india_geojson, metric_title=metric_display_title)
            else:
                st.error(f"Data file '{st.session_state.india_map_file_name}' is missing one or more required columns: {required_cols}")
        except pd.errors.EmptyDataError:
            st.warning(f"The data file '{india_map_file_name}' is empty.")
        except Exception as e:
            st.error(f"Error loading or processing India map data from '{india_map_file_name}': {e}")
    else:
        st.warning(f"Data file not found for India map: {india_map_file_name} at path {india_map_full_path}")
'''elif not st.session_state.india_geojson:
    st.error("India map cannot be displayed because GeoJSON data failed to load.")
else:
    st.info("Select options in the sidebar to display the India map.")
if st.session_state.india_geojson and india_map_full_path:
    if os.path.exists(india_map_full_path):
        try:
            df_india = pd.read_csv(india_map_full_path)
            required_cols = ["State", "Year", "Value"]
            if all(col in df_india.columns for col in required_cols):
                metric_display_title = f"{selected_pulse_india} - {selected_season_india} - {st.session_state.selected_type}"
                show_india_timelapse_map(df_india, st.session_state.india_geojson, metric_title=metric_display_title)
            else:
                st.error(f"Data file '{india_map_file_name}' is missing one or more required columns: {required_cols}.")'''
