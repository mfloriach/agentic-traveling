import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph, NotRequired
from qdrant_client.models import ScoredPoint

from src.retriever.workflows.planner.travel_planner import (
    Triage,
    TripState,
    ValidationResult,
)
from src.tracing import traced_node


class Node(StrEnum):
    CACHE_LOOKUP = "cache_lookup"
    RETRIEVE = "retrieve"
    RERANK = "rerank"
    SEARCH = "search"
    RESPONSE = "response"


class SemanticDatabaseRetrieve(Protocol):
    def search(self, query: str, limit: int = 5) -> list[ScoredPoint]: ...


class SemanticCache(Protocol):
    def get(
        self,
        query: str,
        tenant_id: str,
        threshold: float = 0.95,
        limit: int = 5,
    ) -> str | None: ...

    def set(
        self,
        query: str,
        answer: str,
        tenant_id: str,
        ttl: int = 3600,
    ) -> None: ...


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        points: list[ScoredPoint],
    ) -> list[ScoredPoint]: ...


@dataclass
class RouterDeps:
    graph: CompiledStateGraph[TripState, None, TripState, TripState]
    database: SemanticDatabaseRetrieve
    cache: SemanticCache
    # reranker: Reranker


class QueryState(TypedDict):
    query: str
    user_id: uuid.UUID

    cached_response: NotRequired[TripState]
    points: NotRequired[list[ScoredPoint]]
    reranked_documents: NotRequired[list[ScoredPoint]]
    response: NotRequired[TripState]


class Router:
    def __init__(self, deps: RouterDeps):
        self.deps = deps

    @traced_node(Node.CACHE_LOOKUP)
    def cache_lookup(self, state: QueryState):
        return {}
        # cached = self.deps.cache.get(
        #     query=state["query"],
        #     tenant_id=str(state["user_id"]),
        #     threshold=0.95,
        # )

        # if cached is None:
        #     return {}

        # return {"cached_response": cached}

    @traced_node(Node.RETRIEVE)
    def retrieve(self, state: QueryState):
        points = self.deps.database.search(state["query"], limit=5)

        high_scores = [point for point in points if point.score > 0.8]
        if not high_scores:
            return {"action": "search"}

        return {"points": points}

    @traced_node(Node.RERANK)
    def rerank(self, state: QueryState):
        if "points" not in state:
            raise ValueError("Points are not present")

        # documents = self.deps.reranker.rerank(
        #     query=state["query"],
        #     points=state["points"],
        # )

        return {"reranked_documents": state["points"]}

    @traced_node(Node.RESPONSE)
    def respond(self, state: QueryState):
        if "cached_response" in state:
            return {"response": state["cached_response"]}

        if "response" not in state:
            raise ValueError("There are not response")

        response = state["response"]

        # self.deps.cache.set(
        #     query=state["query"],
        #     answer=str(json.dumps(response.__dict__)),
        #     tenant_id=str(state["user_id"]),
        # )

        return {"response": response}

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
                # TODO: investigate if this is needed for our use case
                # recursion_limit=3,
                # TODO: investigate if this is needed for our use case
                max_concurrency=10,
            ),
        )
        return {"response": response}

    def route_after_cache(self, state: QueryState) -> str:
        if "cached_response" in state:
            return "respond"

        return "retrieve"

    def route_after_retrive(self, state: QueryState) -> str:
        if "points" in state:
            return "rerank"

        return "search"
