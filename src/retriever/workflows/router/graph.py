from langgraph.graph import END, START, StateGraph

from .builder import router
from .router import QueryState

graph = StateGraph(QueryState)

graph.add_node("cache_lookup", router.cache_lookup)
graph.add_node("retrieve", router.retrieve)
graph.add_node("rerank", router.rerank)
graph.add_node("search", router.search)
graph.add_node("response", router.respond)

graph.add_edge(START, "cache_lookup")

graph.add_conditional_edges(
    "cache_lookup",
    router.route_after_cache,
    {
        "respond": "response",
        "retrieve": "retrieve",
    },
)

graph.add_conditional_edges(
    "retrieve",
    router.route_after_retrive,
    {
        "rerank": "rerank",
        "search": "search",
    },
)

graph.add_edge("rerank", "response")
graph.add_edge("search", "response")
graph.add_edge("response", END)

app = graph.compile()
