from flask_camp.models import Document, DocumentVersion
from sqlalchemy import delete
from werkzeug.exceptions import BadRequest

from c2corg_api.models import ARTICLE_TYPE, USERPROFILE_TYPE, XREPORT_TYPE, ALL_TYPES
from c2corg_api.models.article import Article
from c2corg_api.models.userprofile import UserProfile
from c2corg_api.models.xreport import Xreport
from c2corg_api.schemas import schema_validator
from c2corg_api.search import DocumentSearch, update_document_search_table


def on_document_save(document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
    if new_version is None:  # document as been merged
        delete(DocumentSearch).where(DocumentSearch.id == document.id)
        return

    document_type = new_version.data["type"]

    if document_type not in ALL_TYPES:
        raise BadRequest(f"Unknow document type: {document_type}")

    model = {
        ARTICLE_TYPE: Article,
        USERPROFILE_TYPE: UserProfile,
        XREPORT_TYPE: Xreport,
    }[document_type]

    if old_version is None:  # it's a creation
        model.on_creation(version=new_version)

    schema_validator.validate(new_version.data, f"{document_type}.json")

    if old_version is not None and new_version is not None:

        if old_version.data["type"] != new_version.data["type"]:
            raise BadRequest("type property can't be changed")

        model.on_new_version(old_version=old_version, new_version=new_version)

    update_document_search_table(document)
