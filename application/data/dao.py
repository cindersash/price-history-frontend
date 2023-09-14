import datetime
import hashlib
import logging
import os
import random
import string
from email.utils import parseaddr
from typing import Optional, List, Dict
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import bcrypt
import pymongo
from bson import ObjectId
from flask import current_app
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from application.constants.app_constants import DATE_FORMAT_STRING
from application.data.price_history import PriceHistory
from application.data.products_search import Product

DATABASE_NAME = "price_history"

LOG = logging.getLogger("DAO")


class ApplicationDao:
    def __init__(self, database: Database = None):
        # If no database provided, connect to one
        if database is None:
            username = os.environ.get("MONGO_USER")
            password = os.environ.get("MONGO_PASSWORD")
            host = os.environ.get("MONGO_HOST")
            self.client = MongoClient(
                f"mongodb+srv://{username}:{password}@{host}/{DATABASE_NAME}?retryWrites=true&w=majority"
            )

            database: Database = self.client["price_history"]

        # Set up database and collection variables
        self.database = database
        self.products_collection: Collection = self.database["products"]
        self.categories_collection: Collection = self.database["categories"]
        self.prices_collection: Collection = self.database["prices"]

        LOG.info(f"Database collections: {self.database.list_collection_names()}")

    def get_product_price_history(self, product_id: int) -> PriceHistory:
        dates = []
        prices = []

        documents = self.prices_collection.find(filter={"product_id": product_id}, sort=[("start_date", pymongo.DESCENDING)])

        for document in documents:
            dates.append(document["start_date"].strftime(DATE_FORMAT_STRING))
            prices.append(float(document["price_cents"]) / 100.0)

        # Ensure we add a data point for today based on the most recent data point
        if dates:
            dates.append(datetime.datetime.today().strftime(DATE_FORMAT_STRING))
            prices.append(prices[-1])

        return PriceHistory(dates=dates, prices=prices)

    def get_product_display_name(self, product_id: int) -> str:
        document = self.products_collection.find_one(filter={"id": product_id})

        if document:
            return document["display_name"]
        else:
            return "UNKNOWN"

    def get_products(self, search_query: str) -> List[Product]:
        products = []

        documents = self.products_collection.find({"$text": {"$search": search_query}})
        for document in documents:
            product = Product(id=document["id"], display_name=document["display_name"])
            products.append(product)

        return products
