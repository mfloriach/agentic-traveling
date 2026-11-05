from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel

from ..workflows.travel_planner import TravelDeps
from .hooks import acl
from .schemas import ActivitiesOutput, DestinationOutput, FlightOutput, HotelOutput
from .tools import get_weather


def build_agent_destination(
    file_path: Path, mock_model: FunctionModel | None = None
) -> Agent[TravelDeps, DestinationOutput]:
    model = mock_model

    return Agent.from_file(
        str(file_path),
        # model=FallbackModel(
        #     configs["flight"]["model"],
        #     *configs["flight"]["fallback_models"],
        #     fallback_on=(
        #         ModelRateLimitError,
        #         ModelUnavailableError,
        #         ModelServerError,
        #     ),
        # ),
        model=model,
        deps_type=TravelDeps,
        output_type=DestinationOutput,
        tools=[get_weather],
        capabilities=[acl],
    )


def build_agent_flight(
    file_path: Path, mock_model: FunctionModel | None = None
) -> Agent[TravelDeps, FlightOutput]:
    model = mock_model

    return Agent.from_file(
        str(file_path),
        # model=FallbackModel(
        #     configs["flight"]["model"],
        #     *configs["flight"]["fallback_models"],
        #     fallback_on=(
        #         ModelRateLimitError,
        #         ModelUnavailableError,
        #         ModelServerError,
        #     ),
        # ),
        model=model,
        deps_type=TravelDeps,
        output_type=FlightOutput,
        capabilities=[acl],
    )


def build_agent_hotel(
    file_path: Path, mock_model: FunctionModel | None = None
) -> Agent[TravelDeps, HotelOutput]:
    model = mock_model

    return Agent.from_file(
        str(file_path),
        # model=FallbackModel(
        #     configs["hotel"]["model"],
        #     *configs["hotel"]["fallback_models"],
        #     fallback_on=(
        #         ModelRateLimitError,
        #         ModelUnavailableError,
        #         ModelServerError,
        #     ),
        # ),
        model=model,
        deps_type=TravelDeps,
        output_type=HotelOutput,
        capabilities=[acl],
    )


def build_agent_activities(
    file_path: Path, mock_model: FunctionModel | None = None
) -> Agent[TravelDeps, ActivitiesOutput]:
    model = mock_model

    return Agent.from_file(
        str(file_path),
        # model=FallbackModel(
        #     configs["activities"]["model"],
        #     *configs["activities"]["fallback_models"],
        #     fallback_on=(
        #         ModelRateLimitError,
        #         ModelUnavailableError,
        #         ModelServerError,
        #     ),
        # ),
        model=model,
        deps_type=TravelDeps,
        output_type=ActivitiesOutput,
        capabilities=[acl],
    )
