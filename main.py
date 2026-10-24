from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

APP_NAME = "GeoPilot AI"
APP_VERSION = "1.1.0"

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"
HTTP_TIMEOUT = 15

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Outdoor planning using weather and air-quality forecasts. "
        "Scores are prototype heuristics, not medical advice."
    ),
)


class RecommendationRequest(BaseModel):
    activity: str = Field(min_length=2, max_length=50)
    location: str = Field(min_length=2, max_length=150)
    radius_km: float = Field(default=5.0, gt=0, le=100)
    time_range: str = Field(
        default="tomorrow morning", min_length=2, max_length=80
    )
    age: Optional[int] = Field(default=None, ge=1, le=120)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("activity")
    @classmethod
    def clean_activity(cls, value):
        value = value.strip().lower()
        allowed = {
            "jogging", "running", "cycling", "golf", "cricket",
            "football", "outdoor football", "tennis", "hiking",
            "nature walk", "picnic", "park outing", "outdoor event",
            "gathering", "photography", "outdoor photography",
        }
        if value not in allowed:
            raise ValueError(
                "Unsupported activity. Choose jogging, cycling, golf, "
                "cricket, football, tennis, hiking, nature walk, picnic, "
                "outdoor event, or photography."
            )
        return value

    @field_validator("location")
    @classmethod
    def clean_location(cls, value):
        return value.strip()

    @field_validator("time_range")
    @classmethod
    def clean_time_range(cls, value):
        return value.strip().lower()

    @field_validator("constraints")
    @classmethod
    def clean_constraints(cls, values):
        return [v.strip() for v in values if v and v.strip()]


def get_json(url, params):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "GeoPilotAI/1.1"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"An external data source could not be reached: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="An external data source returned invalid JSON.",
        ) from exc


def geocode_location(location):
    data = get_json(
        GEOCODING_URL,
        {
            "name": location,
            "count": 10,
            "language": "en",
            "format": "json",
        },
    )

    results = data.get("results", [])

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No location was found for '{location}'. "
                "Add city, state, and country."
            ),
        )

    candidates = results

    if "india" in location.lower() or "odisha" in location.lower():
        india = [
            item for item in results
            if item.get("country_code", "").upper() == "IN"
        ]
        if india:
            candidates = india

    exact = [
        item for item in candidates
        if item.get("name", "").lower() == location.lower()
    ]

    item = exact[0] if exact else candidates[0]

    return {
        "name": item.get("name"),
        "admin1": item.get("admin1"),
        "country": item.get("country"),
        "country_code": item.get("country_code"),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "timezone": item.get("timezone", "auto"),
    }


def get_weather(lat, lon):
    return get_json(
        WEATHER_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "forecast_days": 7,
            "current": (
                "temperature_2m,relative_humidity_2m,"
                "apparent_temperature,precipitation,weather_code,"
                "wind_speed_10m,wind_direction_10m"
            ),
            "hourly": (
                "temperature_2m,precipitation_probability,"
                "precipitation,wind_speed_10m,wind_direction_10m,"
                "weather_code"
            ),
        },
    )


def get_air_quality(lat, lon):
    try:
        response = requests.get(
            AIR_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "timezone": "auto",
                "forecast_days": 5,
                "hourly": "us_aqi,pm2_5",
            },
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "GeoPilotAI/1.1"},
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def local_now(tz_name):
    try:
        return datetime.now(ZoneInfo(tz_name))
    except (ZoneInfoNotFoundError, ValueError):
        return datetime.now().astimezone()


def get_requested_window(phrase, tz_name):
    now = local_now(tz_name)
    phrase = phrase.lower().strip()

    if phrase in {"next 24 hours", "next 24h", "24 hours"}:
        start = now.replace(minute=0, second=0, microsecond=0)
        return start, start + timedelta(hours=24), "Next 24 hours"

    if "weekend" in phrase:
        days = (5 - now.weekday()) % 7

        if days == 0 and now.hour >= 18:
            days = 7

        target_date = (now + timedelta(days=days)).date()
        start = datetime.combine(
            target_date,
            datetime.min.time(),
            tzinfo=now.tzinfo,
        )
        return start, start + timedelta(days=2), "This weekend"

    if phrase.startswith("tomorrow"):
        target_date = now.date() + timedelta(days=1)
    elif phrase.startswith("today") or phrase.startswith("this "):
        target_date = now.date()
    else:
        target_date = now.date() + timedelta(days=1)

    if "morning" in phrase:
        start_hour, end_hour = 6, 12
        label = "Morning (06:00-12:00)"
    elif "afternoon" in phrase:
        start_hour, end_hour = 12, 17
        label = "Afternoon (12:00-17:00)"
    elif "evening" in phrase or "night" in phrase:
        start_hour, end_hour = 17, 22
        label = "Evening (17:00-22:00)"
    else:
        start_hour, end_hour = 0, 24
        label = "Full day"

    start = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo=now.tzinfo,
    ).replace(hour=start_hour)

    if end_hour == 24:
        end = datetime.combine(
            target_date + timedelta(days=1),
            datetime.min.time(),
            tzinfo=now.tzinfo,
        )
    else:
        end = start.replace(hour=end_hour)

    if target_date == now.date() and start < now:
        start = now.replace(minute=0, second=0, microsecond=0)

    return start, end, label


