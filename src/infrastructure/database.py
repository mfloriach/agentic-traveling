import uuid
from dataclasses import dataclass
from datetime import datetime

import asyncpg


@dataclass
class Hotel:
    id: uuid.UUID
    name: str
    nights: int
    entry_date: datetime
    room_num: int
    price: int


@dataclass
class Flight:
    id: str
    seat_num: int
    company: str
    price: int
    date: datetime


@dataclass
class Activities:
    id: str
    seat_num: int
    title: str
    price: int
    date: datetime


@dataclass
class Travel:
    id: uuid.UUID
    user_id: uuid.UUID
    hotel: Hotel
    flight: Flight
    activities: list[Activities]


class PostgresDatabase:
    def __init__(self, url: str):
        self.url = url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(
            dsn=self.url,
            min_size=2,
            max_size=10,
            command_timeout=10,
        )

    async def get_travels(
        self,
        user_id: uuid.UUID,
    ) -> list[Travel]:
        async with self._get_pool().acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, destination, start_date,
                       end_date, created_at
                FROM travels
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )

            return [Travel(**row) for row in rows]

    async def get_travel(
        self,
        user_id: uuid.UUID,
        travel_id: uuid.UUID,
    ) -> Travel | None:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, destination, start_date,
                       end_date, created_at
                FROM travels
                WHERE user_id = $1
                  AND id = $2
                """,
                user_id,
                travel_id,
            )

            return Travel(**row) if row else None

    def _get_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database not connected")

        return self.pool

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
