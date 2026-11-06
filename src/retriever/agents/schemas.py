from pydantic import BaseModel


class DestinationOutput(BaseModel):
    destination: str


class FlightOutput(BaseModel):
    from_city: str
    to_city: str
    arrival_time: str


class HotelOutput(BaseModel):
    name: str
    location: str
    price_per_night_usd: int
    stars: int


class ActivitiesOutput(BaseModel):
    top_activities: list[str]
