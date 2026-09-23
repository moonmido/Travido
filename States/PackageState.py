from typing import Any,Dict,Optional,List
from pydantic import BaseModel


class PackageState(BaseModel, total=False):

    candidate_packages: List[Dict[str, Any]]

    optimized_package: Optional[Dict[str, Any]]

    total_cost: float

    remaining_budget: float

    optimization_objective: Dict[str, float]

    reasoning: str