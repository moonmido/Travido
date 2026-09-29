"""Travido LangGraph workflow.

    START
      -> constraint_builder
      -> [ flight | hotel | destination_research ]   (fan out, run in parallel)
      -> aggregator                                  (fan in)
      -> transport
      -> package_optimizer
      -> itinerary_planner
      -> critic
      -> needs revision? -- yes --> package_optimizer (bounded loop)
                          -- no  --> finalize --> END

Every node is an ``async def`` so that the ``TimeoutPolicy`` watchdog can cancel
it, and every node carries a ``RetryPolicy`` so transient LLM/API failures are
retried with exponential backoff. When a node exhausts its attempts the
``recover_from_error`` handler records the failure in ``node_errors`` instead of
aborting the run. The three parallel branches retry inside the node as well,
because langgraph 1.2.12 cannot suppress a failure raised inside a parallel
superstep through ``error_handler`` (see ``Workflow/Resilience.py``).
"""

import config  # noqa: F401  first import: sets SSL_CERT_FILE for the SDKs below
import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from langchain_core.runnables import Runnable
from langgraph.errors import NodeError
from langgraph.graph import END, START, StateGraph

from Agents.DestinationResearchAgent import DestinationResearchAgent
from Agents.FlightAgent import FlightAgent
from Agents.HotelAgent import HotelAgent
from Agents.ItineraryPlannerAgent import ItineraryPlannerAgent
from Agents.TransportAgent import TransportAgent

from Chains.AggregatorChain import aggregatorChain
from Chains.ConstraintBuilderChain import constraintChain
from Chains.CriticChain import criticChain
from Chains.PackageOptimizerChain import packageOptimizerChain

from States.SharedTravelState import TravelState
from Workflow.NodePolicy import DEFAULT_POLICY, POLICIES, NodePolicy
from Workflow.Resilience import run_with_policy


DEFAULT_MAX_ITERATIONS = 3
RECURSION_LIMIT = 60

CONSTRAINT_FIELDS: Tuple[str, ...] = (
    "user_query",
    "origin",
    "destination",
    "departure_date",
    "return_date",
    "travelers",
    "budget",
    "currency",
    "travel_style",
    "preferences",
    "hard_constraints",
    "soft_constraints",
)

# state key owned by each node, used by the error handler to degrade gracefully
NODE_STATE_KEY: Dict[str, str] = {
    "constraint_builder": "hard_constraints",
    "flight": "flight",
    "hotel": "hotel",
    "destination_research": "destination_research",
    "aggregator": "aggregated",
    "transport": "transport",
    "package_optimizer": "package",
    "itinerary_planner": "itinerary",
    "critic": "critic",
    "finalize": "final_response",
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True)
    if isinstance(value, dict):
        return value
    return {"value": value}


def _as_text(value: Any) -> str:
    if value is None:
        return "{}"
    if isinstance(value, BaseModel):
        value = value.model_dump(exclude_none=True)
    try:
        return json.dumps(value, indent=2, default=str)
    except (TypeError, ValueError):
        return str(value)


def _section(title: str, value: Any) -> str:
    return f"{title}:\n{_as_text(value)}"


def _constraints(state: TravelState) -> Dict[str, Any]:
    return {key: state.get(key) for key in CONSTRAINT_FIELDS if state.get(key)}


def _critic_feedback(state: TravelState) -> Dict[str, Any]:
    critic = _as_dict(state.get("critic"))
    if not critic:
        return {}
    return {
        "score": critic.get("score"),
        "needs_revision": critic.get("needs_revision"),
        "revision_instructions": critic.get("revision_instructions"),
        "problems": critic.get("problems"),
    }


def _structured(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict) and "structured_response" in result:
        result = result["structured_response"]
    return _as_dict(result)


async def _run_chain(chain: Runnable, user_query: str) -> Dict[str, Any]:
    return _structured(await chain.ainvoke({"user_query": user_query}))


async def _run_agent(agent: Runnable, user_query: str) -> Dict[str, Any]:
    result = await agent.ainvoke(
        {"messages": [("user", user_query)]}
    )
    return _structured(result)


# --------------------------------------------------------------------------
# nodes
# --------------------------------------------------------------------------


async def constraint_builder(state: TravelState) -> Dict[str, Any]:
    """Turn the raw user query into a structured travel specification."""

    user_query = state.get("user_query", "")

    out = await _run_chain(constraintChain(user_query), user_query)

    # skip None values so fields the agent left unknown keep the seeded form data
    return {key: out[key] for key in CONSTRAINT_FIELDS if key in out and out[key] is not None}


async def flight(state: TravelState) -> Dict[str, Any]:
    """Search flights that satisfy the shared constraints."""

    prompt = "\n\n".join(
        [
            "Search flights for this trip using the tools available.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
        ]
    )

    outcome = await run_with_policy(POLICIES["flight"], _run_agent, FlightAgent(), prompt)

    return {"flight": outcome.payload()}


