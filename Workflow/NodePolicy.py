"""Retry and timeout policies for every node of the Travido workflow.

Two independent failure controls are configured per node:

* ``RetryPolicy``  -> how many times a failed attempt is retried, with what
  backoff, and which exceptions are considered transient.
* ``TimeoutPolicy`` -> ``run_timeout`` bounds a single attempt in wall clock
  time, ``idle_timeout`` bounds the gap between two progress events.

Timeouts are enforced with asyncio cancellation, so the workflow nodes are
written as ``async def`` and drive the LLM/agent with ``ainvoke``.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Type

import httpx
import requests

from langgraph.errors import NodeTimeoutError
from langgraph.types import RetryPolicy, TimeoutPolicy


TRANSIENT_ERRORS: Tuple[Type[BaseException], ...] = (
    NodeTimeoutError,
    TimeoutError,
    ConnectionError,
    httpx.TransportError,
    httpx.RemoteProtocolError,
    requests.ConnectionError,
    requests.Timeout,
)

FATAL_ERRORS: Tuple[Type[BaseException], ...] = (
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
    ImportError,
    NameError,
    SyntaxError,
    ArithmeticError,
)


def is_retryable(exc: BaseException) -> bool:
    """Transient failures are retried, deterministic bugs are not."""

    if isinstance(exc, NodeTimeoutError):
        return True

    if isinstance(exc, httpx.HTTPStatusError):
        return _retryable_status(exc.response.status_code)

    if isinstance(exc, requests.HTTPError):
        response = exc.response
        return response is None or _retryable_status(response.status_code)

    if isinstance(exc, TRANSIENT_ERRORS):
        return True

    return not isinstance(exc, FATAL_ERRORS)


def _retryable_status(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


@dataclass(frozen=True)
class NodePolicy:
    """Retry and timeout budget for one node.

    ``run_timeout`` bounds one attempt in wall clock time. ``idle_timeout`` is
    opt-in: it only makes sense for nodes that emit progress callbacks, because
    the idle clock is refreshed by callback events and a plain blocking LLM call
    emits none, so any idle budget would fire spuriously.
    """

    max_attempts: int = 3
    run_timeout: float = 120.0
    idle_timeout: Optional[float] = None
    initial_interval: float = 1.0
    backoff_factor: float = 2.0
    max_interval: float = 15.0
    jitter: bool = True

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=self.max_attempts,
            initial_interval=self.initial_interval,
            backoff_factor=self.backoff_factor,
            max_interval=self.max_interval,
            jitter=self.jitter,
            retry_on=is_retryable,
        )

    def timeout_policy(self) -> TimeoutPolicy:
        return TimeoutPolicy(
            run_timeout=self.run_timeout,
            idle_timeout=self.idle_timeout,
            refresh_on="auto",
        )


POLICIES: Dict[str, NodePolicy] = {
    # plain structured-output LLM call
    "constraint_builder": NodePolicy(max_attempts=3, run_timeout=150.0),
    "aggregator": NodePolicy(max_attempts=3, run_timeout=180.0),
    "critic": NodePolicy(max_attempts=3, run_timeout=180.0),
    # tool using agents, they are slower and depend on flaky search/APIs
    "flight": NodePolicy(
        max_attempts=3,
        run_timeout=300.0,
        initial_interval=2.0,
        max_interval=20.0,
    ),
    "hotel": NodePolicy(
        max_attempts=3,
        run_timeout=300.0,
        initial_interval=2.0,
        max_interval=20.0,
    ),
    "destination_research": NodePolicy(
        max_attempts=3,
        run_timeout=300.0,
        initial_interval=2.0,
        max_interval=20.0,
    ),
    "transport": NodePolicy(
        max_attempts=4,
        run_timeout=300.0,
        initial_interval=2.0,
        max_interval=20.0,
    ),
    # revisited by the critic loop, so it gets the most attempts
    "package_optimizer": NodePolicy(
        max_attempts=4,
        run_timeout=240.0,
        initial_interval=1.5,
        max_interval=20.0,
    ),
    "itinerary_planner": NodePolicy(max_attempts=3, run_timeout=300.0),
    # deterministic, no network involved
    "finalize": NodePolicy(max_attempts=1, run_timeout=15.0),
}

DEFAULT_POLICY = NodePolicy()

__all__: Tuple[str, ...] = (
    "DEFAULT_POLICY",
    "NodePolicy",
    "POLICIES",
    "is_retryable",
)
