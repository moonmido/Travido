from pydantic import BaseModel
from typing import Any,Dict,List

class ItineraryState(BaseModel total=False):

    itinerary: List[Dict[str, Any]]

    daily_plans: Dict[str, Any]

    itinerary_cost: float

    warnings: List[str]