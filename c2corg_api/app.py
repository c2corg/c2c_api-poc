from flask import Flask
from flask_camp import RestApi

from c2corg_api import hooks
from c2corg_api.legacy.core import add_legacy_modules
from c2corg_api.models import models
from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view
from c2corg_api.views.sitemap import Sitemaps as SitemapsView
from c2corg_api.views.discourse import login_url as discourse_login_url_view


def cooker(document, get_document):
    document_type = document["data"]["type"]
    models[document_type].cook(document, get_document)

    # import json
    # print(json.dumps(document, indent=4))


def create_app(**config):
    app = Flask(__name__, static_folder=None)

    # defaulting
    app.config.update(
        {
            "url.timeout": 666,
            "C2C_DISCOURSE_URL": "https://forum.camptocamp.org",
            "C2C_DISCOURSE_PUBLIC_URL": "https://forum.camptocamp.org",
            "C2C_DISCOURSE_API_KEY": "4647c0d98e8beb793da099ff103b9793d8d4f94fff7cdd52d58391c6fa025845",
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
        update_search_query=hooks.update_search_query,
        url_prefix="/v7",
    )

    api.after_get_document(hooks.after_get_document)
    api.before_create_user(hooks.before_create_user)
    api.before_validate_user(hooks.before_validate_user)
    api.before_update_user(hooks.before_update_user)
    api.before_block_user(hooks.before_block_user)
    api.before_update_document(hooks.before_update_document)
    api.before_create_document(hooks.before_create_document)
    api.before_merge_documents(hooks.before_merge_documents)

    api.add_views(app, health_view, cooker_view)
    api.add_views(app, discourse_login_url_view)
    api.add_views(app, SitemapsView())

    add_legacy_modules(app, api)  # TODO rename to add_legacy_views

    return app, api
