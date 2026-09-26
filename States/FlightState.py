from typing import Any,Dict,Optional,List
from pydantic import BaseModel, ConfigDict
class FlightState(BaseModel):
    model_config = ConfigDict(total=False)

    search_params: Dict[str, Any]

    available_flights: List[Dict[str, Any]]

    selected_flight: Optional[Dict[str, Any]]

    total_flight_cost: float

    errors: List[str]