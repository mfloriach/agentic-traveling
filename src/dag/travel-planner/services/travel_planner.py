import asyncio
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel
from pydantic_ai import Agent

from ..decorators import log_agent
from ..config import load_agent_configs
from ..agents.agents import destination, flight, hotel, activities

import logfire
from ..logging import logger


class TripContext(BaseModel):
    destination: Optional[str] = None
    from_city: Optional[str] = None
    arrival_time: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_location: Optional[str] = None

@dataclass
class TravelDeps:
    user_name: str
    origin_city: str

class TravelPlanner:
    def __init__(self, deps: TravelDeps):
        self.deps = deps
        self.ctx = TripContext()
        self.config = load_agent_configs()
        
        self.destination_agent = destination
        self.flight_agent = flight
        self.hotel_agent = hotel
        self.activity_agent = activities
       
    async def handle_destination(self, user_input: str) -> None:
        result = await self.destination_agent.run(user_input, deps=self.deps)
        self.ctx.destination = result.output.destination
        print(f"Destination: {self.ctx.destination}")
        
    async def handle_flight(self, user_input: str) -> None:
        prompt = f"Plan a flight from {self.deps.origin_city} to {self.ctx.destination}"
        result = await self.flight_agent.run(prompt, deps=self.deps)
        self.ctx.from_city = result.output.from_city
        self.ctx.arrival_time = result.output.arrivla_time
        print(
            f"✈️ Flight: from {self.ctx.from_city} → {self.ctx.destination}, arriving at {self.ctx.arrival_time}"
        )
        
    async def handle_hotel(self, user_input: str) -> None:
        prompt = (
            f"Recommend a hotel in {self.ctx.destination} for a traveler arriving at {self.ctx.arrival_time}. "
            f"Prefer locations near the airport or city center."
        )
        result = await self.hotel_agent.run(prompt, deps=self.deps)
        self.ctx.hotel_name = result.output.name
        self.ctx.hotel_location = result.output.location
        print(
            f"🏨 Hotel: {self.ctx.hotel_name}, {result.output.stars}★ at ${result.output.price_per_night_usd}/night"
        )
        logfire.info(str(result.output))

    async def handle_activities(self, user_input: str) -> None:
        prompt = (
            f"Suggest activities in {self.ctx.destination} close to {self.ctx.hotel_location} "
            f"and suitable for a traveler arriving at {self.ctx.arrival_time}."
        )
        result = await self.activity_agent.run(prompt, deps=self.deps)
        print(f"🎯 Activities for {result.output.personalized_for}:")
        for a in result.output.top_activities:
            print(f"  - {a}")
            
    async def plan_trip(self, user_input: str) -> None:
        print(f"{self.deps.user_name} says: {user_input}")
        
        chain = [
            self.handle_destination,
            self.handle_flight,
            self.handle_hotel,
            self.handle_activities
        ]
        
        with logfire.span(
            "travel.plan_trip",
            origin_city=self.deps.origin_city,
        ):
        
            logger.info("trip.started")
            
            try:
                for step in chain:
                    with log_agent:
                        await step(user_input=user_input)  
                    
                logger.info("trip.completed")
            except Exception:  
                logger.exception("trip.failed")
                raise