def parse_times(weather):
    try:
        timezone = ZoneInfo(weather.get("timezone", "UTC"))
    except (ZoneInfoNotFoundError, ValueError):
        timezone = datetime.now().astimezone().tzinfo

    result = []

    for time_text in weather.get("hourly", {}).get("time", []):
        try:
            result.append(
                datetime.fromisoformat(time_text).replace(tzinfo=timezone)
            )
        except (ValueError, TypeError):
            result.append(None)

    return result


def val(data, key, index):
    if index is None:
        return None

    array = data.get(key, [])
    return array[index] if index < len(array) else None


def num(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def weather_description(code):
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }

    try:
        return descriptions.get(int(code), "Weather condition not classified")
    except (TypeError, ValueError):
        return "Weather condition not available"


def assess_air(aqi, pm25, sensitive):
    if aqi is None and pm25 is None:
        return {
            "status": "unknown",
            "outdoor_exertion_advised": None,
            "message": (
                "Air-quality data is unavailable, so pollution suitability "
                "cannot be assessed."
            ),
        }

    if (
        (aqi is not None and aqi > 150)
        or (pm25 is not None and pm25 > 55.4)
    ):
        return {
            "status": "strong_caution",
            "outdoor_exertion_advised": False,
            "message": (
                "Forecast air pollution is high. Consider moving strenuous "
                "activity indoors and check local official guidance."
            ),
        }

    if sensitive and (
        (aqi is not None and aqi > 100)
        or (pm25 is not None and pm25 > 35.4)
    ):
        return {
            "status": "sensitive_group_caution",
            "outdoor_exertion_advised": False,
            "message": (
                "Given the stated sensitivity and forecast pollution, "
                "consider an indoor alternative or reducing outdoor exertion."
            ),
        }

    if aqi is not None and aqi > 100:
        return {
            "status": "sensitive_group_caution",
            "outdoor_exertion_advised": None,
            "message": (
                "Forecast AQI may affect sensitive groups. Consider reducing "
                "strenuous activity and check local guidance."
            ),
        }

    if pm25 is not None and pm25 > 35.4:
        return {
            "status": "pm25_caution",
            "outdoor_exertion_advised": None,
            "message": (
                "PM2.5 is elevated. Check local air-quality guidance "
                "before outdoor exertion."
            ),
        }

    return {
        "status": "no_high_pollution_flag_from_available_values",
        "outdoor_exertion_advised": None,
        "message": (
            "No high-pollution flag was triggered by available values. "
            "This is not a guarantee of safety."
        ),
    }


