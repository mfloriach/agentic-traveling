from langgraph.graph import END, START, StateGraph

from .builder import planner
from .travel_planner import TripState

graph = StateGraph(TripState)

graph.add_node("destination", planner.handle_destination)
graph.add_node("flight", planner.handle_flight)
graph.add_node("hotel", planner.handle_hotel)
graph.add_node("activities", planner.handle_activities)
graph.add_node("validator", planner.handle_validator)

graph.add_edge(START, "destination")
graph.add_edge("destination", "flight")
graph.add_edge("destination", "hotel")
graph.add_edge("destination", "activities")
graph.add_edge("flight", "validator")
graph.add_edge("hotel", "validator")
graph.add_edge("activities", "validator")

graph.add_conditional_edges(
    "validator",
    planner.route_after_validation,
    {
        "finish": END,
        "retry": "destination",
    },
)

app = graph.compile()
