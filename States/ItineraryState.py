from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional


class ItineraryState(BaseModel):
    model_config = ConfigDict(total=False)

    itinerary: Optional[List[Dict[str, Any]]] = None

    daily_plans: Optional[Dict[str, Any]] = None

    itinerary_cost: Optional[float] = None

    warnings: Optional[List[str]] = None