def calculate_score(
    activity, temp, rain_prob, rain_mm, wind, aqi, pm25, sensitive
):
    score = 80.0
    reasons = []
    risks = []

    if temp is not None:
        if temp < 5:
            score -= 15
            risks.append("Cold conditions may require extra layers.")
        elif temp <= 25:
            score += 5
            reasons.append(
                "Temperature is within a broadly comfortable range."
            )
        elif temp <= 32:
            score -= 8
            risks.append(
                "Warm conditions: consider hydration and heat exposure."
            )
        else:
            score -= 20
            risks.append("High temperature may increase heat stress.")

    if rain_prob is not None:
        if rain_prob >= 70:
            score -= 25
            risks.append("High forecast probability of precipitation.")
        elif rain_prob >= 40:
            score -= 12
            risks.append(
                "Some chance of rain; check conditions before leaving."
            )
        elif rain_prob <= 15:
            score += 5
            reasons.append(
                "Low forecast probability of precipitation."
            )

    if rain_mm is not None and rain_mm >= 2:
        score -= 10
        risks.append(
            "Forecast precipitation may affect outdoor conditions."
        )

    if wind is not None:
        if wind >= 40:
            score -= 25
            risks.append(
                "Very windy conditions may be disruptive."
            )
        elif wind >= 25:
            score -= 12
            risks.append(
                "Wind may affect comfort or activity performance."
            )
        elif wind <= 15:
            score += 3
            reasons.append("Wind speed is relatively low.")

    if aqi is None:
        risks.append(
            "Air-quality data is unavailable; pollution conditions are unknown."
        )
    elif aqi > 300:
        score -= 65
        risks.append(
            "Very high US AQI forecast; avoid strenuous outdoor activity."
        )
    elif aqi > 200:
        score -= 55
        risks.append(
            "Very unhealthy US AQI forecast; avoid outdoor exertion."
        )
    elif aqi > 150:
        score -= 45
        risks.append(
            "US AQI forecast is in the unhealthy range; "
            "consider avoiding outdoor exertion."
        )
    elif aqi > 100:
        score -= 30
        risks.append(
            "US AQI forecast is unhealthy for sensitive groups."
        )
    elif aqi > 50:
        score -= 12
        risks.append(
            "Air quality may be a concern for sensitive individuals."
        )
    else:
        score += 5
        reasons.append("US AQI forecast is in the good range.")

    if pm25 is None:
        risks.append("PM2.5 forecast is unavailable.")
    elif pm25 > 55.4:
        score -= 25
        risks.append("Very elevated PM2.5 is forecast.")
    elif pm25 > 35.4:
        score -= 18
        risks.append("Elevated PM2.5 is forecast.")
    elif pm25 > 12:
        score -= 7
        risks.append("PM2.5 is above the lowest concentration band.")

    if sensitive and (aqi is None or pm25 is None):
        score -= 8
        risks.append(
            "Air-quality data is incomplete despite stated pollution "
            "sensitivity; treat uncertainty cautiously."
        )
    elif sensitive and (
        (aqi is not None and aqi > 100)
        or (pm25 is not None and pm25 > 35.4)
    ):
        score -= 20
        risks.append(
            "Additional penalty applied for stated sensitivity to air pollution."
        )

    if "cycling" in activity and wind is not None and wind >= 25:
        score -= 5
        risks.append("Wind can make cycling more difficult.")

    if (
        "photography" in activity
        and rain_prob is not None
        and rain_prob >= 50
    ):
        risks.append(
            "Rain may affect outdoor photography equipment and access."
        )

    if (
        "picnic" in activity
        and rain_prob is not None
        and rain_prob >= 40
    ):
        risks.append("Rain may make a picnic less comfortable.")

    if not reasons:
        reasons.append(
            "Score is based on the available forecast variables."
        )

    return max(0, min(100, round(score))), reasons, risks


def ask_ollama(evidence):
    prompt = (
        "You explain GeoPilot AI forecast results. Use only the JSON evidence. "
        "Do not invent data or claim an activity is medically safe. "
        "Respect the air-quality advisory; if it says avoid outdoor exertion, "
        "do not recommend outdoor exertion. Explain the highest-ranked hour, "
        "risks and limitations in 3-5 concise sentences.\n\nEVIDENCE:\n"
        + str(evidence)
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip() or None
    except (requests.RequestException, ValueError):
        return None


@app.get("/")
def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "message": "GeoPilot AI API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    models = []
    status = "unavailable"

    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=3,
        )
        response.raise_for_status()
        models = [
            item.get("name")
            for item in response.json().get("models", [])
            if item.get("name")
        ]

        status = (
            "available"
            if OLLAMA_MODEL in models
            or any(name.startswith(OLLAMA_MODEL + ":") for name in models)
            else "reachable_model_not_listed"
        )
    except (requests.RequestException, ValueError):
        pass

    return {
        "status": "ok",
        "application": APP_NAME,
        "version": APP_VERSION,
        "ollama_status": status,
        "configured_model": OLLAMA_MODEL,
        "available_models": models,
        "data_sources": {
            "geocoding": "Open-Meteo Geocoding API",
            "weather": "Open-Meteo Forecast API",
            "air_quality": (
                "Open-Meteo Air Quality API (optional if unavailable)"
            ),
            "osm_features": "Not implemented in this API version",
        },
    }


