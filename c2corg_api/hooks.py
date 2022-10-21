from copy import deepcopy
import re

from flask import request, current_app
from flask_camp import current_api
from flask_camp.models import Document, BaseModel, User
from sqlalchemy import Column, ForeignKey, Integer, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from werkzeug.exceptions import BadRequest

from c2corg_api.models import USERPROFILE_TYPE
from c2corg_api.security.discourse_client import get_discourse_client
from c2corg_api.search import DocumentSearch

# Make the link between the user and the profile page in DB
class ProfilePageLink(BaseModel):
    id = Column(Integer, primary_key=True)

    document_id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    document = relationship(Document, cascade="all,delete")

    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=False, unique=True)
    user = relationship(User, cascade="all,delete")


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


def get_profile_document(user):
    query = select(ProfilePageLink.document_id).where(ProfilePageLink.user_id == user.id)
    result = current_api.database.session.execute(query)
    document_id = list(result)[0][0]
    return Document.get(id=document_id)


def on_user_creation(user, body=None):
    # TODO legacy : remove body parameter
    body = body if body is not None else request.get_json()

    lang = body.get("lang", "fr")
    full_name = body.get("full_name", user.name)
    user.ui_preferences = {
        "lang": lang,
        "full_name": full_name,
        "is_profile_public": False,
        "feed": {"areas": [], "activities": [], "langs": [], "followed_only": False},
    }

    check_user_name(user.name)

    # create the profile page. This function adds the page in the session
    data = {
        "type": USERPROFILE_TYPE,
        "user_id": user.id,
        "locales": {"fr": {"title": user.name}, "en": {"title": user.name}},
    }

    user_page = Document.create(comment="Creation of user page", data=data, author=user)
    current_api.database.session.add(ProfilePageLink(document=user_page, user=user))


def on_user_validation(user, sync_sso=True):

    profile_document = get_profile_document(user)
    before_document_save(profile_document)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


def on_user_update(user, sync_sso=True):

    # as now, flask_camp does not allow to modify user name. To be discussed (maybe a modo action)
    # v6 API allows it, so we do that here
    data = request.get_json()

    if "name" in data:
        user.name = data["name"]
        check_user_name(user.name)
        try:
            current_api.database.session.flush()
        except IntegrityError as e:
            raise BadRequest("Name is already used") from e

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


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

    if search_item.document_type == USERPROFILE_TYPE:
        search_item.user_id = version.data.get("user_id")
