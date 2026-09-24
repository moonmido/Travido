import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

ORS_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")


@tool
def calculate_route(
    origin_longitude: float,
    origin_latitude: float,
    destination_longitude: float,
    destination_latitude: float,
    profile: str = "driving-car"
) -> dict:
    """
    Calculate a route between two coordinates using OpenRouteService.

    Profiles:
    - driving-car
    - cycling-regular
    - foot-walking
    - foot-hiking
    - wheelchair

    Coordinates must be provided as longitude and latitude.
    """

    url = (
        f"https://api.heigit.org/"
        f"openrouteservice/v2/directions/{profile}"
    )

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = {
        "coordinates": [
            [origin_longitude, origin_latitude],
            [destination_longitude, destination_latitude]
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("routes"):
        return {
            "success": False,
            "error": "No route found"
        }

    route = data["routes"][0]

    summary = route.get("summary", {})

    return {
        "success": True,
        "distance_km": round(
            summary.get("distance", 0) / 1000,
            2
        ),
        "duration_minutes": round(
            summary.get("duration", 0) / 60,
            2
        ),
        "distance_meters": summary.get("distance"),
        "duration_seconds": summary.get("duration"),
    }