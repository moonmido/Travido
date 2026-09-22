from typing import TypedDict,Any,Dict,Optional,List

class FlightState(TypedDict, total=False):

    search_params: Dict[str, Any]

    available_flights: List[Dict[str, Any]]

    selected_flight: Optional[Dict[str, Any]]

    total_flight_cost: float

    errors: List[str]