"""
Just an extension to make coding a little easier for handling MongoDB databases.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import json
from typing import Any

import pymongo
from pymongo import MongoClient


__all__ = (
    'Database',
)


class Database:

    __slots__ = "cluster", "database", "collection"

    def __init__(self, config: dict[str, Any], database: str, collection: str) -> None:
        self.cluster = MongoClient(config["mongodb_api_token"])
        self.database = self.cluster[database]
        self.collection = self.database[collection]


    def find(self, query: dict[str, Any]) -> pymongo.cursor.Cursor:
        results = self.collection.find(query)
        return results

        
    def find_one(self, query: dict[str, Any]) -> dict[str, Any]:
        result = self.collection.find_one(query)
        return result


    def find_with_key(self, query: dict[str, Any], key: str) -> list[Any]:
        result = self.collection.find(query)
        results = [r[key] for r in result]
        return results


    def insert_one(self, post: dict[str, Any]) -> None:
        self.collection.insert_one(post)


    def delete_one(self, post: dict[str, Any]) -> None:
        self.collection.delete_one(post)

    
    def delete_many(self, post: dict[str, Any]) -> None:
        self.collection.delete_many(post)