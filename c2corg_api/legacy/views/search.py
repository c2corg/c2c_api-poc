from flask import request
from flask_camp import allow
from flask_login import current_user
from werkzeug.datastructures import ImmutableMultiDict

from c2corg_api.views import search
from c2corg_api.legacy.converter import convert_to_legacy_doc
from c2corg_api.legacy.models.document import legacy_types

rule = "/search"


@allow("anonymous", "authenticated")
def get():

    if "t" in request.args.to_dict():
        http_args = request.args.to_dict()
        types = http_args.pop("t")
        http_args["types"] = ",".join(legacy_types[v6_type] for v6_type in types.split(","))
        request.args = ImmutableMultiDict(http_args)

    result = search.get()

    legacy_result = {
        f"{document_type}s": {
            "total": 666,
            "documents": [
                convert_to_legacy_doc(document, preferred_lang=request.args.get("pl")) for document in documents
            ],
        }
        for document_type, documents in result.items()
    }

    if "profiles" in legacy_result:
        if not current_user.is_authenticated:
            del legacy_result["profiles"]
        else:
            legacy_result["users"] = legacy_result["profiles"]

    return legacy_result
