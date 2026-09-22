from typing import TypedDict,Any,Dict,Optional,List

class HotelState(TypedDict, total=False):

    search_params: Dict[str, Any]

    available_hotels: List[Dict[str, Any]]

    selected_hotel: Optional[Dict[str, Any]]

    total_hotel_cost: float

    errors: List[str]