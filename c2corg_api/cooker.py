from flask import request

from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE
from c2corg_api.views.markdown import cook as markdown_cooker


def cooker(document, get_document):
    data = document["data"]

    document["cooked_data"] = {"locales": {lang: markdown_cooker(locale) for lang, locale in data["locales"].items()}}

    locales = [locale | {"version": 0} for locale in data["locales"].values()]

    document["legacy"] = {
        "locales": locales,
        "available_langs": [locale["lang"] for locale in locales],
        "document_id": document["id"],
        "protected": document["protected"],
        "type": data["type"],
        "version": 0,  # no equivalent ?
        "associations": [],
    }

    if data["type"] == AREA_TYPE:
        pass

    elif data["type"] == USERPROFILE_TYPE:
        document["legacy"] |= {
            "areas": data["areas"],
            "name": data["name"],
            "geometry": data["geometry"] | {"version": 0},
            "forum_username": data["name"],
        }
