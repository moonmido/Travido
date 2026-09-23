
from typing import Any,Dict,Optional,List
from pydantic import BaseModel

class CriticState(BaseModel, total=False):

    valid: bool

    problems: List[Dict[str, Any]]

    warnings: List[str]

    score: float

    needs_revision: bool

    revision_instructions: List[str]