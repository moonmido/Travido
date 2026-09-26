from pydantic import BaseModel, ConfigDict
from typing import Any,Dict,Optional,List


class DestinationState(BaseModel):
    model_config = ConfigDict(total=False)

    attractions: List[Dict[str, Any]]

    activities: List[Dict[str, Any]]

    restaurants: List[Dict[str, Any]]

    local_tips: List[str]

    destination_research: Dict[str, Any]

    errors: List[str]