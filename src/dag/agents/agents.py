import yaml
from pydantic_ai import Agent

# from .tools import get_weather, document_tools, write_tools
from pydantic_ai.exceptions import (
    ModelRateLimitError,
    ModelServerError,
    ModelUnavailableError,
)
from pydantic_ai.models.fallback import FallbackModel

from ..services.travel_planner import TripState
from .schemas import Activities, DestinationOutput, FlightPlan, HotelOption

# from ..security.permissions import Permission
# from .tools import get_weather

with open("agents.yml") as f:
    configs = yaml.safe_load(f)


destination = Agent.from_spec(
    configs["destination"],
    model=FallbackModel(
        configs["destination"].model,
        configs["destination"].fallback_models,
        fallback_on=(
            ModelRateLimitError,
            ModelUnavailableError,
            ModelServerError,
        ),
    ),
    deps_type=TripState,
    output_type=DestinationOutput,
    # tools=[get_weather],
    # toolsets=[
    #     lambda ctx: document_tools
    #     if ctx.deps.principal.can(Permission.DOCUMENT_READ)
    #     else None,
    #     lambda ctx: write_tools
    #     if ctx.deps.principal.can(Permission.DOCUMENT_WRITE)
    #     else None,
    # ],
)


flight = Agent.from_spec(
    configs["flight"],
    model=FallbackModel(
        configs["flight"].model,
        configs["flight"].fallback_models,
        fallback_on=(
            ModelRateLimitError,
            ModelUnavailableError,
            ModelServerError,
        ),
    ),
    deps_type=TripState,
    output_type=FlightPlan,
)


hotel = Agent.from_spec(
    configs["hotel"],
    model=FallbackModel(
        configs["hotel"].model,
        configs["hotel"].fallback_models,
        fallback_on=(
            ModelRateLimitError,
            ModelUnavailableError,
            ModelServerError,
        ),
    ),
    deps_type=TripState,
    output_type=HotelOption,
)


activities = Agent.from_spec(
    configs["activities"],
    model=FallbackModel(
        configs["activities"].model,
        configs["activities"].fallback_models,
        fallback_on=(
            ModelRateLimitError,
            ModelUnavailableError,
            ModelServerError,
        ),
    ),
    deps_type=TripState,
    output_type=Activities,
)
