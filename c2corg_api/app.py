import re

from flask import Flask, request, current_app
from flask_camp import RestApi, current_api
from flask_camp.models import Document, BaseModel, User
from sqlalchemy import Column, ForeignKey, Integer, delete, select
from sqlalchemy.orm import relationship
from werkzeug.exceptions import BadRequest

from c2corg_api.models import USERPROFILE_TYPE
from c2corg_api.search import DocumentSearch
from c2corg_api.security.discourse_client import get_discourse_client

from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view
from c2corg_api.views.discourse import login_url as discourse_login_url_view

from c2corg_api.legacy.views.users import login as login_view
from c2corg_api.legacy.views.users import logout as logout_view
from c2corg_api.legacy.views.users import request_password_change as request_password_change_view
from c2corg_api.legacy.views.users import register as register_view
from c2corg_api.legacy.views.users import validate_new_password as validate_new_password_view
from c2corg_api.legacy.views.users import validate_register_email as validate_register_email_view


# https://github.com/discourse/discourse/blob/master/app/models/username_validator.rb
def check_user_name(value):
    if len(value) < 3:
        raise BadRequest("Shorter than minimum length 3")
    if len(value) > 25:
        raise BadRequest("Longer than maximum length 25")
    if re.search(r"[^\w.-]", value):
        raise BadRequest("Contain invalid character(s)")
    if re.match(r"\W", value[0]):
        raise BadRequest("First character is invalid")
    if re.match(r"[^A-Za-z0-9]", value[-1]):
        raise BadRequest("Last character is invalid")
    if re.search(r"[-_\.]{2,}", value):
        raise BadRequest("Contains consecutive special characters")
    if re.search((r"\.(js|json|css|htm|html|xml|jpg|jpeg|png|gif|bmp|ico|tif|tiff|woff)$"), value):
        raise BadRequest("Ended by confusing suffix")


# Make the link between the user and the profile page in DB
class ProfilePageLink(BaseModel):
    id = Column(Integer, primary_key=True)

    document_id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    document = relationship(Document, cascade="all,delete")

    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    user = relationship(User, cascade="all,delete")


def before_user_creation(user, body=None):
    # TODO legacy : remove body parameter
    body = body if body is not None else request.get_json()

    lang = body.get("lang", "fr")
    user.ui_preferences = {"lang": lang}

    check_user_name(user.name)

    # create the profile page. This function adds the page in the session
    data = {"type": USERPROFILE_TYPE, "locales": {"fr": {"title": user.name}}}

    user_page = Document.create(comment="Creation of user page", data=data, author=user)
    current_api.database.session.add(ProfilePageLink(document=user_page, user=user))


def before_document_save(document):
    if document.last_version is None:  # document as been merged
        delete(DocumentSearch).where(DocumentSearch.id == document.id)
        return

    version = document.last_version

    search_item = DocumentSearch.get(id=document.id)
    if search_item is None:  # means the document is not yet created
        search_item = DocumentSearch(id=document.id)
        current_api.database.session.add(search_item)

    search_item.document_type = version.data.get("type")


def on_email_validation(user, sync_sso=True):
    query = select(ProfilePageLink.document_id).where(ProfilePageLink.user_id == user.id)
    result = current_api.database.session.execute(query)
    document_id = list(result)[0][0]
    profile_document = Document.get(id=document_id)

    before_document_save(profile_document)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


def cooker(document, get_document):
    document["legacy"] = {}


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
        before_user_creation=before_user_creation,
        before_document_save=before_document_save,
        on_email_validation=on_email_validation,
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
        request_password_change_view,
        validate_new_password_view,
        url_prefix="",
    )
    api.add_modules(
        app,
        login_view,
        logout_view,
        url_prefix="",
    )

    return app, api
