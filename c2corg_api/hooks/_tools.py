import re
from flask_camp import current_api
from flask_camp.models import Document
from sqlalchemy import select
from werkzeug.exceptions import BadRequest

from c2corg_api.models import USERPROFILE_TYPE, AREA_TYPE, ARTICLE_TYPE, WAYPOINT_TYPE, ProfilePageLink
from c2corg_api.search import DocumentSearch


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


def get_user_id_from_profile_id(profile_id):
    query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == profile_id)
    result = current_api.database.session.execute(query)
    return list(result)[0][0]


def update_document_search_table(document, session=None):
    # TODO: on remove legacy, removes session parameters
    session = current_api.database.session if session is None else session

    new_version = document.last_version

    search_item: DocumentSearch = session.query(DocumentSearch).get(document.id)

    if search_item is None:  # means the document is not yet created
        search_item = DocumentSearch(id=document.id)
        session.add(search_item)

    search_item.available_langs = [lang for lang in new_version.data["locales"]]

    search_item.document_type = new_version.data["type"]

    if search_item.document_type == USERPROFILE_TYPE:
        search_item.user_id = new_version.data.get("user_id")
    elif search_item.document_type == ARTICLE_TYPE:
        pass
    elif search_item.document_type == WAYPOINT_TYPE:
        pass
    elif search_item.document_type == AREA_TYPE:
        pass
    else:
        raise NotImplementedError(f"Please set how to search {search_item.document_type}")
