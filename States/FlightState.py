from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class FlightState(BaseModel):
    model_config = ConfigDict(total=False)

    search_params: Optional[Dict[str, Any]] = None

    available_flights: Optional[List[Dict[str, Any]]] = None

    selected_flight: Optional[Dict[str, Any]] = None

    total_flight_cost: Optional[float] = None

    errors: Optional[List[str]] = None