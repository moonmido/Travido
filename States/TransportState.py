from typing import Any,Dict,Optional,List
from pydantic import BaseModel, ConfigDict
class TransportState(BaseModel):
    model_config = ConfigDict(total=False)

    transport_options: List[Dict[str, Any]]

    selected_transport: List[Dict[str, Any]]

    transport_cost: float

    transport_warnings: List[str]