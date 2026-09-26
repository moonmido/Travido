import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


@tool
def get_current_weather(
    latitude: float,
    longitude: float
) -> dict:
    """
    Get the current weather for a location.

    Args:
        latitude: Location latitude.
        longitude: Location longitude.

    Returns:
        Current temperature, feels-like temperature, humidity,
        weather condition, wind and visibility.
    """

    if not OPENWEATHER_API_KEY:
        return {
            "success": False,
            "error": "OPENWEATHER_API_KEY is not configured."
        }

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "en"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})

        return {
            "success": True,
            "location": data.get("name"),

            "temperature_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),

            "humidity_percent": main.get("humidity"),
            "pressure_hpa": main.get("pressure"),

            "condition": weather.get("main"),
            "description": weather.get("description"),

            "wind_speed_mps": wind.get("speed"),
            "wind_direction_deg": wind.get("deg"),

            "visibility_m": data.get("visibility"),

            "sunrise": data.get("sys", {}).get("sunrise"),
            "sunset": data.get("sys", {}).get("sunset"),

            "timestamp": data.get("dt")
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool
def get_weather_forecast(
    latitude: float,
    longitude: float
) -> dict:
    """
    Get the 5-day weather forecast with 3-hour intervals.

    Args:
        latitude: Location latitude.
        longitude: Location longitude.

    Returns:
        Forecast information for the location.
    """

    if not OPENWEATHER_API_KEY:
        return {
            "success": False,
            "error": "OPENWEATHER_API_KEY is not configured."
        }

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "en"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        forecasts = []

        for item in data.get("list", []):

            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            wind = item.get("wind", {})

            forecasts.append({
                "datetime": item.get("dt_txt"),

                "temperature_c": main.get("temp"),
                "feels_like_c": main.get("feels_like"),

                "temperature_min_c": main.get("temp_min"),
                "temperature_max_c": main.get("temp_max"),

                "humidity_percent": main.get("humidity"),

                "condition": weather.get("main"),
                "description": weather.get("description"),

                "wind_speed_mps": wind.get("speed"),

                "clouds_percent": item.get(
                    "clouds", {}
                ).get("all"),

                "rain_3h_mm": item.get(
                    "rain", {}
                ).get("3h", 0),

                "snow_3h_mm": item.get(
                    "snow", {}
                ).get("3h", 0)
            })

        return {
            "success": True,
            "location": data.get("city", {}).get("name"),
            "country": data.get("city", {}).get("country"),
            "forecasts": forecasts
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }