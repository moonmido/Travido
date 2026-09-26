from pydantic import BaseModel, ConfigDict
from typing import Any,Dict,List

class ItineraryState(BaseModel):
    model_config = ConfigDict(total=False)

    itinerary: List[Dict[str, Any]]

    daily_plans: Dict[str, Any]

    itinerary_cost: float

    warnings: List[str]