import re

from flask import Flask, request
from flask_camp import RestApi, current_api
from flask_camp.models import Document, BaseModel, User
from sqlalchemy import Column, ForeignKey, Integer, delete
from sqlalchemy.orm import relationship
from werkzeug.exceptions import BadRequest

from c2corg_api.models import USERPROFILE_TYPE
from c2corg_api.search import DocumentSearch

from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view

from c2corg_api.views.legacy.users import register as register_view
from c2corg_api.views.legacy.users import validate_register_email as validate_register_email_view


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
    user_page = Document.create(comment="Creation of user page", data={"type": USERPROFILE_TYPE}, author=user)
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


def create_app(**config):
    app = Flask(__name__, static_folder=None)

    app.config.from_mapping(config)
    app.config.update({"SQLALCHEMY_TRACK_MODIFICATIONS": False})

    api = RestApi(
        app=app,
        before_user_creation=before_user_creation,
        before_document_save=before_document_save,
        url_prefix="/v7",
    )

    api.add_modules(app, health_view, cooker_view)

    # define v6 interface
    api.add_modules(app, health_view, cooker_view, url_prefix="")
    api.add_modules(app, register_view, validate_register_email_view, url_prefix="")

    return app, api
