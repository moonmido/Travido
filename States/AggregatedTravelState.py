from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class AggregatedTravelState(BaseModel):
    model_config = ConfigDict(total=False)

    flight_data: Optional[Dict[str, Any]] = None

    hotel_data: Optional[Dict[str, Any]] = None

    destination_data: Optional[Dict[str, Any]] = None

    candidate_packages: Optional[List[Dict[str, Any]]] = None