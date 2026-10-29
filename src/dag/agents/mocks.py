import json

from pydantic_ai.messages import ModelResponse, TextPart


def mock_hotel(messages, info):
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "name": "Hotel Example",
                        "location": "Near Taipei Airport",
                        "price_per_night": 100,
                        "stars": 12,
                    }
                )
            )
        ]
    )


def mock_destination(messages, info):
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "destination": "Taipei",
                    }
                )
            )
        ]
    )


def mock_flight(messages, info):
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "from_city": "Taipe",
                        "to_city": "Barcelona",
                        "arrivla_time": "12pm",
                    }
                )
            )
        ]
    )


def mock_activities(messages, info):
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "top_activities": ["tapioca"],
                    }
                )
            )
        ]
    )
