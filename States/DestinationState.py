from pydantic import BaseModel

from typing import Any,Dict,Optional,List


class DestinationState(BaseModel, total=False):

    attractions: List[Dict[str, Any]]

    activities: List[Dict[str, Any]]

    restaurants: List[Dict[str, Any]]

    local_tips: List[str]

    destination_research: Dict[str, Any]

    errors: List[str]