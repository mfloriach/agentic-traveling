import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, Optional, Protocol

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ...logger import logger
from ..agents.schemas import Activities, DestinationOutput, FlightPlan, HotelOption


class Node(StrEnum):
    ROUTER = "router"
    RESEARCH_HOTEL = "research:hotel"
    RESEARCH_FLIGHTS = "research:flight"
    RESEARCH_ACTIVITIES = "research:activities"
    VALIDATOR = "validator"


class API(Protocol):
    def get(self, path: str, **kwargs) -> dict: ...
    def close(self) -> None: ...


class Triage(BaseModel):
    category: Literal[
        "destination",
        "transport",
        "accommodation",
        "activities",
        "restaurants",
        "itinerary",
        "budget",
        "weather",
        "travel_requirements",
        "booking_changes",
        "general",
    ]
    priority: Literal["anonymous", "normal", "vip"]
    needs_human: bool = False
    reason: str


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)


class TripState(BaseModel):
    user_id: uuid.UUID

    user_input: str
    origin_city: str
    triage: Triage

    destination: Optional[str] = None
    from_city: Optional[str] = None
    arrival_time: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_location: Optional[str] = None
    activities: Optional[str] = None

    validation: ValidationResult
    retry_count: int


@dataclass
class TravelDeps:
    wheather: API


@dataclass
class Agents:
    destination: Agent[TravelDeps, DestinationOutput]
    flight: Agent[TravelDeps, FlightPlan]
    hotel: Agent[TravelDeps, HotelOption]
    activity: Agent[TravelDeps, Activities]


class TravelPlanner:
    def __init__(self, deps: TravelDeps, agents: Agents):
        self.deps = deps
        self.agents = agents

    async def handle_destination(self, state: TripState) -> None:
        # result = await self.agents.destination.run(state.user_input, deps=self.deps)
        state.destination = "result.output.destination"
        logger.info(f"Destination: {state.destination}")

    async def handle_flight(self, state: TripState) -> None:
        prompt = f"Plan a flight from {state.origin_city} to {state.destination}"
        # result = await self.agents.flight.run(prompt, deps=self.deps)
        state.from_city = "result.output.from_city"
        state.arrival_time = "result.output.arrivla_time"
        logger.info(
            f"✈️ Flight: from {state.from_city} → {state.destination}, arriving at {state.arrival_time}"
        )

    async def handle_hotel(self, state: TripState) -> None:
        prompt = (
            f"Recommend a hotel in {state.destination} for a traveler arriving at {state.arrival_time}. "
            f"Prefer locations near the airport or city center."
        )
        # result = await self.agents.hotel.run(prompt, deps=self.deps)
        state.hotel_name = "result.output.name"
        state.hotel_location = "result.output.location"
        logger.info(f"🏨 Hotel: {state.hotel_name}, {state.hotel_location}")

    async def handle_activities(self, state: TripState) -> None:
        prompt = (
            f"Suggest activities in {state.destination} close to {state.hotel_location} "
            f"and suitable for a traveler arriving at {state.arrival_time}."
        )
        # result = await self.agents.activity.run(prompt, deps=self.deps)
        state.activities = "result.output.top_activities"
        for a in state.activities:
            logger.info(f"  - {a}")

    async def handle_validator(self, state: TripState) -> dict[str, Any]:
        issues: list[str] = []

        # if not state.destination:
        #     issues.append("Missing destination")

        # if not state.arrival_time:
        #     issues.append("Missing flight arrival time")

        # if not state.hotel_name:
        #     issues.append("Missing hotel")

        # if not state.activities:
        #     issues.append("Missing activities")

        return {
            "validation": ValidationResult(
                passed=not issues,
                issues=issues,
            )
        }

    @staticmethod
    def route_after_validation(state: TripState) -> str:
        if state.validation.passed:
            return "finish"

        if state.retry_count >= 2:
            return "finish"  # Replace with a failure handler.

        return "retry"

    def build(self):
        graph = StateGraph(TripState)

        graph.add_node("destination", self.handle_destination)
        graph.add_node("flight", self.handle_flight)
        graph.add_node("hotel", self.handle_hotel)
        graph.add_node("activities", self.handle_activities)
        graph.add_node("validator", self.handle_validator)

        graph.add_edge(START, "destination")
        graph.add_edge("destination", "flight")
        graph.add_edge("flight", "hotel")
        graph.add_edge("hotel", "activities")
        graph.add_edge("activities", "validator")

        graph.add_conditional_edges(
            "validator",
            self.route_after_validation,
            {
                "finish": END,
                "retry": "destination",
            },
        )

        return graph.compile()
