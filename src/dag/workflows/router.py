import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, List, Protocol, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph, NotRequired
from qdrant_client.models import ScoredPoint

from src.dag.workflows.travel_planner import Triage, TripState, ValidationResult
from src.tracing import traced_node


class Node(StrEnum):
    ROUTER = "router"
    SEARCH = "search"
    RESPOND = "respond"


class DatabaseRetrieve(Protocol):
    def search(self, query: str, limit: int = 5) -> List[ScoredPoint]: ...


@dataclass
class RouterDeps:
    graph: CompiledStateGraph[TripState, None, TripState, TripState]
    database: DatabaseRetrieve


class QueryState(TypedDict):
    query: str
    user_id: uuid.UUID
    action: NotRequired[str]
    response: NotRequired[TripState]


class Router:
    def __init__(self, deps: RouterDeps):
        self.deps = deps

    @traced_node(Node.ROUTER)
    def router(self, state: QueryState):
        points = self.deps.database.search(state["query"], limit=5)
        print(f"Router: Found {len(points)} points for query '{state['query']}'")
        for p in points:
            print(f" - {p.score}")

        # The old ">= 5 points → respond" shortcut was unreachable: a response
        # only exists after `search` runs, so a direct-entry respond always
        # raised. KB-hitShortcut needs a cached-response path first. # TODO
        return {"action": "search"}

    @traced_node(Node.RESPOND)
    def respond(self, state: QueryState):
        if "response" not in state:
            raise ValueError("Router did not set a response")

        return {"query": state["query"], "response": state["response"]}

    @traced_node(Node.SEARCH)
    async def search(self, state: QueryState) -> dict[str, Any]:
        response = await self.deps.graph.ainvoke(
            TripState(
                user_id=state["user_id"],
                user_input=state["query"],
                origin_city="Barcelona",
                triage=Triage(
                    category="general", priority="normal", reason="initial request"
                ),
                validation=ValidationResult(passed=False),
                retry_count=0,
            ),
            config=RunnableConfig(
                # happy path = 6 super-steps; +5 per retry round-trip.
                # 25 (langgraph default) covers retries=2 with slack.
                # recursion_limit=3, #TODO: investigate if this is needed for our use case
                max_concurrency=10,  # TODO: investigate if this is needed for our use case
            ),
        )
        return {"query": state["query"], "response": response}

    def build(self):
        graph = StateGraph(QueryState)

        graph.add_node("router", self.router)
        graph.add_node("search", self.search)
        graph.add_node("respond", self.respond)

        graph.add_edge(START, "router")
        graph.add_edge("router", "search")
        graph.add_edge("search", "respond")
        graph.add_edge("respond", END)

        return graph.compile()
