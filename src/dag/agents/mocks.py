import json

from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.usage import RequestUsage


def mock_hotel(messages, info):
    return ModelResponse(
        model_name="openapi",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "name": "Hotel Example",
                        "location": "Near Taipei Airport",
                        "price_per_night_usd": 100,
                        "stars": 12,
                    }
                )
            )
        ],
    )


def mock_destination(messages, info):
    return ModelResponse(
        model_name="openapi",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "destination": "Taipei",
                    }
                )
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
                content=json.dumps(
                    {
                        "from_city": "Taipe",
                        "to_city": "Barcelona",
                        "arrival_time": "12pm",
                    }
                )
            )
        ],
    )


def mock_activities(messages, info):
    return ModelResponse(
        model_name="openapi",
        usage=RequestUsage(
            input_tokens=150,
            output_tokens=20,
        ),
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "top_activities": ["tapioca"],
                    }
                )
            )
        ],
    )
