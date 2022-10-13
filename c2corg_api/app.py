from flask import Flask
from flask_camp import RestApi

from c2corg_api.views import health as health_view


def create_app(**config):
    app = Flask(__name__, static_folder=None)

    app.config.from_mapping(config)
    app.config.update({"SQLALCHEMY_TRACK_MODIFICATIONS": False})

    api = RestApi(app=app)
    api.add_modules(app, health_view)

    return app, api
