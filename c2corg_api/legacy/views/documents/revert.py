from flask import request
from flask_camp import allow, current_api
from flask_camp.models import Document, DocumentVersion
from flask_camp.views.content import document
from flask_login import current_user
from werkzeug.exceptions import BadRequest

rule = "/documents/revert"


@allow("moderator")
def post():
    data = request.get_json()

    if data["document_id"] <= 0:
        raise BadRequest("document_id can't be negative")

    if data["version_id"] <= 0:
        raise BadRequest("version_id can't be negative")

    doc = Document.get(id=data["document_id"])

    if doc.last_version_id == data["version_id"]:
        raise BadRequest("Version is already the latest one")

    version = DocumentVersion.get(id=data["version_id"])

    if version is None:
        raise BadRequest("Version not found")

    body = {"document": doc.as_dict(), "comment": "no comment for revert in v6"}
    body["document"]["data"] = version.data

    request._cached_json = (body, body)

    return document.post(doc.id)
