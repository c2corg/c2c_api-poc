from flask import request
from flask_camp import allow
from flask_camp.views.content import documents


rule = "/profiles"


@allow("authenticated", allow_blocked=True)
def get():
    result = documents.get()

    return {
        "total": result["count"],
        "documents": [_get_legacy_doc(document, request.args.get("pl")) for document in result["documents"]],
    }


def _get_legacy_doc(document, pl):
    result = document["legacy"]

    if pl is not None:
        locales = [locale for locale in result["locales"] if locale["lang"] == pl]
        if len(locales) == 0:
            locales = [locale for locale in result["locales"] if locale["lang"] == "fr"]  # TODO preferred lang

        result["locales"] = locales

    return result
