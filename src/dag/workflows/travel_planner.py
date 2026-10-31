import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, NotRequired, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from logger import logger
from tracing import traced_node

from ..agents.schemas import (
    ActivitiesOutput,
    DestinationOutput,
    FlightOutput,
    HotelOutput,
)


class Node(StrEnum):
    DESTINATION = "destination"
    HOTEL = "hotel"
    FLIGHT = "flight"
    ACTIVITIES = "activities"
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


class TripState(TypedDict):
    user_id: NotRequired[uuid.UUID]
    triage: Triage

    user_input: str
    origin_city: str
    destination: NotRequired[DestinationOutput]

    hotel: NotRequired[HotelOutput]
    flight: NotRequired[FlightOutput]
    activities: NotRequired[ActivitiesOutput]

    validation: NotRequired[ValidationResult]
    retry_count: int


@dataclass
class TravelDeps:
    retries: int
    wheather: API


@dataclass
class Agents:
    destination: Agent[TravelDeps, DestinationOutput]
    flight: Agent[TravelDeps, FlightOutput]
    hotel: Agent[TravelDeps, HotelOutput]
    activity: Agent[TravelDeps, ActivitiesOutput]


class TravelPlanner:
    def __init__(self, deps: TravelDeps, agents: Agents):
        self.deps = deps
        self.agents = agents

    @traced_node(Node.DESTINATION)
    async def handle_destination(self, state: TripState) -> dict:
        result = await self.agents.destination.run(state["user_input"], deps=self.deps)
        logger.info(f"Destination: {result.output}")
        return {"destination": result.output}

    @traced_node(Node.FLIGHT)
    async def handle_flight(self, state: TripState) -> dict:
        if "destination" not in state:
            raise ValueError("Destination is required before flight")

        prompt = f"Plan a flight from {state['origin_city']} to {state['destination']}"
        result = await self.agents.flight.run(prompt, deps=self.deps)
        logger.info(
            f"✈️ Flight: from {result.output.from_city} → {result.output.to_city}, arriving at {result.output.arrival_time}"
        )
        return {"flight": result.output}

    @traced_node(Node.HOTEL)
    async def handle_hotel(self, state: TripState) -> dict:
        if "destination" not in state:
            raise ValueError("Destination is required before hotel recommendation")

        prompt = (
            f"Recommend a hotel in {state['destination']} for a traveler arriving. "
            f"Prefer locations near the airport or city center."
        )
        result = await self.agents.hotel.run(prompt, deps=self.deps)
        logger.info(f"🏨 Hotel: {result.output.name}, {result.output.location}")
        return {"hotel": result.output}

    @traced_node(Node.ACTIVITIES)
    async def handle_activities(self, state: TripState) -> dict:
        if "destination" not in state:
            raise ValueError("Destination is required before activities")

        prompt = (
            f"Suggest activities in {state['destination']} close to {'hotel.name'} "
        )
        result = await self.agents.activity.run(prompt, deps=self.deps)
        for a in result.output:
            logger.info(f"  - {a}")
        return {"activities": result.output}

    async def handle_validator(self, state: TripState) -> dict:
        issues: list[str] = []

        if "destination" not in state:
            issues.append("Missing destination")

        if "flight" not in state:
            issues.append("Missing flight arrival time")

        if "hotel" not in state:
            issues.append("Missing hotel")

        if "activities" not in state:
            issues.append("Missing activities")

        return {
            "validation": ValidationResult(
                passed=not issues,
                issues=issues,
            )
        }

    def route_after_validation(self, state: TripState) -> str:
        if "validation" in state and state["validation"].passed:
            return "finish"

        if state["retry_count"] >= self.deps.retries:
            return "finish"  # Replace with a failure handler.

        return "retry"

    def build(self):
        graph = StateGraph(TripState)

        graph.add_node(Node.DESTINATION, self.handle_destination)
        graph.add_node(Node.FLIGHT, self.handle_flight)
        graph.add_node(Node.HOTEL, self.handle_hotel)
        graph.add_node(Node.ACTIVITIES, self.handle_activities)
        graph.add_node(Node.VALIDATOR, self.handle_validator)

        graph.add_edge(START, Node.DESTINATION)
        graph.add_edge(Node.DESTINATION, Node.FLIGHT)
        graph.add_edge(Node.DESTINATION, Node.HOTEL)
        graph.add_edge(Node.DESTINATION, Node.ACTIVITIES)
        graph.add_edge(Node.FLIGHT, Node.VALIDATOR)
        graph.add_edge(Node.HOTEL, Node.VALIDATOR)
        graph.add_edge(Node.ACTIVITIES, Node.VALIDATOR)

        graph.add_conditional_edges(
            Node.VALIDATOR,
            self.route_after_validation,
            {
                "finish": END,
                "retry": "destination",
            },
        )

        return graph.compile()
