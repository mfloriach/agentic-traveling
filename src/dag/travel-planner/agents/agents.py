from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking, WebSearch
from .schemas import DestinationOutput, FlightPlan, HotelOption, Activities
from ..services.travel_planner import TripContext


destination = Agent(
    name="destination",
    description="medical advice base on the patient",
    dependencies=TripContext,
    output_model= DestinationOutput,
    model="openai:gpt-4o",
    max_concurrency=10,
    max_token=1000,
    temperature=0.5,
    system_prompt=(
        "You are a triaged assistant helping patients."
        "Provide clear advice and assess urgency."
        "Always mention the patient's name whe available"
    ),
    capabilities=[Thinking(effort="high"), WebSearch()],
    instructions="asdsadsadsaad",
)

@destination.tool
def get_weather(ctx: TripContext[None], latitude: float, longitude: float) -> str:
    """Get current weather for coordinates."""
    response = ctx.deps.http_client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
            "temperature_unit": "fahrenheit",
        },
    )
    data = response.json()["current"]
    return f"Temperature: {data['temperature_2m']}F, Wind: {data['wind_speed_10m']} km/h"


flight = Agent(
    name="flight",
    description="medical advice base on the patient",
    dependencies=TripContext,
    output_model= FlightPlan,
    model="openai:gpt-4o",
    max_concurrency=10,
    max_token=1000,
    temperature=0.5,
    system_prompt=(
        "You are a triaged assistant helping patients."
        "Provide clear advice and assess urgency."
        "Always mention the patient's name whe available"
    ),
    capabilities=[Thinking(effort="high"), WebSearch()],
    instructions="asdsadsadsaad"
)


hotel = Agent(
    name="hotel",
    description="medical advice base on the patient",
    dependencies=TripContext,
    output_model= HotelOption,
    model="openai:gpt-4o",
    max_concurrency=10,
    max_token=1000,
    temperature=0.5,
    system_prompt=(
        "You are a triaged assistant helping patients."
        "Provide clear advice and assess urgency."
        "Always mention the patient's name whe available"
    ),
    capabilities=[Thinking(effort="high"), WebSearch()],
    instructions="asdsadsadsaad"
)


activities = Agent(
    name="activities",
    description="medical advice base on the patient",
    dependencies=TripContext,
    output_model= Activities,
    model="openai:gpt-4o",
    max_concurrency=10,
    max_token=1000,
    temperature=0.5,
    system_prompt=(
        "You are a triaged assistant helping patients."
        "Provide clear advice and assess urgency."
        "Always mention the patient's name whe available"
    ),
    capabilities=[Thinking(effort="high"), WebSearch()],
    instructions="asdsadsadsaad"
)