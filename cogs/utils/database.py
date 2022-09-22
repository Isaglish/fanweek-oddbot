"""
Just an extension to make coding a little easier for handling MongoDB databases.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Any

import motor.motor_asyncio


__all__ = (
    'Database',
)


class Database:

    __slots__ = "client", "database", "collection"

    def __init__(self, config: dict[str, Any], database: str, collection: str) -> None:
        self.client = motor.motor_asyncio.AsyncIOMotorClient(config["mongodb_api_token"])
        self.database = self.client[database]
        self.collection = self.database[collection]


    async def find(self, post: dict[str, Any]) -> list[dict[str, Any]]:
        documents = self.collection.find(post)
        results = [document for document in await documents.to_list(length=1000)]
        return results

        
    async def find_one(self, post: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.find_one(post)
        return result


    async def insert_one(self, post: dict[str, Any]) -> None:
        await self.collection.insert_one(post)


    async def delete_one(self, post: dict[str, Any]) -> None:
        await self.collection.delete_one(post)

    
    async def delete_many(self, post: dict[str, Any]) -> None:
        await self.collection.delete_many(post)