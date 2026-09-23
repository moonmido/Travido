from typing import Any,Dict,Optional,List
from pydantic import BaseModel


class AggregatedTravelState(BaseModel, total=False):

    flight_data: Dict[str, Any]

    hotel_data: Dict[str, Any]

    destination_data: Dict[str, Any]

    candidate_packages: List[Dict[str, Any]]