"""In-node retry/timeout for the nodes that run in a parallel superstep.

Why this exists next to ``langgraph.types.RetryPolicy``:

``StateGraph(..., error_handler=...)`` degrades gracefully for a node that runs
alone in its superstep, but langgraph 1.2.12 still re-raises the original
exception when the failing node was one of several tasks scheduled together --
the background executor that owns those tasks has no knowledge of the error
handler. The Flight / Hotel / Destination Research branches are exactly that
case (fan out from the constraint builder, fan in at the aggregator), so they
retry inside the node and return a degraded result instead of raising.

The budgets come from the same ``NodePolicy`` objects used for the graph level
``retry_policy`` / ``timeout``, so there is a single source of truth.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from Workflow.NodePolicy import NodePolicy, is_retryable


@dataclass
class NodeOutcome:
    """Result of an in-node retry loop."""

    value: Any = None
    error: Optional[str] = None
    attempts: int = 0

    @property
    def failed(self) -> bool:
        return self.error is not None

    def payload(self, errors_key: str = "errors") -> Dict[str, Any]:
        """Successful value, or an empty record carrying the error."""

        if self.failed:
            return {errors_key: [self.error]}

        return self.value or {}


async def run_with_policy(
    policy: NodePolicy,
    operation: Callable[..., Awaitable[Any]],
    *args: Any,
    **kwargs: Any,
) -> NodeOutcome:
    """Run ``operation`` until it succeeds, with backoff and a per-attempt timeout.

    Never raises for a node level failure: the error is returned in the
    ``NodeOutcome`` so the graph keeps running on partial data.
    """

    delay = policy.initial_interval
    last_error: Optional[BaseException] = None
    message: Optional[str] = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            value = await asyncio.wait_for(
                operation(*args, **kwargs),
                timeout=policy.run_timeout,
            )
            return NodeOutcome(value=value, attempts=attempt)

        except asyncio.CancelledError:
            raise

        except TimeoutError as exc:
            last_error = exc
            message = f"TimeoutError: exceeded run_timeout of {policy.run_timeout}s"

        except BaseException as exc:
            last_error = exc
            message = f"{type(exc).__name__}: {exc}"

            if not is_retryable(exc):
                break

        if attempt == policy.max_attempts:
            break

        await asyncio.sleep(delay + random.uniform(0, delay * 0.1))
        delay = min(delay * policy.backoff_factor, policy.max_interval)

    return NodeOutcome(error=message, attempts=policy.max_attempts)


__all__: Tuple[str, ...] = ("NodeOutcome", "run_with_policy")
