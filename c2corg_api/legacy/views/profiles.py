from flask import request
from flask_camp import allow
from flask_camp.views.content import documents


rule = "/profiles"


@allow("authenticated", allow_blocked=True)
def get():
    result = documents.get()

    result["documents"] = [document["legacy"] for document in result["documents"]]

    return result
