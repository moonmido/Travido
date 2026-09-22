from typing import TypedDict,Any,Dict,Optional,List


class AggregatedTravelState(TypedDict, total=False):

    flight_data: Dict[str, Any]

    hotel_data: Dict[str, Any]

    destination_data: Dict[str, Any]

    candidate_packages: List[Dict[str, Any]]