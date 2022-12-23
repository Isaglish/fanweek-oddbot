"""
Just an extension to make coding a little easier for handling PostgreSQL database.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Any

import asyncpg


__all__ = (
    'Database',
)


class Database:

    __slots__ = "config", "task", "pool"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config


    async def create_pool(self) -> asyncpg.Pool:
        pool = await asyncpg.create_pool(dsn=self.config["postgres_url"])
        async with pool.acquire() as connection:
            query = """CREATE TABLE IF NOT EXISTS submission (
                id SERIAL PRIMARY KEY,
                author_id BIGINT,
                guild_id BIGINT,
                game_title TEXT,
                game_url TEXT
            )"""
            await connection.execute(query)

        self.pool = pool
