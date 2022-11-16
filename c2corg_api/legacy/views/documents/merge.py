from flask import request
from flask_camp import allow, current_api
from flask_camp.models import Document
from flask_camp.views.content import merge as merge_view
from werkzeug.exceptions import BadRequest

rule = "/documents/merge"


@allow("moderator")
def post():
    data = request.get_json()

    if "source_document_id" not in data or data["source_document_id"] <= 0:
        raise BadRequest("document_id can't be negative")

    if "target_document_id" not in data or data["target_document_id"] <= 0:
        raise BadRequest("document_id can't be negative")

    data |= {"comment": "no comment for revert in v6"}

    request._cached_json = (data, data)

    return merge_view.put()
