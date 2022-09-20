"""
Just an extension to make coding a little easier for handling MongoDB databases.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from pymongo import MongoClient

from .config import Config


class Database:

    def __init__(self, database: str, collection: str):
        self.cluster = MongoClient(Config.MONGODB_API_TOKEN)
        self.database = self.cluster[database]
        self.collection = self.database[collection]


    def find(self, query: dict):
        results = self.collection.find(query)
        return results

        
    def find_one(self, query: dict):
        result = self.collection.find_one(query)
        return result


    def find_with_key(self, query: dict, key: str):
        result = self.collection.find(query)
        results = [r[key] for r in result]
        return results


    def insert_one(self, post: dict):
        self.collection.insert_one(post)


    def delete_one(self, post: dict):
        self.collection.delete_one(post)

    
    def delete_many(self, post: dict):
        self.collection.delete_many(post)