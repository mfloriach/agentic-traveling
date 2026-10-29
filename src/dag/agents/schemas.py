from pydantic import BaseModel


class DestinationOutput(BaseModel):
    destination: str


class FlightPlan(BaseModel):
    from_city: str
    to_city: str
    arrival_time: str


class HotelOption(BaseModel):
    name: str
    location: str
    price_per_night_usd: int
    stars: int


class Activities(BaseModel):
    top_activities: list[str]
