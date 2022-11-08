from flask import request
from flask_camp import allow
from flask_camp.views.content import document as document_view
from werkzeug.exceptions import BadRequest

rule = "/documents/unprotect"


@allow("moderator")
def post():
    data = request.get_json()

    if data["document_id"] <= 0:
        raise BadRequest("document_id can't be negative")

    body = {"document": {"protected": False}, "comment": "v6 does not comment protections"}
    request._cached_json = (body, body)

    return document_view.put(data["document_id"])
