from flask import Flask
from flask_camp import RestApi

from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view

from c2corg_api.views.legacy.users import register as register_view


def before_user_creation(user):
    user.ui_preferences = {"lang": "fr"}


def create_app(**config):
    app = Flask(__name__, static_folder=None)

    app.config.from_mapping(config)
    app.config.update({"SQLALCHEMY_TRACK_MODIFICATIONS": False})

    api = RestApi(
        app=app,
        before_user_creation=before_user_creation,
        url_prefix="/v7",
    )

    api.add_modules(app, health_view, cooker_view)

    # define v6 interface
    api.add_modules(app, health_view, cooker_view, url_prefix="")
    api.add_modules(app, register_view, url_prefix="")

    return app, api
