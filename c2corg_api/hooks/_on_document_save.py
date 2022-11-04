from flask_camp.models import Document, DocumentVersion
from flask_login import current_user
from sqlalchemy import delete
from werkzeug.exceptions import BadRequest, Forbidden

from c2corg_api.hooks._tools import get_user_id_from_profile_id
from c2corg_api.models import USERPROFILE_TYPE, AREA_TYPE, ARTICLE_TYPE, WAYPOINT_TYPE
from c2corg_api.schemas import schema_validator
from c2corg_api.search import DocumentSearch, update_document_search_table


def on_document_save(document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
    if new_version is None:  # document as been merged
        delete(DocumentSearch).where(DocumentSearch.id == document.id)
        return

    document_type = new_version.data["type"]

    if document_type not in [USERPROFILE_TYPE, AREA_TYPE, ARTICLE_TYPE, WAYPOINT_TYPE]:
        raise BadRequest(f"Unknow document type: {document_type}")

    if old_version is None:  # it's a creation
        if document_type == USERPROFILE_TYPE:
            raise BadRequest("Profile page can't be created without an user")

        if document_type == ARTICLE_TYPE:
            new_version.data |= {"author": {"user_id": current_user.id}}

    schema_validator.validate(new_version.data, f"{document_type}.json")

    if old_version is not None and new_version is not None:

        if old_version.data["type"] != new_version.data["type"]:
            raise BadRequest("type property can't be changed")

        if document_type == USERPROFILE_TYPE:
            user_id = get_user_id_from_profile_id(document.id)
            if user_id != current_user.id:
                if not current_user.is_moderator:
                    raise Forbidden()

        elif document_type == ARTICLE_TYPE:
            if old_version.data["author"]["user_id"] != new_version.data["author"]["user_id"]:
                if not current_user.is_moderator:
                    raise Forbidden("You are not allowed to change author")

            articles_types = (old_version.data["article_type"], new_version.data["article_type"])

            if articles_types == ("collab", "personal"):  # from collab to personal
                if not current_user.is_moderator:
                    raise BadRequest("Article type cannot be changed for collaborative articles")
            elif articles_types == ("personal", "collab"):  # from personal to collab
                if new_version.data["author"]["user_id"] != current_user.id:
                    raise Forbidden("You are not allowed to change article type")

            if new_version.data["article_type"] == "personal":
                if new_version.data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
                    raise Forbidden("You are not allowed to edit this article")

    update_document_search_table(document)
