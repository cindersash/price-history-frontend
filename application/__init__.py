import logging
import os

from flask import Flask

from application.constants.app_constants import DATABASE_CONFIG_KEY
from application.data.custom_json_encoder import CustomJsonEncoder
from application.data.dao import ApplicationDao
from application.routes.html_routes import HTML_BLUEPRINT

logging.basicConfig(level=logging.INFO)
logging.getLogger("engineio.server").setLevel(logging.WARNING)
logging.getLogger("socketio.server").setLevel(logging.WARNING)


def create_flask_app() -> Flask:
    # Create the flask app
    app = Flask(__name__)

    # Set custom JSON encoder to handle MongoDB ObjectID
    app.json_encoder = CustomJsonEncoder

    # Create a DAO and add it to the flask app config for access by the blueprints
    app.config[DATABASE_CONFIG_KEY] = ApplicationDao()

    # This must be set in the environment as a secret
    app.secret_key = os.environ["SECRET_KEY"]

    # Register blueprints to add routes to the app
    app.register_blueprint(HTML_BLUEPRINT)

    return app
