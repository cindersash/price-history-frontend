import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from application.constants.app_constants import MAX_METRICS_DOCUMENTS, MAX_METRICS_SIZE

DATABASE_NAME = "price_history_metrics"


class Metrics:
    def __init__(self, database: Database = None):
        # If no database provided, connect to one
        if database is None:
            username = os.environ.get("METRICS_USER")
            password = os.environ.get("METRICS_PASSWORD")
            host = os.environ.get("METRICS_HOST")
            self.client = MongoClient(
                f"mongodb+srv://{username}:{password}@{host}/{DATABASE_NAME}?retryWrites=true&w=majority"
            )

            database: Database = self.client[DATABASE_NAME]

        # Set up database and collection variables
        self.database = database

        list_of_collections = self.database.list_collection_names()

        if "products_search_time" not in list_of_collections:
            self.database.create_collection("products_search_time", check_exists=True, capped=True, size=MAX_METRICS_SIZE, max=MAX_METRICS_DOCUMENTS)
        if "products_price_history_time" not in list_of_collections:
            self.database.create_collection("products_price_history_time", check_exists=True, capped=True, size=MAX_METRICS_SIZE, max=MAX_METRICS_DOCUMENTS)

        self.products_search_time_collection: Collection = self.database["products_search_time"]
        self.products_price_history_time: Collection = self.database["products_price_history_time"]

    def log_products_search_time(self, search_time_ms: int, query: str):
        self.products_search_time_collection.insert_one({"search_time_ms": search_time_ms, "query": query})

    def log_products_price_history_time(self, time_ms: int, product_id: int):
        self.products_price_history_time.insert_one({"time_ms": time_ms, "product_id": product_id})