@app.post("/recommend")
def recommend(request: RecommendationRequest):
    place = geocode_location(request.location)
    lat = place["latitude"]
    lon = place["longitude"]

    weather = get_weather(lat, lon)
    hourly = weather.get("hourly", {})
    times = parse_times(weather)

    if not times:
        raise HTTPException(
            status_code=502,
            detail="Weather source returned no usable hourly forecast times.",
        )

    air = get_air_quality(lat, lon)
    air_hourly = (air or {}).get("hourly", {})
    air_indices = {
        time_text: index
        for index, time_text in enumerate(air_hourly.get("time", []))
    }

    timezone_name = weather.get("timezone", place.get("timezone", "UTC"))
    start, end, label = get_requested_window(
        request.time_range, timezone_name
    )

    sensitive = any(
        "sensitive to air pollution" in constraint.lower()
        for constraint in request.constraints
    )

    rows = []

    for index, forecast_time in enumerate(times):
        if forecast_time is None or forecast_time < start or forecast_time >= end:
            continue

        time_key = forecast_time.strftime("%Y-%m-%dT%H:%M")
        air_index = air_indices.get(time_key)

        temperature = num(val(hourly, "temperature_2m", index))
        rain_probability = num(
            val(hourly, "precipitation_probability", index)
        )
        rain_mm = num(val(hourly, "precipitation", index))
        wind = num(val(hourly, "wind_speed_10m", index))
        wind_direction = num(
            val(hourly, "wind_direction_10m", index)
        )
        weather_code = val(hourly, "weather_code", index)

        aqi = num(val(air_hourly, "us_aqi", air_index))
        pm25 = num(val(air_hourly, "pm2_5", air_index))

        score, reasons, risks = calculate_score(
            request.activity,
            temperature,
            rain_probability,
            rain_mm,
            wind,
            aqi,
            pm25,
            sensitive,
        )

        advisory = assess_air(aqi, pm25, sensitive)

        rows.append(
            {
                "time": forecast_time.isoformat(),
                "score": score,
                "temperature_c": temperature,
                "precipitation_probability_percent": rain_probability,
                "precipitation_mm": rain_mm,
                "wind_speed_kmh": wind,
                "wind_direction_degrees": wind_direction,
                "weather": weather_description(weather_code),
                "us_aqi": aqi,
                "pm2_5_ug_m3": pm25,
                "reasons": reasons,
                "risks": risks,
                "air_quality_advisory": advisory,
            }
        )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No forecast hours were available for '{request.time_range}'. "
                "Try another time range."
            ),
        )

    rows.sort(key=lambda row: (-row["score"], row["time"]))
    top = rows[:5]
    best = top[0]
    advisory = best["air_quality_advisory"]

    evidence = {
        "activity": request.activity,
        "location": place,
        "requested_time_range": request.time_range,
        "interpreted_time_range": label,
        "highest_scoring_forecast_hour": best,
        "air_quality_advisory": advisory,
        "top_forecast_options": top[:3],
        "personal_constraints": request.constraints,
        "limitations": [
            "Prototype heuristic, not validated health or safety advice.",
            "Radius is accepted but nearby venues are not searched.",
            "Roads, traffic, green cover, water bodies, and industrial "
            "proximity are not analyzed.",
            "Air-quality data may be unavailable.",
        ],
    }

    explanation = ask_ollama(evidence)

    fallback = (
        f"The highest-scoring available forecast hour is {best['time']} "
        f"with a prototype score of {best['score']}/100. "
        f"Forecast condition: {best['weather']}. "
        f"Air-quality advisory: {advisory['message']} "
        "Scores are heuristics, not guarantees of safety."
    )

    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "request": request.model_dump(),
        "location": place,
        "coordinates": {
            "latitude": lat,
            "longitude": lon,
        },
        "timezone": timezone_name,
        "time_range": {
            "requested": request.time_range,
            "interpreted_as": label,
            "start_local": start.isoformat(),
            "end_local_exclusive": end.isoformat(),
        },
        "best_recommendation": best,
        "recommendation_status": advisory,
        "alternatives": top[1:],
        "forecast_hours_evaluated": len(rows),
        "explanation": explanation or fallback,
        "llm_status": "used" if explanation else "fallback_used",
        "data_sources": [
            {
                "name": "Open-Meteo Geocoding API",
                "url": "https://geocoding-api.open-meteo.com/",
                "used_for": (
                    "Resolving the requested location to coordinates"
                ),
            },
            {
                "name": "Open-Meteo Forecast API",
                "url": "https://open-meteo.com/",
                "used_for": "Hourly weather forecast",
            },
            {
                "name": "Open-Meteo Air Quality API",
                "url": "https://open-meteo.com/en/docs/air-quality-api",
                "used_for": (
                    "Hourly US AQI and PM2.5 when available"
                ),
            },
        ],
        "limitations": [
            "Suitability scores are prototype heuristics, not validated "
            "medical or safety advice.",
            "The radius is accepted but nearby venues are not searched "
            "in this API version.",
            "Road networks, traffic, green cover, water bodies, and "
            "industrial proximity are not analyzed in this API version.",
            "Air-quality forecasts may be unavailable for some locations "
            "or hours.",
            "Forecasts can change; check authoritative local conditions "
            "before going outdoors.",
        ],
    }