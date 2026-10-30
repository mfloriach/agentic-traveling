import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

from dag.agents.agents import activities, destination, flight, hotel
from dag.services.travel_planner import API, Agents, TravelDeps, TravelPlanner
from dag.utils.api_client import APIClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


deps = TravelDeps(
    retries=2,
    wheather=cast("API", APIClient("https://api.open-meteo.com")),
)

agents = Agents(
    destination=destination, flight=flight, hotel=hotel, activity=activities
)

planner = TravelPlanner(deps=deps, agents=agents)
graph = planner.build()


def main() -> None:
    # repo root on sys.path so `src.routes` resolves when run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import uvicorn

    uvicorn.run("routes:app", host="127.0.0.1", port=8010)


if __name__ == "__main__":
    main()
