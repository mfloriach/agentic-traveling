import uuid

import pybreaker
from pydantic_ai import RunContext

from src.database import Travel

from ..workflows.planner.travel_planner import TravelDeps
from ..workflows.travel_info import TravelInfo

db_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, exclude=[ValueError]
)


@db_breaker
async def get_weather(
    ctx: RunContext[TravelDeps], latitude: float, longitude: float
) -> str:
    """Get current weather for coordinates."""

    params: dict[str, float | str] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
        "temperature_unit": "fahrenheit",
    }

    try:
        response = await ctx.deps.wheather.get("/v1/forecast", params=params)
    except pybreaker.CircuitBreakerError as e:
        raise e  # TODO: concretee aerror
    finally:
        await ctx.deps.wheather.close()

    data = response["current"]
    return (
        f"Temperature: {data['temperature_2m']}F, Wind: {data['wind_speed_10m']} km/h"
    )


async def get_travel_by_id(
    ctx: RunContext[TravelInfo], travel_id: uuid.UUID, user_id: uuid.UUID
) -> Travel | None:
    """Get current weather for coordinates."""

    return await ctx.deps.database.get_travel(user_id=user_id, travel_id=travel_id)
