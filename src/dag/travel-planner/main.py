import asyncio
from dataclasses import dataclass

from dotenv import load_dotenv

import logging
import logfire
from .services.travel_planner import TravelPlanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("travel_planner")

logfire.configure()
logfire.instrument_pydantic_ai()

load_dotenv()

@dataclass
class TravelDeps:
    user_name: str
    origin_city: str
    
async def main():
    deps = TravelDeps(user_name="John", origin_city="Berlin")
    planner = TravelPlanner(deps=deps)
    await planner.plan_trip("I want a rainy city trip within Europe. I love towers")

if __name__ == "__main__":
    asyncio.run(main())
    
 