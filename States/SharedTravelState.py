from typing import TypedDict, List, Dict, Any, Optional


class TravelState(TypedDict, total=False):

    # =========================
    # SHARED / Constraint Builder
    # =========================

    user_query: str

    origin: str
    destination: str

    departure_date: str
    return_date: str

    travelers: int

    budget: float
    currency: str

    travel_style: str

    preferences: Dict[str, Any]

    hard_constraints: Dict[str, Any]
    soft_constraints: Dict[str, Any]

    # Constraint builder metadata
    missing_information: List[str]
    contradictions: List[str]
    clarification_required: bool


    # =========================
    # FLIGHT
    # =========================

    flight: Dict[str, Any]

    # =========================
    # HOTEL
    # =========================

    hotel: Dict[str, Any]

    # =========================
    # DESTINATION
    # =========================

    destination_research: Dict[str, Any]

    # =========================
    # AGGREGATION
    # =========================

    aggregated: Dict[str, Any]

    # =========================
    # TRANSPORT
    # =========================

    transport: Dict[str, Any]

    # =========================
    # PACKAGE
    # =========================

    package: Dict[str, Any]

    # =========================
    # ITINERARY
    # =========================

    itinerary: Dict[str, Any]

    # =========================
    # CRITIC
    # =========================

    critic: Dict[str, Any]

    # =========================
    # LOOP
    # =========================

    iteration: int
    max_iterations: int

    # =========================
    # OUTPUT
    # =========================

    final_response: str