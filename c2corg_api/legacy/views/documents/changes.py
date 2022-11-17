from flask import request
from flask_camp import allow

# from flask_camp.models import Document
from flask_camp.views.content import versions as versions_view
from c2corg_api.legacy.converter import convert_to_legacy_doc

from werkzeug.exceptions import BadRequest

rule = "/documents/changes"


@allow("anonymous")
def get():

    token = request.args.get("token")

    if token is not None:
        try:
            token = int(token)
        except ValueError as e:
            raise BadRequest() from e

    response = versions_view.get()
    response.data["pagination_token"] = "wont-be-implemented"
    response.data["feed"] = []

    for v in response.data.pop("versions"):
        document = convert_to_legacy_doc(v)
        if document["type"] not in ("u", "o"):
            response.data["feed"].append({"document": document})

    for version in response.data["feed"]:
        print(version)

    return response
