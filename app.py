
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="GeoPilot AI | Outdoor Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.hero {
    padding: 1.5rem 1.7rem;
    border-radius: 18px;
    background: linear-gradient(120deg, #102a43, #155e75);
    color: white;
    margin-bottom: 1.4rem;
}
.hero h1 {color: white; margin-bottom: .35rem;}
.hero p {color: #d9edf5; margin-bottom: 0;}
.section-label {
    color: #0e7490;
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .12em;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="section-label">GEOSPATIAL DECISION SUPPORT</div>
  <h1>🌍 GeoPilot AI</h1>
  <p>Plan outdoor activities with hourly weather and air-quality intelligence.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Your activity")
    st.caption("Tell GeoPilot what you are planning.")

    activity = st.selectbox(
        "Activity",
        [
            "jogging",
            "running",
            "cycling",
            "golf",
            "cricket",
            "outdoor football",
            "tennis",
            "hiking",
            "nature walk",
            "picnic",
            "outdoor event",
            "photography",
        ],
    )

    location = st.text_input(
        "City or location",
        value="Bhubaneswar, Odisha, India",
        help="Enter a place name that can be resolved by the geocoding service.",
    )

    radius_km = st.slider(
        "Preferred radius (km)",
        min_value=1,
        max_value=50,
        value=5,
    )

    time_range = st.selectbox(
        "When do you want to go?",
        [
            "this afternoon",
            "tomorrow morning",
            "tomorrow afternoon",
            "tomorrow evening",
            "this weekend",
            "next 24 hours",
        ],
        index=1,
    )

    age = st.number_input(
        "Age (optional context)",
        min_value=1,
        max_value=110,
        value=22,
    )

    constraints = st.multiselect(
        "Additional considerations",
        [
            "sensitive to air pollution",
            "prefer cooler temperatures",
            "avoid rain",
            "prefer low wind",
        ],
        default=["sensitive to air pollution"],
    )

    submitted = st.button(
        "Analyse conditions",
        type="primary",
        use_container_width=True,
    )

st.markdown("### Activity conditions")
st.write(
    "Choose your preferences in the sidebar, then request an analysis. "
    "Recommendations depend on the forecast available from the connected API."
)

if "result" not in st.session_state:
    st.session_state.result = None

if submitted:
    if not location.strip():
        st.error("Please enter a location.")
    else:
        payload = {
            "activity": activity,
            "location": location.strip(),
            "radius_km": radius_km,
            "time_range": time_range,
            "age": int(age) if age else None,
            "constraints": constraints,
        }

        try:
            with st.spinner(
                "Resolving location and evaluating hourly weather and air quality..."
            ):
                response = requests.post(
                    f"{API_URL}/recommend",
                    json=payload,
                    timeout=90,
                )

            if response.ok:
                st.session_state.result = response.json()
            else:
                st.session_state.result = None
                st.error(f"API returned HTTP {response.status_code}")
                st.code(response.text[:5000])

        except requests.exceptions.ConnectionError:
            st.session_state.result = None
            st.error(
                "Cannot reach the GeoPilot API. Make sure the Uvicorn server "
                "is running at http://127.0.0.1:8000."
            )
        except requests.exceptions.Timeout:
            st.session_state.result = None
            st.error(
                "The API took too long to respond. Check the Uvicorn terminal "
                "for errors and try again."
            )
        except ValueError as exc:
            st.session_state.result = None
            st.error(f"The API returned an unexpected response: {exc}")
        except requests.exceptions.RequestException as exc:
            st.session_state.result = None
            st.error(f"Request failed: {exc}")

data = st.session_state.result

if data:
    place = data.get("location") or {}
    best = data.get("best_recommendation") or {}
    alternatives = data.get("alternatives") or []
    window = data.get("time_range") or {}

    st.divider()
    st.markdown("### Analysis overview")

    st.write(
        f"**Location:** {place.get('name', location if 'location' in locals() else 'Requested location')}, "
        f"{place.get('admin1', '')}, {place.get('country', '')}"
    )
    st.write(
        f"**Requested period:** {window.get('interpreted_as', window.get('requested', 'Not provided'))}"
    )

    if best:
        st.markdown("### Highest-ranked time slot")

        # The score is a prototype ranking, not a safety rating.
        score = best.get("score")
        time_value = best.get("time")
        try:
            display_time = datetime.fromisoformat(time_value).strftime(
                "%a, %d %b · %I:%M %p"
            ) if time_value else "Not provided"
        except (ValueError, TypeError):
            display_time = str(time_value or "Not provided")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Suggested time", display_time)
        c2.metric(
            "Temperature",
            f"{best['temperature_c']} °C"
            if best.get("temperature_c") is not None else "Unavailable",
        )
        c3.metric(
            "US AQI",
            str(best["us_aqi"]) if best.get("us_aqi") is not None else "Unavailable",
        )
        c4.metric(
            "Prototype score",
            str(score) if score is not None else "Unavailable",
        )

        aqi = best.get("us_aqi")
        pm25 = best.get("pm2_5_ug_m3")

        if aqi is not None and aqi >= 101:
            st.warning(
                f"The forecast US AQI is {aqi}. This is an air-quality concern, "
                "particularly for sensitive groups. Consider reducing strenuous "
                "outdoor activity or choosing an indoor alternative."
            )

        if pm25 is not None and pm25 >= 35:
            st.warning(
                f"Forecast PM2.5 is {pm25} µg/m³. Check current local air-quality "
                "guidance before deciding to exercise outdoors."
            )

        st.caption(
            "A higher prototype score does not mean an activity is medically "
            "safe. Forecasts can change and are not a substitute for local guidance."
        )

        st.markdown("#### Weather details")
        details = {
            "Weather": best.get("weather"),
            "Precipitation probability (%)": best.get(
                "precipitation_probability_percent"
            ),
            "Precipitation (mm)": best.get("precipitation_mm"),
            "Wind speed (km/h)": best.get("wind_speed_kmh"),
            "Wind direction (degrees)": best.get("wind_direction_degrees"),
            "PM2.5 (µg/m³)": pm25,
        }
        st.dataframe(
            pd.DataFrame(
                [{"Measure": key, "Forecast": value if value is not None else "Unavailable"}
                 for key, value in details.items()]
            ),
            use_container_width=True,
            hide_index=True,
        )

        if best.get("reasons"):
            st.markdown("#### Why this time was ranked highest")
            for reason in best["reasons"]:
                st.write(f"• {reason}")

        if best.get("risks"):
            st.markdown("#### Risks and precautions")
            for risk in best["risks"]:
                st.write(f"• {risk}")

    if alternatives:
        st.markdown("### Other evaluated time slots")

        rows = []
        for item in alternatives:
            raw_time = item.get("time")
            try:
                formatted_time = datetime.fromisoformat(raw_time).strftime(
                    "%a, %d %b · %I:%M %p"
                ) if raw_time else "Not provided"
            except (ValueError, TypeError):
                formatted_time = str(raw_time or "Not provided")

            rows.append({
                "Time": formatted_time,
                "Score": item.get("score"),
                "Temperature (°C)": item.get("temperature_c"),
                "US AQI": item.get("us_aqi"),
                "PM2.5 (µg/m³)": item.get("pm2_5_ug_m3"),
                "Rain probability (%)": item.get(
                    "precipitation_probability_percent"
                ),
                "Wind (km/h)": item.get("wind_speed_kmh"),
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    if data.get("explanation"):
        st.markdown("### AI-generated explanation")
        st.write(data["explanation"])
        st.caption(
            "AI-generated text may contain errors. Verify numerical values "
            "against the structured forecast and source data above."
        )

    st.markdown("### Data sources")
    for source in data.get("data_sources", []):
        name = source.get("name", "Data source")
        url = source.get("url")
        used_for = source.get("used_for", "")
        if url:
            st.markdown(f"- [{name}]({url}) — {used_for}")
        else:
            st.write(f"- {name} — {used_for}")

    st.markdown("### Current prototype limitations")
    for limitation in data.get("limitations", []):
        st.write(f"• {limitation}")

    with st.expander("Technical details"):
        st.write("Application:", data.get("application"))
        st.write("Forecast hours evaluated:", data.get("forecast_hours_evaluated"))
        st.write("LLM status:", data.get("llm_status"))
        st.write("Coordinates:", data.get("coordinates"))
        st.write("Timezone:", data.get("timezone"))
        st.json(data.get("request", {}))

else:
    st.info(
        "Your results will appear here after you click **Analyse conditions**."
    )

st.divider()
st.caption(
    "GeoPilot AI · Prototype for geospatially informed outdoor planning · "
    "Weather and air-quality forecasts are uncertain. "
    "Nearby venues, roads, traffic, vegetation and industrial proximity "
    "are not yet analysed by the current backend."
)
