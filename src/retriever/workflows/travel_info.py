import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import NotRequired, TypedDict

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.infrastructure.database import PostgresDatabase

from ..agents.schemas import (
    DestinationOutput,
)


class Node(StrEnum):
    DESTINATION = "destination"
    HOTEL = "hotel"


# Typed per-node updates: static-checked by pyright/mypy, value types reused
# from the agent output schemas (single source — no duplicated models).
class DestinationUpdate(TypedDict):
    destination: DestinationOutput


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)


class TripState(TypedDict):
    user_id: NotRequired[uuid.UUID]


@dataclass
class TravelInfo:
    database: PostgresDatabase


@dataclass
class Agents:
    destination: Agent[TravelInfo, DestinationOutput]


class TravelPlanner:
    def __init__(self, deps: TravelInfo, agents: Agents):
        self.deps = deps
        self.agents = agents

    # @traced_node(Node.DESTINATION)
    # async def handle_check(self, state: TripState) -> DestinationUpdate:
    #     result = await self.agents.destination.run(state["user_input"], deps=self.deps)
    #     logger.info(f"Destination: {result.output}")
    #     return {"destination": result.output}

    # def build(self):
    #     graph = StateGraph(TripState)

    #     graph.add_node(Node.DESTINATION, self.handle_check)
    #     graph.add_node(Node.FLIGHT, self.handle_flight)

    #     graph.add_edge(START, Node.DESTINATION)
    #     graph.add_edge(Node.ACTIVITIES, Node.VALIDATOR)

    #     graph.add_conditional_edges(
    #         Node.VALIDATOR,
    #         self.route_after_validation,
    #         {
    #             "finish": END,
    #             "retry": Node.DESTINATION,
    #         },
    #     )

    #     return graph.compile()
