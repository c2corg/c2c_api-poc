from flask import request
from flask_camp import allow
from flask_login import current_user

from c2corg_api.models import USERPROFILE_TYPE
from c2corg_api.views import search
from c2corg_api.legacy.converter import convert_to_legacy_doc

rule = "/search"


@allow("anonymous", "authenticated")
def get():

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

    if not current_user.is_authenticated:
        del legacy_result["profiles"]
    else:
        legacy_result["users"] = legacy_result["profiles"]

    return legacy_result
