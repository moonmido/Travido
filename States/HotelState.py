from typing import Any,Dict,Optional,List
from pydantic import BaseModel

class HotelState(BaseModel, total=False):

    search_params: Dict[str, Any]

    available_hotels: List[Dict[str, Any]]

    selected_hotel: Optional[Dict[str, Any]]

    total_hotel_cost: float

    errors: List[str]