import streamlit as st
import pandas as pd
import serial
import time
import requests
import plotly.graph_objects as go
import math

from parser import parse_data
from twin import AtlasTwin
import storage
import config

# ---------- CONFIG ----------
PORT = config.SERIAL_PORT
BAUD = config.SERIAL_BAUD
API_KEY = config.API_KEY
CITY = config.CITY

st.set_page_config(page_title="Atlas Digital Twin", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top, #0f172a, #020617);
}

.glass {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(18px);
    padding: 15px;
    border-radius: 16px;
    margin-bottom: 12px;
}

.normal { border-left: 4px solid #22c55e; }
.warning { border-left: 4px solid #f59e0b; box-shadow: 0 0 20px rgba(245,158,11,0.3); }
.alert { border-left: 4px solid #ef4444; box-shadow: 0 0 30px rgba(239,68,68,0.5); }

.title { font-size: 20px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------- INIT ----------
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial(PORT, BAUD, timeout=0.1)
        time.sleep(2)
        st.session_state.ser.flushInput()
    except Exception as exc:
        st.session_state.ser = None
        st.warning(f"Serial connection unavailable: {exc}")

if "twin" not in st.session_state:
    st.session_state.twin = AtlasTwin()

if "latest" not in st.session_state:
    st.session_state.latest = {}

if "scenario_state" not in st.session_state:
    st.session_state.scenario_state = {
        "temp_offset": 0,
        "pressure_offset": 0,
        "aq_offset": 0
    }

ser = st.session_state.get("ser")

# ---------- WEATHER ----------
@st.cache_data(ttl=60)
def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        r = requests.get(url).json()
        return {
            "temp": r["main"]["temp"],
            "pressure": r["main"]["pressure"],
            "lat": r["coord"]["lat"],
            "lon": r["coord"]["lon"]
        }
    except:
        return None

weather = get_weather()

# ---------- SCENARIO ----------
scenario = st.selectbox("🌍 Scenario", ["None","Heatwave","Storm","Pollution Spike"])
st.caption("Applies gradual environmental perturbations to test system response.")

def evolve(state, scenario):
    t = time.time()
    if scenario == "Heatwave":
        state["temp_offset"] += 0.2 + 0.05 * math.sin(t)
        state["aq_offset"] += 1
    elif scenario == "Storm":
        state["pressure_offset"] -= 0.8 + 0.2 * math.sin(t)
        state["temp_offset"] += 0.1 * math.sin(t)
    elif scenario == "Pollution Spike":
        state["aq_offset"] += 8
        state["temp_offset"] += 0.05
    else:
        for k in state:
            state[k] *= 0.9
    return state

# ---------- PIPELINE ----------
if ser is not None and ser.in_waiting:
    line = ser.readline().decode(errors="ignore").strip()

    if line.startswith("DATA:"):
        parsed = parse_data(line[5:])

        if parsed:
            st.session_state.scenario_state = evolve(
                st.session_state.scenario_state, scenario
            )

            s = st.session_state.scenario_state

            sim = parsed.copy()
            sim["temp"] = sim.get("temp", 0) + s["temp_offset"]
            sim["pressure"] = sim.get("pressure", 0) + s["pressure_offset"]
            sim["aq"] = sim.get("aq", 0) + s["aq_offset"]

            result = st.session_state.twin.update(sim)

            result["sim_temp"] = sim["temp"]

            if weather:
                result["api_temp"] = weather["temp"]
                result["api_pressure"] = weather["pressure"]

            storage.insert(result)
            st.session_state.latest = result

data = st.session_state.latest

# ---------- STATE ----------
def get_state(data, weather):
    if not data or not weather:
        return "NORMAL"
    deviation = abs(data["sim_temp"] - weather["temp"])
    if deviation > 5:
        return "ALERT"
    elif deviation > 2:
        return "WARNING"
    return "NORMAL"

state = get_state(data, weather)
panel_class = "normal" if state=="NORMAL" else "warning" if state=="WARNING" else "alert"

# ---------- INTELLIGENCE ----------
def detect_microclimate(data, weather):
    if not data or not weather:
        return None
    diff = weather["temp"] - data["sim_temp"]
    if diff > 5:
        return "Indoor Cooling (Possible AC)"
    elif diff > 2:
        return "Localized Cool Zone"
    return None

def environment_summary(data):
    if not data:
        return "No data"
    if data["sim_temp"] > 35:
        return "High temperature conditions"
    elif data["sim_temp"] < 20:
        return "Cool environment"
    if data["pressure"] < 1000:
        return "Low pressure system forming"
    if data["aq"] > 500:
        return "Poor air quality detected"
    return "Stable environmental conditions"

def predictive_insight(data, weather):
    if not data or not weather:
        return None
    if data["sim_temp"] > 32:
        return "Possible heat escalation trend"
    if data["pressure"] < 1000:
        return "Possible storm conditions forming"
    return None

# ---------- HEADER ----------
st.title("🌍 Atlas — Digital Twin Intelligence System")

# ---------- INSIGHTS ----------
if data and weather:
    deviation = data["sim_temp"] - weather["temp"]

    if state == "ALERT":
        st.error(f"🚨 High anomaly ({deviation:.2f}°C)")
    elif state == "WARNING":
        st.warning(f"⚠️ Moderate deviation ({deviation:.2f}°C)")
    else:
        st.success("✅ System stable")

    micro = detect_microclimate(data, weather)
    if micro:
        st.info(f"🧊 Microclimate: {micro}")

    insight = predictive_insight(data, weather)
    if insight:
        st.info(f"🔮 Insight: {insight}")

    st.caption(f"🌍 {environment_summary(data)}")

# ---------- GAUGES ----------
def gauge(v, title, minv, maxv):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v,
        title={'text': title},
        gauge={'axis': {'range': [minv, maxv]}}
    ))
    fig.update_layout(template="plotly_dark", height=200)
    return fig

if data and weather:
    c1,c2,c3,c4 = st.columns(4)
    c1.plotly_chart(gauge(data["sim_temp"], "Sim Temp", 0, 50))
    c2.plotly_chart(gauge(weather["temp"], "API Temp", 0, 50))
    c3.plotly_chart(gauge(data["pressure"], "Pressure", 900, 1100))
    c4.plotly_chart(gauge(data["aq"], "Air Quality", 0, 1000))

# ---------- DATA ----------
rows = storage.fetch_recent(200)
df = None

if rows:
    df = pd.DataFrame(rows, columns=["time","temp","comp_temp","pressure","aq"])
    df = df[::-1]

    df["temp_smooth"] = df["temp"].rolling(10, min_periods=1).mean()
    df["pressure_smooth"] = df["pressure"].rolling(10, min_periods=1).mean()
    df["aq_smooth"] = df["aq"].rolling(10, min_periods=1).mean()

    if weather:
        df["api_temp"] = weather["temp"]
        df["api_pressure"] = weather["pressure"]

# ---------- PANELS ----------
if df is not None:

    tab1, tab2, tab3 = st.tabs(["🌡 Temp","🌧 Pressure","🌫 AQ"])

    with tab1:
        st.markdown(f"<div class='glass {panel_class}'>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=df["temp"], mode="markers", name="Sim"))
        fig.add_trace(go.Scatter(y=df["comp_temp"], mode="markers", name="Corrected"))
        fig.add_trace(go.Scatter(y=df["temp_smooth"], mode="markers", name="Smooth"))
        fig.add_trace(go.Scatter(y=df.get("api_temp", df["temp"]), mode="markers", name="API"))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown(f"<div class='glass {panel_class}'>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=df["pressure"], mode="markers", name="Sensor"))
        fig.add_trace(go.Scatter(y=df["pressure_smooth"], mode="markers", name="Smooth"))
        fig.add_trace(go.Scatter(y=df.get("api_pressure", df["pressure"]), mode="markers", name="API"))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown(f"<div class='glass {panel_class}'>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=df["aq"], mode="markers", name="Sensor"))
        fig.add_trace(go.Scatter(y=df["aq_smooth"], mode="markers", name="Smooth"))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- MAP ----------
if weather:
    st.subheader("🗺️ Geo Context")
    st.map(pd.DataFrame({"lat":[weather["lat"]],"lon":[weather["lon"]]}))

# ---------- REFRESH ----------
time.sleep(1)
st.rerun()