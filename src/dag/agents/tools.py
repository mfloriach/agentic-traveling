import pybreaker

from ..services.travel_planner import TripState

# from ..security.permissions import Permission
# from pydantic_ai import FunctionToolset, RunContext

db_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, exclude=[ValueError]
)


@db_breaker
async def get_weather(ctx: TripState[None], latitude: float, longitude: float) -> str:
    """Get current weather for coordinates."""

    params: dict[str, float | str] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
        "temperature_unit": "fahrenheit",
    }

    try:
        response = await ctx.services.wheather.get("/v1/forecast", params=params)
    except pybreaker.CircuitBreakerError as e:
        raise e  # TODO: concretee aerror
    finally:
        await ctx.services.close()

    data = response.json()["current"]
    return (
        f"Temperature: {data['temperature_2m']}F, Wind: {data['wind_speed_10m']} km/h"
    )


# document_tools = FunctionToolset[TripContext]()


# @document_tools.tool
# async def search_documents(
#     ctx: RunContext[TripContext],
#     query: str,
# ) -> list[dict]:
#     """Search documents the current user can read."""

#     ctx.deps.authz.require(
#         ctx.deps.principal,
#         Permission.DOCUMENT_READ,
#     )

#     await ctx.deps.audit_log.record(
#         actor_id=ctx.deps.principal.user_id,
#         action="documents.search",
#     )

#     # The repository must apply any resource-level filters too.
#     return await ctx.deps.document_repository.search(
#         query=query,
#         principal=ctx.deps.principal,
#     )


# write_tools = FunctionToolset[TripContext]()


# @write_tools.tool
# async def update_document(
#     ctx: RunContext[TripContext],
#     document_id: str,
#     content: str,
# ) -> str:
#     """Update a document the user is authorized to edit."""

#     ctx.deps.authz.require(
#         ctx.deps.principal,
#         Permission.DOCUMENT_WRITE,
#     )

#     await ctx.deps.document_repository.update(
#         document_id=document_id,
#         content=content,
#         principal=ctx.deps.principal,
#     )

#     return "Document updated"