async def hotel(state: TravelState) -> Dict[str, Any]:
    """Search accommodation that satisfies the shared constraints."""

    prompt = "\n\n".join(
        [
            "Search hotels for this trip using the tools available.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
        ]
    )

    outcome = await run_with_policy(POLICIES["hotel"], _run_agent, HotelAgent(), prompt)

    return {"hotel": outcome.payload()}


async def destination_research(state: TravelState) -> Dict[str, Any]:
    """Research attractions, activities, food and local context."""

    prompt = "\n\n".join(
        [
            "Research the destination for this trip using the tools available.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
        ]
    )

    outcome = await run_with_policy(
        POLICIES["destination_research"],
        _run_agent,
        DestinationResearchAgent(),
        prompt,
    )

    return {"destination_research": outcome.payload()}


async def aggregator(state: TravelState) -> Dict[str, Any]:
    """Merge the three parallel branches into one coherent dataset."""

    prompt = "\n\n".join(
        [
            "Aggregate the results below into candidate travel packages.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
            _section("FLIGHT AGENT RESULT", state.get("flight")),
            _section("HOTEL AGENT RESULT", state.get("hotel")),
            _section(
                "DESTINATION RESEARCH RESULT", state.get("destination_research")
            ),
        ]
    )

    return {"aggregated": await _run_chain(aggregatorChain(prompt), prompt)}


async def transport(state: TravelState) -> Dict[str, Any]:
    """Resolve ground transport between airport, hotel and activities."""

    prompt = "\n\n".join(
        [
            "Determine the ground transportation needed to execute this plan.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
            _section("AGGREGATED DATA", state.get("aggregated")),
            _section("DESTINATION RESEARCH", state.get("destination_research")),
        ]
    )

    return {"transport": await _run_agent(TransportAgent(), prompt)}


async def package_optimizer(state: TravelState) -> Dict[str, Any]:
    """Build or revise the package, honouring hard constraints first."""

    feedback = _critic_feedback(state)

    prompt = "\n\n".join(
        [
            (
                "Revise the travel package using the critic feedback below."
                if feedback
                else "Build the optimal travel package from the data below."
            ),
            _section("SHARED CONSTRAINTS", _constraints(state)),
            _section("AGGREGATED DATA", state.get("aggregated")),
            _section("TRANSPORT", state.get("transport")),
            _section("DESTINATION RESEARCH", state.get("destination_research")),
            _section("CRITIC FEEDBACK", feedback),
        ]
    )

    result = await _run_chain(packageOptimizerChain(prompt), prompt)

    return {
        "package": result,
        "iteration": state.get("iteration", 0) + 1,
    }


async def itinerary_planner(state: TravelState) -> Dict[str, Any]:
    """Turn the selected package into a day by day itinerary."""

    feedback = _critic_feedback(state)

    prompt = "\n\n".join(
        [
            "Build a realistic day by day itinerary for the package below.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
            _section("SELECTED PACKAGE", state.get("package")),
            _section("TRANSPORT", state.get("transport")),
            _section("DESTINATION RESEARCH", state.get("destination_research")),
            _section("CRITIC FEEDBACK", feedback),
        ]
    )

    return {"itinerary": await _run_agent(ItineraryPlannerAgent(), prompt)}


async def critic(state: TravelState) -> Dict[str, Any]:
    """Inspect the plan and decide whether another iteration is needed."""

    prompt = "\n\n".join(
        [
            "Review the complete travel plan below and report concrete problems.",
            _section("SHARED CONSTRAINTS", _constraints(state)),
            _section("SELECTED PACKAGE", state.get("package")),
            _section("TRANSPORT", state.get("transport")),
            _section("ITINERARY", state.get("itinerary")),
            _section("AGGREGATED DATA", state.get("aggregated")),
        ]
    )

    return {"critic": await _run_chain(criticChain(prompt), prompt)}


async def finalize(state: TravelState) -> Dict[str, Any]:
    """Package Optimizer output: the answer returned to the user."""

    package = _as_dict(state.get("package"))
    critic = _as_dict(state.get("critic"))
    feedback = _critic_feedback(state)

    lines: List[str] = [
        "TRAVILO PLAN",
        "=" * 40,
        "",
        f"Destination      : {state.get('destination', 'unknown')}",
        f"Departure        : {state.get('departure_date', 'unknown')}",
        f"Return           : {state.get('return_date', 'unknown')}",
        f"Travelers        : {state.get('travelers', 'unknown')}",
        f"Budget           : {state.get('budget', 'unknown')} "
        f"{state.get('currency', '')}".rstrip(),
        "",
        "OPTIMIZED PACKAGE",
        "-" * 40,
        _as_text(package),
        "",
        "ITINERARY",
        "-" * 40,
        _as_text(state.get("itinerary")),
        "",
        "CRITIC VERDICT",
        "-" * 40,
        f"iterations   : {state.get('iteration', 0)}"
        f"/{state.get('max_iterations', DEFAULT_MAX_ITERATIONS)}",
        f"score        : {critic.get('score', 'unknown')}",
        f"needs_review : {critic.get('needs_revision', 'unknown')}",
    ]

    if feedback.get("revision_instructions"):
        lines += [
            "",
            "OUTSTANDING REVISION INSTRUCTIONS",
            _as_text(feedback["revision_instructions"]),
        ]

    node_errors = state.get("node_errors") or []
    if node_errors:
        lines += ["", "DEGRADED NODES", _as_text(node_errors)]

    return {"final_response": "\n".join(lines)}


