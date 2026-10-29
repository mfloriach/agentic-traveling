from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
from ..agents.agents import destination, flight, hotel, activities
import logfire
from enum import StrEnum
from typing import Protocol, Literal
from langgraph.graph import StateGraph, START, END


class Node(StrEnum):
    ROUTER = "router"
    RESEARCH_HOTEL = "research:hotel"
    RESEARCH_FLIGHTS = "research:flight"
    RESEARCH_ACTIVITIES = "research:activities"
    VALIDATOR = "validator"


class API(Protocol):
    def get(self, path: str, **kwargs) -> dict: ... 
    def close() -> None: ...
    
@dataclass
class Services:
    wheather: API
    
class Triage(BaseModel):
    category: Literal[
        "destination", "transport", "accommodation",
        "activities", "restaurants", "itinerary",
        "budget", "weather", "travel_requirements",
        "booking_changes", "general",
    ]
    priority: Literal["anonymous", "normal", "vip"]
    needs_human: bool = False
    reason: str
    
class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)

class TripState(BaseModel):
    user_input: str
    triage: Triage
    
    destination: Optional[str] = None
    from_city: Optional[str] = None
    arrival_time: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_location: Optional[str] = None
    
    validation: ValidationResult
    retry_count: int

@dataclass
class TravelDeps:
    user_name: str
    origin_city: str
    services: Services

class TravelPlanner:
    def __init__(self, deps: TravelDeps):
        self.deps = deps
        
        self.destination_agent = destination
        self.flight_agent = flight
        self.hotel_agent = hotel
        self.activity_agent = activities
       
    async def handle_destination(self, state: TripState) -> None:
        result = await self.destination_agent.run(state.user_input, deps=self.deps)
        self.ctx.destination = result.output.destination
        print(f"Destination: {self.ctx.destination}")
        
    async def handle_flight(self, state: TripState) -> None:
        prompt = f"Plan a flight from {self.deps.origin_city} to {self.ctx.destination}"
        result = await self.flight_agent.run(prompt, deps=self.deps)
        self.ctx.from_city = result.output.from_city
        self.ctx.arrival_time = result.output.arrivla_time
        print(
            f"✈️ Flight: from {self.ctx.from_city} → {self.ctx.destination}, arriving at {self.ctx.arrival_time}"
        )
        
    async def handle_hotel(self, state: TripState) -> None:
        prompt = (
            f"Recommend a hotel in {self.ctx.destination} for a traveler arriving at {self.ctx.arrival_time}. "
            f"Prefer locations near the airport or city center."
        )
        result = await self.hotel_agent.run(prompt, deps=self.deps)
        self.ctx.hotel_name = result.output.name
        self.ctx.hotel_location = result.output.location
        print(
            f"🏨 Hotel: {self.ctx.hotel_name}, {result.output.stars}★ at ${result.output.price_per_night_usd}/night"
        )
        logfire.info(str(result.output))

    async def handle_activities(self, state: TripState) -> None:
        prompt = (
            f"Suggest activities in {self.ctx.destination} close to {self.ctx.hotel_location} "
            f"and suitable for a traveler arriving at {self.ctx.arrival_time}."
        )
        result = await self.activity_agent.run(prompt, deps=self.deps)
        print(f"🎯 Activities for {result.output.personalized_for}:")
        for a in result.output.top_activities:
            print(f"  - {a}")
            
    async def handle_validator(self, state: TripState) -> None:
        issues = []

        if not state.get("destination"):
            issues.append("Missing destination")

        if not state.get("arrival_time"):
            issues.append("Missing flight arrival time")

        if not state.get("hotel_name"):
            issues.append("Missing hotel")

        if not state.get("activities"):
            issues.append("Missing activities")

        return {
            "validation": ValidationResult(
                passed=not issues,
                issues=issues,
            )
        }
        
    @staticmethod
    def route_after_validation(state: TripState) -> str:
        if state["validation"].passed:
            return "finish"

        if state.get("retry_count", 0) >= 2:
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

