from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ConstraintBuilderState(BaseModel):
    model_config = ConfigDict(total=False)

    user_query: Optional[str] = None

    origin: Optional[str] = None
    destination: Optional[str] = None

    departure_date: Optional[str] = None
    return_date: Optional[str] = None

    travelers: Optional[int] = None

    budget: Optional[float] = None
    currency: Optional[str] = None

    travel_style: Optional[str] = None

    preferences: Optional[Dict[str, Any]] = None

    hard_constraints: Optional[Dict[str, Any]] = None
    soft_constraints: Optional[Dict[str, Any]] = None

    # Constraint builder metadata
    missing_information: Optional[List[str]] = None
    contradictions: Optional[List[str]] = None
    clarification_required: Optional[bool] = None