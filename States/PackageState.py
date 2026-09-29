from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class PackageState(BaseModel):
    model_config = ConfigDict(total=False)

    candidate_packages: Optional[List[Dict[str, Any]]] = None

    optimized_package: Optional[Dict[str, Any]] = None

    total_cost: Optional[float] = None

    remaining_budget: Optional[float] = None

    optimization_objective: Optional[Dict[str, float]] = None

    reasoning: Optional[str] = None