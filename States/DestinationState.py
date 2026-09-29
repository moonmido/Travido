from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional, List


class DestinationState(BaseModel):
    model_config = ConfigDict(total=False)

    attractions: Optional[List[Dict[str, Any]]] = None

    activities: Optional[List[Dict[str, Any]]] = None

    restaurants: Optional[List[Dict[str, Any]]] = None

    local_tips: Optional[List[str]] = None

    destination_research: Optional[Dict[str, Any]] = None

    errors: Optional[List[str]] = None