from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class TransportState(BaseModel):
    model_config = ConfigDict(total=False)

    transport_options: Optional[List[Dict[str, Any]]] = None

    selected_transport: Optional[List[Dict[str, Any]]] = None

    transport_cost: Optional[float] = None

    transport_warnings: Optional[List[str]] = None