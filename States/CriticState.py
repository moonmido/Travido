from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class CriticState(BaseModel):
    model_config = ConfigDict(total=False)

    valid: Optional[bool] = None

    problems: Optional[List[Dict[str, Any]]] = None

    warnings: Optional[List[str]] = None

    score: Optional[float] = None

    needs_revision: Optional[bool] = None

    revision_instructions: Optional[List[str]] = None