NODES = (
    ("constraint_builder", constraint_builder),
    ("flight", flight),
    ("hotel", hotel),
    ("destination_research", destination_research),
    ("aggregator", aggregator),
    ("transport", transport),
    ("package_optimizer", package_optimizer),
    ("itinerary_planner", itinerary_planner),
    ("critic", critic),
    ("finalize", finalize),
)


# --------------------------------------------------------------------------
# routing + error handling
# --------------------------------------------------------------------------


def route_after_critic(state: TravelState) -> str:
    """Loop back to the Package Optimizer when the critic found problems."""

    critic_state = _as_dict(state.get("critic"))
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", DEFAULT_MAX_ITERATIONS)

    needs_revision = bool(
        critic_state.get("needs_revision", critic_state.get("valid") is False)
    )

    if needs_revision and iteration < max_iterations:
        return "package_optimizer"

    return "finalize"


async def recover_from_error(
    state: TravelState, error: NodeError
) -> Dict[str, Any]:
    """Keep the graph alive when a node exhausts its retry budget.

    The failed node contributes an empty result carrying its error message, so
    downstream nodes can still run on partial data instead of the run dying.

    This handler is async on purpose: node defaults apply the timeout policy to
    error handlers too, and langgraph refuses to compile a timeout on a sync
    node. The workflow therefore has to be driven with ``ainvoke``.
    """

    message = f"{error.node}: {type(error.error).__name__}: {error.error}"

    update: Dict[str, Any] = {
        "node_errors": [*(state.get("node_errors") or []), message]
    }

    key = NODE_STATE_KEY.get(error.node)
    if key:
        failed_value = _as_dict(state.get(key))
        failed_value["errors"] = [
            *(failed_value.get("errors") or []),
            message,
        ]
        update[key] = failed_value

    return update


# --------------------------------------------------------------------------
# graph
# --------------------------------------------------------------------------


def build_graph():
    """Build and compile the Travido workflow."""

    default_policy: NodePolicy = DEFAULT_POLICY

    builder = StateGraph(TravelState)

    builder.set_node_defaults(
        retry_policy=default_policy.retry_policy(),
        timeout=default_policy.timeout_policy(),
        error_handler=recover_from_error,
    )

    for name, node in NODES:
        policy = POLICIES.get(name, default_policy)
        builder.add_node(
            name,
            node,
            retry_policy=policy.retry_policy(),
            timeout=policy.timeout_policy(),
        )

    builder.add_edge(START, "constraint_builder")

    # fan out, the three research agents run in the same superstep
    builder.add_edge("constraint_builder", "flight")
    builder.add_edge("constraint_builder", "hotel")
    builder.add_edge("constraint_builder", "destination_research")

    # fan in, the aggregator waits for all three branches
    builder.add_edge("flight", "aggregator")
    builder.add_edge("hotel", "aggregator")
    builder.add_edge("destination_research", "aggregator")

    builder.add_edge("aggregator", "transport")
    builder.add_edge("transport", "package_optimizer")
    builder.add_edge("package_optimizer", "itinerary_planner")
    builder.add_edge("itinerary_planner", "critic")

    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {"package_optimizer": "package_optimizer", "finalize": "finalize"},
    )

    builder.add_edge("finalize", END)

    return builder.compile()


async def arun_workflow(user_query: str, **overrides: Any) -> Dict[str, Any]:
    """Async entrypoint. Required, the timeout watchdog relies on asyncio."""

    graph = build_graph()

    initial: Dict[str, Any] = {
        "user_query": user_query,
        "iteration": 0,
        "max_iterations": overrides.pop("max_iterations", DEFAULT_MAX_ITERATIONS),
    }
    initial.update(overrides)

    return await graph.ainvoke(
        initial,
        config={"recursion_limit": RECURSION_LIMIT},
    )


def run_workflow(user_query: str, **overrides: Any) -> Dict[str, Any]:
    """Blocking entrypoint for scripts. Use ``await arun_workflow`` in notebooks."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(arun_workflow(user_query, **overrides))

    raise RuntimeError(
        "run_workflow() cannot block inside a running event loop, "
        "await arun_workflow() instead."
    )


__all__: Tuple[str, ...] = (
    "arun_workflow",
    "build_graph",
    "recover_from_error",
    "route_after_critic",
    "run_workflow",
)
