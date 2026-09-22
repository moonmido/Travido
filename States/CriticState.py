
from typing import TypedDict,Any,Dict,Optional,List

class CriticState(TypedDict, total=False):

    valid: bool

    problems: List[Dict[str, Any]]

    warnings: List[str]

    score: float

    needs_revision: bool

    revision_instructions: List[str]