from typing import TypedDict,Any,Dict,Optional,List

class TransportState(TypedDict, total=False):

    transport_options: List[Dict[str, Any]]

    selected_transport: List[Dict[str, Any]]

    transport_cost: float

    transport_warnings: List[str]