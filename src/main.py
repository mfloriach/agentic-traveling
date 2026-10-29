from typing import cast

from .dag.agents.agents import activities, destination, flight, hotel
from .dag.services.travel_planner import API, Agents, TravelDeps, TravelPlanner
from .dag.utils.api_client import APIClient

deps = TravelDeps(
    wheather=cast("API", APIClient("https://api.open-meteo.com")),
)

agents = Agents(
    destination=destination, flight=flight, hotel=hotel, activity=activities
)

planner = TravelPlanner(deps=deps, agents=agents)
graph = planner.build()
