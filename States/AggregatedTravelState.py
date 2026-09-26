from typing import Any,Dict,Optional,List
from pydantic import BaseModel, ConfigDict
class AggregatedTravelState(BaseModel):
    model_config = ConfigDict(total=False)

    flight_data: Dict[str, Any]

    hotel_data: Dict[str, Any]

    destination_data: Dict[str, Any]

    candidate_packages: List[Dict[str, Any]]