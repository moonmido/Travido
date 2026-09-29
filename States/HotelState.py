from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class HotelState(BaseModel):
    model_config = ConfigDict(total=False)

    search_params: Optional[Dict[str, Any]] = None

    available_hotels: Optional[List[Dict[str, Any]]] = None

    selected_hotel: Optional[Dict[str, Any]] = None

    total_hotel_cost: Optional[float] = None

    errors: Optional[List[str]] = None