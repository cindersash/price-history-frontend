import logging
import os
import uuid
from email.utils import parseaddr
from typing import Optional, List

import bcrypt
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

LOG = logging.getLogger(__name__)

DATABASE_NAME = "price_history_users"

# Users collection fields
USER_ID_FIELD = "id"
USER_EMAIL_FIELD = "email"
USER_NAME_FIELD = "name"
USER_PASSWORD_FIELD = "password"

# Favorites collection fields
FAVORITES_USER_ID_FIELD = "user_id"
FAVORITES_PRODUCT_ID_FIELD = "product_id"


class Users:
    def __init__(self, database: Database = None):
        # If no database provided, connect to one
        if database is None:
            username = os.environ.get("USERS_USER")
            password = os.environ.get("USERS_PASSWORD")
            host = os.environ.get("MONGO_HOST")
            self.client = MongoClient(
                f"mongodb+srv://{username}:{password}@{host}/{DATABASE_NAME}" f"?retryWrites=true&w=majority"
            )

            database: Database = self.client[DATABASE_NAME]

        # Set up database and collection variables
        self.database = database

        # Users collection
        self.users_collection: Collection = self.database["users"]
        self.users_collection.create_index([(USER_ID_FIELD, pymongo.ASCENDING)], unique=True)
        self.users_collection.create_index([(USER_EMAIL_FIELD, pymongo.ASCENDING)], unique=True)

        # Favorites collection
        self.favorites_collection: Collection = self.database["favorites"]
        self.favorites_collection.create_index(
            [(FAVORITES_USER_ID_FIELD, pymongo.ASCENDING), (FAVORITES_PRODUCT_ID_FIELD, pymongo.ASCENDING)], unique=True
        )

    def get_user_name(self, user_email: str) -> Optional[str]:
        if user_email is None:
            return None

        user_document = self.users_collection.find_one({USER_EMAIL_FIELD: user_email})
        if user_document is None:
            return None

        return user_document[USER_NAME_FIELD]

    def get_user_id(self, user_email: str) -> Optional[str]:
        user_document = self.users_collection.find_one({USER_EMAIL_FIELD: user_email})
        if user_document:
            return user_document[USER_ID_FIELD]
        else:
            return None

    def create_user(self, user_name: str, user_email: str, password: str):
        """
        Creates a new user with the given information.
        This method ensures the given email address is valid and that an existing user does not already exist.

        Args:
            user_name: the name of the user
            user_email: the email of the user
            password: the password for the new account

        Raises:
            ValueError: if any checks fail.
        """
        # Ensure the email is actually a valid email address
        parsed_email = parseaddr(user_email)
        if "@" not in parsed_email[1]:
            LOG.error(f"User email {user_email} invalid!")
            raise ValueError(f"User email {user_email} invalid!")

        # Ensure an existing user does not already exist
        existing_user = self.get_user_id(user_email)
        if existing_user:
            LOG.warning(f"User already exists with email {user_email}. Not creating.")
            raise ValueError(f"User already exists with email {user_email}. Not creating.")

        user_password_hash = self._generate_user_password_hash(password)

        # UUID should produce a unique identifier for us
        user_id = str(uuid.uuid4())

        self.users_collection.insert_one(
            {
                USER_ID_FIELD: user_id,
                USER_EMAIL_FIELD: user_email,
                USER_NAME_FIELD: user_name,
                USER_PASSWORD_FIELD: user_password_hash,
            }
        )

    def user_auth(self, user_email: str, password_guess: str) -> bool:
        """
        Attempts to authenticate the given user with the given password.

        Args:
            user_email: the user email
            password_guess: the password provided for the user

        Returns:
            True if the password is correct, False otherwise
        """
        # First, check that the user exists
        user_id = self.get_user_id(user_email)
        if user_id is None:
            return False

        # If the user exists, check that the password hash matches
        user_password_hash = self._get_user_password_hash(user_id)
        return self._check_user_password(password_guess, user_password_hash)

    def get_favorites(self, user_id: str) -> List[int]:
        """
        Get the favorites for a user.

        Args:
            user_id: The user ID

        Returns:
            A list of product IDs
        """
        documents = self.favorites_collection.find({FAVORITES_USER_ID_FIELD: user_id})
        favorites = []
        for document in documents:
            favorites.append(document[FAVORITES_PRODUCT_ID_FIELD])
        return favorites

    def toggle_favorite(self, user_id: str, product_id: str):
        """
        Toggles the favorite status of the given product for the given user.

        Args:
            user_id: The user ID
            product_id: The product ID
        """
        if not self._user_exists(user_id):
            raise ValueError(f"User {user_id} does not exist!")

        favorite_dict = {FAVORITES_USER_ID_FIELD: user_id, FAVORITES_PRODUCT_ID_FIELD: product_id}
        document = self.favorites_collection.find_one(filter=favorite_dict)
        if document:
            LOG.info(f"Un-favoriting product {product_id} for user {user_id}")
        else:
            LOG.info(f"Favoriting product {product_id} for user {user_id}")
            self.favorites_collection.insert_one(favorite_dict)

    def _user_exists(self, user_id: str) -> bool:
        user_document = self.users_collection.find_one(filter={USER_ID_FIELD: user_id})
        if user_document:
            return True
        else:
            return False

    def _get_user_password_hash(self, user_id: str) -> str:
        return self.users_collection.find_one({USER_ID_FIELD: user_id})[USER_PASSWORD_FIELD]

    @staticmethod
    def _generate_user_password_hash(user_password: str) -> str:
        # Hash a password for the first time
        #   (Using bcrypt, the salt is saved into the hash itself)
        return bcrypt.hashpw(user_password.encode("utf8"), bcrypt.gensalt()).decode("utf8")

    @staticmethod
    def _check_user_password(password_guess: str, user_password_hash: str) -> bool:
        # Check hashed password. Using bcrypt, the salt is saved into the hash itself
        return bcrypt.checkpw(password_guess.encode("utf8"), user_password_hash.encode("utf8"))
