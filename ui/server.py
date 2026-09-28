"""Travido UI server.

Form driven front end, no chat box: the browser posts the trip fields, this
process runs the LangGraph workflow and streams every node update back over SSE
so the page can show how the state travels from agent to agent.

    .venv/bin/python ui/server.py
    open http://127.0.0.1:8000
"""

import asyncio
import json
import logging
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402,F401  first import: SSL_CERT_FILE + ssl context patch

from aiohttp import web  # noqa: E402

from Workflow.NodePolicy import POLICIES  # noqa: E402
from Workflow.TravidoWorkflow import (  # noqa: E402
    DEFAULT_MAX_ITERATIONS,
    RECURSION_LIMIT,
    build_graph,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
JOB_LOG = logging.getLogger("travido.jobs")

JOB_RETENTION_SECONDS = 3600
JOBS: Dict[str, "Job"] = {}


# --------------------------------------------------------------------------
# form -> workflow input
# --------------------------------------------------------------------------


def _int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _float(value: Any) -> Optional[float]:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def build_query(form: Dict[str, Any]) -> str:
    """Turn the form fields into the natural language request for the agents."""

    lines = [
        f"Plan a trip from {form['origin']} to {form['destination']} "
        f"from {form['departure_date']} to {form['return_date']}."
    ]

    party = [f"{form['adults']} adult"]
    if form["children"]:
        party.append(f"{form['children']} child")
        party.append(f"{form['rooms']} room")
    lines.append("Travellers: " + ", ".join(party) + ".")

    bags = [f"{form['cabin_bags']} cabin bag"]
    if _int(form["checked_bags"], 0):
        bags.append(f"{form['checked_bags']} checked bag up to {form['checked_bag_kg']} kg")
    else:
        bags.append("no checked bag")
    lines.append("Luggage: " + " and ".join(bags) + ".")

    if form["budget"] is not None:
        lines.append(
            f"Budget: {form['budget']} {form['currency']}, "
            f"{'hard limit' if form['budget_is_strict'] else 'target, may be exceeded'}. "
            f"Cost priority: {form['cost_priority']}."
        )
    else:
        lines.append(f"No budget was given. Cost priority: {form['cost_priority']}.")

    optional = [
        ("Travel style", form["travel_style"]),
        ("Accommodation", form["accommodation"]),
        ("Flight preferences", form["flight_prefs"]),
        ("Transport preferences", form["transport_prefs"]),
        ("Activities", form["activities"]),
        ("Food", form["food"]),
    ]
    for label, value in optional:
        if value:
            lines.append(f"{label}: {value}.")

    if form["notes"]:
        lines.append(f"Additional notes: {form['notes']}")

    return "\n".join(lines)


def build_initial_state(form: Dict[str, Any]) -> Dict[str, Any]:
    """Seed the state with the hard facts so a degraded builder is survivable."""

    return {
        "user_query": build_query(form),
        "origin": form["origin"],
        "destination": form["destination"],
        "departure_date": form["departure_date"],
        "return_date": form["return_date"],
        "travelers": form["travelers"],
        "budget": form["budget"],
        "currency": form["currency"],
        "travel_style": form["travel_style"] or None,
        "preferences": {
            "luggage": {
                "cabin_bags": form["cabin_bags"],
                "checked_bags": form["checked_bags"],
                "checked_bag_weight_kg": form["checked_bag_kg"],
            },
            "cost_priority": form["cost_priority"],
            "accommodation": form["accommodation"] or None,
            "flight": form["flight_prefs"] or None,
            "transportation": form["transport_prefs"] or None,
            "activities": form["activities"] or None,
            "food": form["food"] or None,
            "notes": form["notes"] or None,
        },
        "iteration": 0,
        "max_iterations": form["max_iterations"],
    }


def normalise_form(raw: Dict[str, Any]) -> Dict[str, Any]:
    adults = max(1, _int(raw.get("adults"), 1) or 1)
    children = max(0, _int(raw.get("children"), 0) or 0)

    form = {
        "origin": _text(raw.get("origin")),
        "destination": _text(raw.get("destination")),
        "departure_date": _text(raw.get("departure_date")),
        "return_date": _text(raw.get("return_date")),
        "adults": adults,
        "children": children,
        "rooms": max(1, _int(raw.get("rooms"), 1) or 1),
        "travelers": adults + children,
        "currency": _text(raw.get("currency")) or "EUR",
        "budget": _float(raw.get("budget")),
        "budget_is_strict": bool(raw.get("budget_is_strict")),
        "cost_priority": _text(raw.get("cost_priority")) or "lowest total cost",
        "cabin_bags": max(0, _int(raw.get("cabin_bags"), 1) or 0),
        "checked_bags": max(0, _int(raw.get("checked_bags"), 1) or 0),
        "checked_bag_kg": max(0, _int(raw.get("checked_bag_kg"), 23) or 0),
        "travel_style": _text(raw.get("travel_style")),
        "accommodation": _text(raw.get("accommodation")),
        "flight_prefs": _text(raw.get("flight_prefs")),
        "transport_prefs": _text(raw.get("transport_prefs")),
        "activities": _text(raw.get("activities")),
        "food": _text(raw.get("food")),
        "notes": _text(raw.get("notes")),
        "max_iterations": min(5, max(1, _int(raw.get("max_iterations"), DEFAULT_MAX_ITERATIONS))),
    }

    missing = [f for f in ("origin", "destination", "departure_date", "return_date") if not form[f]]
    if missing:
        raise web.HTTPBadRequest(
            text=json.dumps({"error": f"missing required fields: {', '.join(missing)}"}),
            content_type="application/json",
        )

    return form


# --------------------------------------------------------------------------
# job plumbing
# --------------------------------------------------------------------------


@dataclass
class Job:
    form: Dict[str, Any]
    state: Dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    events: List[Dict[str, Any]] = field(default_factory=list)
    queues: Set["asyncio.Queue"] = field(default_factory=set)
    task: Optional[asyncio.Task] = None
    started: float = field(default_factory=time.time)
    finished: bool = False

    def emit(self, event: Dict[str, Any]) -> None:
        event["t"] = round(time.time() - self.started, 1)
        JOB_LOG.warning("emit %s state_keys=%s", event.get("type"), sorted(self.state or {}))
        self.events.append(event)
        for queue in list(self.queues):
            queue.put_nowait(event)

    def close(self) -> None:
        self.finished = True
        for queue in list(self.queues):
            queue.put_nowait(None)


async def run_job(job: Job) -> None:
    graph = build_graph()

    JOB_LOG.warning("JOB %s start iteration=%s", job.id, job.state.get("iteration"))

    try:
        async for chunk in graph.astream(
            job.state,
            config={"recursion_limit": RECURSION_LIMIT},
            stream_mode=["updates", "values"],
        ):
            mode, payload = chunk
            if mode == "values" and payload:
                job.state = payload
                job.emit({"type": "state", "state": payload})
            elif mode == "updates":
                for node, update in (payload or {}).items():
                    data = update or {}
                    serialised = json.dumps(data, default=str)
                    job.emit(
                        {
                            "type": "node",
                            "node": node,
                            "keys": list(data.keys()),
                            "bytes": len(serialised),
                            "preview": serialised[:8000],
                        }
                    )

        JOB_LOG.warning("JOB %s loop done final_keys=%s", job.id, sorted(job.state or {}))

        job.emit(
            {
                "type": "done",
                "final_response": job.state.get("final_response", ""),
                "node_errors": job.state.get("node_errors"),
                "iteration": job.state.get("iteration"),
                "clarification_required": job.state.get("clarification_required"),
            }
        )

    except asyncio.CancelledError:
        job.emit({"type": "cancelled"})
        raise

    except Exception as exc:  # noqa: BLE001 - surface anything to the page
        job.emit(
            {
                "type": "error",
                "message": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc()[-2000:],
            }
        )

    finally:
        job.close()


# --------------------------------------------------------------------------
# http handlers
# --------------------------------------------------------------------------


async def index(_request: web.Request) -> web.StreamResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def static_file(request: web.Request) -> web.StreamResponse:
    name = request.match_info["name"]
    if "/" in name or ".." in name:
        raise web.HTTPNotFound()
    return web.FileResponse(STATIC_DIR / name)


async def post_plan(request: web.Request) -> web.StreamResponse:
    try:
        form = normalise_form(await request.json())
    except web.HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise web.HTTPBadRequest(
            text=json.dumps({"error": str(exc)}), content_type="application/json"
        )

    job = Job(form=form, state=build_initial_state(form))
    job.task = asyncio.create_task(run_job(job))
    JOBS[job.id] = job

    asyncio.create_task(_expire_jobs())

    return web.json_response({"job_id": job.id, "query": job.state["user_query"]})


async def _expire_jobs() -> None:
    await asyncio.sleep(JOB_RETENTION_SECONDS)
    now = time.time()
    for job_id, job in list(JOBS.items()):
        if job.finished and now - job.started > JOB_RETENTION_SECONDS:
            JOBS.pop(job_id, None)


async def stream_events(request: web.Request) -> web.StreamResponse:
    job = JOBS.get(request.match_info["job_id"])
    if job is None:
        raise web.HTTPNotFound(text=json.dumps({"error": "unknown job"}))

    response = web.StreamResponse(
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
    await response.prepare(request)

    queue: "asyncio.Queue" = asyncio.Queue()
    job.queues.add(queue)

    try:
        for event in list(job.events):
            await response.write(_sse(event))

        while True:
            event = await queue.get()
            if event is None:
                break
            await response.write(_sse(event))
    finally:
        job.queues.discard(queue)

    return response


def _sse(event: Dict[str, Any]) -> bytes:
    return f"data: {json.dumps(event, default=str)}\n\n".encode()


async def cancel_job(request: web.Request) -> web.StreamResponse:
    job = JOBS.get(request.match_info["job_id"])
    if job is None:
        raise web.HTTPNotFound(text=json.dumps({"error": "unknown job"}))
    if job.task and not job.task.done():
        job.task.cancel()
    return web.json_response({"cancelled": True})


async def graph_spec(_request: web.Request) -> web.StreamResponse:
    drawable = build_graph().get_graph()
    return web.json_response(
        {
            "mermaid": drawable.draw_mermaid(),
            "policies": {
                name: {
                    "max_attempts": policy.max_attempts,
                    "run_timeout": policy.run_timeout,
                    "idle_timeout": policy.idle_timeout,
                }
                for name, policy in POLICIES.items()
            },
        }
    )


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/static/{name}", static_file)
    app.router.add_post("/api/plan", post_plan)
    app.router.add_get("/api/jobs/{job_id}/events", stream_events)
    app.router.add_post("/api/jobs/{job_id}/cancel", cancel_job)
    app.router.add_get("/api/graph", graph_spec)
    return app


if __name__ == "__main__":
    web.run_app(build_app(), host="127.0.0.1", port=8000, print=lambda *_: None)
