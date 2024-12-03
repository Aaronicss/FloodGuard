import requests
import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import plotly.express as px


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FloodGuard",
    page_icon="🌊",
)

st.title("Welcome to Flood Guard")
st.image("FloodGuard/logo.png",width=500)

# --- USER AUTHENTICATION ---
names = ["Aaron Lazaro", "Gabriel"]
usernames = ["ronron", "gabby"]

# Load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

# Initialize authenticator
authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "flood_prediction",  # Cookie name
    "abcdef",  # Cookie key (used for encryption)
    cookie_expiry_days=30
)

# Login
name, authenticator_status, username = authenticator.login("Login", "main")

# Handle login status
if authenticator_status is False:
    st.error("Username/password is incorrect")

elif authenticator_status is None:
    st.warning("Please enter your username and password")

elif authenticator_status is True:
    def load_model():
        with open('saved_steps.pkl', 'rb') as file:
            data = pickle.load(file)
        return data


    data = load_model()

    regressor = data["model"]


    def show_predict_page():
        st.write("""### We need some information to predict the probability of flooding""")

        MonsoonIntensity = st.slider("Monsoon Intensity", 0, 16, 2, key="Monsoon_Intensity_key")
        TopographyDrainage = st.slider("Topography Drainage", 0, 16, 2, key="Topography_Drainage_key")
        Urbanization = st.slider("Urbanization", 0, 16, 2, key="Urbanization_key")
        CoastalVulnerability = st.slider("Coastal Vulnerability", 0, 16, 2, key="Coastal_Vulnerability_key")
        Landslides = st.slider("Landslides", 0, 16, 2, key="Landslides_key")

        ok = st.button("Calculate Probability")
        if ok:
            X = np.array([[MonsoonIntensity, TopographyDrainage, Urbanization, CoastalVulnerability, Landslides]])

            probability = regressor.predict(X)
            global value
            value = probability[0] * 100
            global text
            text = (f"The probability of flooding is {probability[0] * 100:.0f}%")


    def get_coordinates(city_name):
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {"User-Agent": "WeatherDashboardApp/1.0 (contact@example.com)"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            location_data = response.json()
            if location_data:
                location = location_data[0]
                return float(location['lat']), float(location['lon'])
            else:
                st.warning("City not found. Try adding the country name (e.g., 'Paris, France').")
                return None, None
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None, None

    def get_weather_data(lat, lon, hours):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&forecast_days=2"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to retrieve weather data.")
            return None

    st.sidebar.write("You are logged in.")

    # Logout button
    if "flood_prediction" in authenticator.cookie_manager.cookies:
        authenticator.logout("Logout", "sidebar")
    else:
        st.sidebar.warning("Logout unavailable (cookie not found). Refresh the page")


    st.title("Flood Probability Prediction Model")
    row1_1, row1_2 = st.columns((3, 3))

    with row1_1:
        show_predict_page()

    with row1_2:

        try:
            st.header("Result Interpretation")
            if value > 50:
                st.header(text)
                st.warning("High Probability of Flooding")
                st.subheader("Move to higher ground")
                st.write("Avoid standing in, swimming in, or driving through flood water. If you're in a vehicle that's filling with water, get onto the roof. If you're trapped in a building, go to the highest level, but don't go into an enclosed space like a loft or attic.")
                st.subheader("Evacuate")
                st.write("If you're told to evacuate, do so.")
                st.subheader("Stay informed")
                st.write("Stay informed of local flood warnings, especially if you live in a flood-prone area.")
                st.subheader("Prepare an emergency kit")
                st.write("Stock an emergency kit with water, nonperishable food, a first-aid kit, flashlights, and extra batteries.")

            elif value < 50:
                st.header(text)
                st.success("Low Probability of Flooding")
                st.write("No recommendation")
        except Exception:
            pass

    st.header("Bacoor City")
    city_name = "Bacoor City"
    forecast_duration = st.slider("Select forecast duration (hours)", min_value=12, max_value=48, value=24, step=12)
    parameter_options = st.multiselect(
        "Choose weather parameters to display:",
        options=["Temperature (°C)", "Humidity (%)", "Wind Speed (m/s)"],
        default=["Temperature (°C)", "Humidity (%)"]
    )

    if st.button("Get Weather Data"):
        lat, lon = get_coordinates(city_name)
        if lat and lon:
            data = get_weather_data(lat, lon, forecast_duration)
            if data:
                times = [datetime.now() + timedelta(hours=i) for i in range(forecast_duration)]
                df = pd.DataFrame({"Time": times})

                if "Temperature (°C)" in parameter_options:
                    df["Temperature (°C)"] = data['hourly']['temperature_2m'][:forecast_duration]
                    st.subheader(f"Temperature Forecast")
                    st.line_chart(df.set_index("Time")["Temperature (°C)"])

                if "Humidity (%)" in parameter_options:
                    df["Humidity (%)"] = data['hourly']['relative_humidity_2m'][:forecast_duration]
                    st.subheader(f"Humidity Forecast")
                    st.line_chart(df.set_index("Time")["Humidity (%)"])

                if "Wind Speed (m/s)" in parameter_options:
                    df["Wind Speed (m/s)"] = data['hourly']['wind_speed_10m'][:forecast_duration]
                    st.subheader(f"Wind Speed Forecast")
                    st.line_chart(df.set_index("Time")["Wind Speed (m/s)"])

        st.subheader("Current Weather Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Temperature", f"{data['hourly']['temperature_2m'][0]}°C")
        col2.metric("💧 Humidity", f"{data['hourly']['relative_humidity_2m'][0]}%")
        col3.metric("🌬️ Wind Speed", f"{data['hourly']['wind_speed_10m'][0]} m/s")



    # Load GeoJSON file
    geojson_path = "barangays-municity-ph042103000.0.1.json"
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)


    features = geojson_data['features']
    properties = [feature['properties'] for feature in features]
    barangays = [prop['ADM4_EN'] for prop in properties]
    flood_path = "2024-12-03T11-38_export.csv"
    data = pd.read_csv(flood_path)  # Automatically handles headers

    # Plotly Choropleth Map
    fig = px.choropleth_mapbox(
        data,
        geojson=geojson_data,
        featureidkey="properties.ADM4_EN",  # Key in GeoJSON for matching
        locations="Barangay",  # Column in data for matching
        color="Flood Probability",  # Data column to color by
        color_continuous_scale="Bluered",
        mapbox_style="carto-positron",
        center={"lat": 14.45, "lon": 120.94},  # Adjust center to your area
        zoom=12
    )
    st.plotly_chart(fig)


