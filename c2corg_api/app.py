from flask import Flask
from flask_camp import RestApi

from c2corg_api import hooks
from c2corg_api.cooker import cooker
from c2corg_api.legacy.core import add_legacy_modules
from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view
from c2corg_api.views.sitemap import Sitemaps as SitemapsView
from c2corg_api.views.discourse import login_url as discourse_login_url_view


def create_app(**config):
    app = Flask(__name__, static_folder=None)

    # defaulting
    app.config.update(
        {
            "url.timeout": 666,
            "discourse.url": "https://forum.demov6.camptocamp.org",
            "discourse.public_url": "https://forum.demov6.camptocamp.org",
            "discourse.api_key": "4647c0d98e8beb793da099ff103b9793d8d4f94fff7cdd52d58391c6fa025845",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "ANONYMOUS_USER_ID": "271737",
        }
    )

    app.config.from_prefixed_env()
    app.config.from_mapping(config)

    try:
        if isinstance(app.config["ANONYMOUS_USER_ID"], str):
            app.config["ANONYMOUS_USER_ID"] = int(app.config["ANONYMOUS_USER_ID"])
    except ValueError as e:
        raise ValueError("Please set a numeric value for FLASK_ANONYMOUS_USER_ID") from e

    api = RestApi(
        app=app,
        cooker=cooker,
        schemas_directory="c2corg_api/schemas",
        user_schema="user.json",
        after_get_document=hooks.after_get_document,
        on_user_creation=hooks.on_user_creation,
        on_user_validation=hooks.on_user_validation,
        on_user_update=hooks.on_user_update,
        on_user_block=hooks.on_user_block,
        on_document_save=hooks.on_document_save,
        update_search_query=hooks.update_search_query,
        url_prefix="/v7",
    )

    api.add_views(app, health_view, cooker_view)
    api.add_views(app, discourse_login_url_view)
    api.add_views(app, SitemapsView())

    add_legacy_modules(app, api)  # TODO rename to add_legacy_views

    return app, api
