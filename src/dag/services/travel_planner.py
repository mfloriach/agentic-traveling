import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Optional, Protocol

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


class TripState(BaseModel):
    user_id: Optional[uuid.UUID] = None
    triage: Triage

    user_input: str
    origin_city: str
    destination: Optional[DestinationOutput] = None

    hotel: Optional[HotelOutput] = None
    flight: Optional[FlightOutput] = None
    activities: Optional[ActivitiesOutput] = None

    validation: ValidationResult
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
        result = await self.agents.destination.run(state.user_input, deps=self.deps)
        state.destination = result.output
        logger.info(f"Destination: {state.destination}")
        return {"destination": state.destination.dict}

    @traced_node(Node.FLIGHT)
    async def handle_flight(self, state: TripState) -> FlightOutput:
        if not state.destination:
            raise ValueError("Destination is required before flight")

        prompt = f"Plan a flight from {state.origin_city} to {state.destination}"
        result = await self.agents.flight.run(prompt, deps=self.deps)
        state.flight = result.output
        logger.info(
            f"✈️ Flight: from {state.flight.from_city} → {state.destination}, arriving at {state.flight.arrival_time}"
        )
        return state.flight

    @traced_node(Node.HOTEL)
    async def handle_hotel(self, state: TripState) -> HotelOutput:
        if not state.destination:
            raise ValueError("Destination is required before hotel recommendation")

        prompt = (
            f"Recommend a hotel in {state.destination} for a traveler arriving. "
            f"Prefer locations near the airport or city center."
        )
        result = await self.agents.hotel.run(prompt, deps=self.deps)
        state.hotel = result.output
        logger.info(f"🏨 Hotel: {state.hotel.name}, {state.hotel.location}")
        return state.hotel

    @traced_node(Node.ACTIVITIES)
    async def handle_activities(self, state: TripState) -> ActivitiesOutput:
        if not state.destination:
            raise ValueError("Destination is required before activities")

        prompt = f"Suggest activities in {state.destination} close to {state.hotel} "
        result = await self.agents.activity.run(prompt, deps=self.deps)
        state.activities = result.output
        for a in state.activities:
            logger.info(f"  - {a}")
        return state.activities

    async def handle_validator(self, state: TripState) -> ValidationResult:
        issues: list[str] = []

        # if not state.destination:
        #     issues.append("Missing destination")

        # if not state.arrival_time:
        #     issues.append("Missing flight arrival time")

        # if not state.hotel_name:
        #     issues.append("Missing hotel")

        # if not state.activities:
        #     issues.append("Missing activities")

        return ValidationResult(
            passed=True,  # not issues,
            issues=issues,
        )

    def route_after_validation(self, state: TripState) -> str:
        if state.validation.passed:
            return "finish"

        if state.retry_count >= self.deps.retries:
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
