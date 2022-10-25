from copy import deepcopy
import re

from flask import request, current_app
from flask_camp import current_api
from flask_camp.models import Document, BaseModel, User
from sqlalchemy import Column, ForeignKey, Integer, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from c2corg_api.models import USERPROFILE_TYPE, get_default_user_profile_data
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


def on_user_creation(user):

    check_user_name(user.name)

    assert user.id is not None, "Dev check..."

    # create the profile page. This function adds the page in the session
    data = get_default_user_profile_data(user, categories=[])
    user_page = Document.create(comment="Creation of user page", data=data, author=user)
    current_api.database.session.add(ProfilePageLink(document=user_page, user=user))


def on_user_validation(user, sync_sso=True):

    profile_document = get_profile_document(user)
    before_document_save(profile_document)

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


def on_user_update(user: User, sync_sso=True):

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

    follow = list(set(user.ui_preferences["feed"]["follow"]))
    user.ui_preferences["feed"]["follow"] = follow  # remove duplicates

    if len(follow) != 0:
        real_user_ids = [r[0] for r in current_api.database.session.query(User.id).filter(User.id.in_(follow)).all()]
        if len(follow) != len(real_user_ids):
            raise NotFound(f"{follow} {real_user_ids}")

    if sync_sso is True:  # TODO: needs forum in dev env
        get_discourse_client(current_app.config).sync_sso(user, user._email)


def on_user_block(user):

    client = get_discourse_client(current_app.config)

    if user.blocked:
        # suspend account in Discourse (suspending an account prevents a login)
        try:
            client.suspend(user.id, 99999, "account blocked by moderator")  # 99999 days = 273 years
        except Exception as e:
            current_app.logger.exception("Suspending account in Discourse failed: %d", user.id)
            raise InternalServerError("Suspending account in Discourse failed") from e
    else:
        try:
            client.unsuspend(user.id)
        except Exception as e:
            current_app.logger.exception("Unsuspending account in Discourse failed: %d", user.id)
            raise InternalServerError("Unsuspending account in Discourse failed") from e


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
