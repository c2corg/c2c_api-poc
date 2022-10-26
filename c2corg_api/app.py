from flask import Flask
from flask_camp import RestApi

from c2corg_api import hooks
from c2corg_api.cooker import cooker

from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view
from c2corg_api.views.discourse import login_url as discourse_login_url_view

from c2corg_api.legacy.views.profiles import ProfilesView, ProfileView
from c2corg_api.legacy.views.users import account as account_view
from c2corg_api.legacy.views.users import block as block_view
from c2corg_api.legacy.views.users import unblock as unblock_view
from c2corg_api.legacy.views.users import follow as follow_view
from c2corg_api.legacy.views.users import unfollow as unfollow_view
from c2corg_api.legacy.views.users import login as login_view
from c2corg_api.legacy.views.users import logout as logout_view
from c2corg_api.legacy.views.users import preferences as preferences_view
from c2corg_api.legacy.views.users import request_password_change as request_password_change_view
from c2corg_api.legacy.views.users import register as register_view
from c2corg_api.legacy.views.users import update_preferred_language as update_preferred_language_view
from c2corg_api.legacy.views.users import validate_change_email as validate_change_email_view
from c2corg_api.legacy.views.users import validate_new_password as validate_new_password_view
from c2corg_api.legacy.views.users import validate_register_email as validate_register_email_view


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
        }
    )

    app.config.from_prefixed_env()
    app.config.from_mapping(config)

    api = RestApi(
        app=app,
        cooker=cooker,
        schemas_directory="c2corg_api/schemas",
        user_schema="user.json",
        on_user_creation=hooks.on_user_creation,
        on_user_validation=hooks.on_user_validation,
        on_user_update=hooks.on_user_update,
        on_user_block=hooks.on_user_block,
        before_document_save=hooks.before_document_save,
        update_search_query=hooks.update_search_query,
        url_prefix="/v7",
    )

    api.add_modules(app, health_view, cooker_view)
    api.add_modules(app, discourse_login_url_view)

    # define v6 interface
    api.add_modules(app, health_view, cooker_view, url_prefix="")
    api.add_modules(
        app,
        register_view,
        validate_register_email_view,
        validate_change_email_view,
        request_password_change_view,
        validate_new_password_view,
        url_prefix="",
    )
    api.add_modules(
        app,
        login_view,
        logout_view,
        account_view,
        update_preferred_language_view,
        preferences_view,
        follow_view,
        unfollow_view,
        url_prefix="",
    )
    api.add_modules(
        app,
        block_view,
        unblock_view,
        url_prefix="",
    )

    api.add_modules(app, ProfilesView(), ProfileView(), url_prefix="")

    return app, api
