from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.usage import RequestUsage

from .schemas import ActivitiesOutput, DestinationOutput, FlightOutput, HotelOutput


def mock_hotel(messages, info):
    return ModelResponse(
        model_name="openapi",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=HotelOutput(
                    name="Hotel Example",
                    location="Near Taipei Airport",
                    price_per_night_usd=100,
                    stars=12,
                ).model_dump_json()
            )
        ],
    )


def mock_destination(messages, info):
    return ModelResponse(
        model_name="google:gemini-3.8-flash",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=DestinationOutput(
                    destination="Taipei",
                ).model_dump_json()
            )
        ],
    )


def mock_flight(messages, info):
    return ModelResponse(
        model_name="openapi",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=FlightOutput(
                    from_city="Taipe",
                    to_city="Barcelona",
                    arrival_time="12pm",
                ).model_dump_json()
            )
        ],
    )


def mock_activities(messages, info):
    return ModelResponse(
        model_name="meta:muse-spark-1.3",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=ActivitiesOutput(
                    top_activities=["tapioca"],
                ).model_dump_json()
            )
        ],
    )
