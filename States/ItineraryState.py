
from typing import TypedDict,Any,Dict,List

class ItineraryState(TypedDict, total=False):

    itinerary: List[Dict[str, Any]]

    daily_plans: Dict[str, Any]

    itinerary_cost: float

    warnings: List[str]