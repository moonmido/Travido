
from typing import List,Dict,Any
from pydantic import BaseModel, ConfigDict
class ConstraintBuilderState(BaseModel):
    model_config = ConfigDict(total=False)

    user_query: str

    origin: str
    destination: str

    departure_date: str
    return_date: str

    travelers: int

    budget: float
    currency: str

    travel_style: str

    preferences: Dict[str, Any]

    hard_constraints: Dict[str, Any]
    soft_constraints: Dict[str, Any]

    # Constraint builder metadata
    missing_information: List[str]
    contradictions: List[str]
    clarification_required: bool