import json
from flask import request
from flask_camp import allow
from flask_camp.views.content import documents as documents_view, document as document_view
from werkzeug.exceptions import NotFound, BadRequest

from c2corg_api.models import USERPROFILE_TYPE


class ProfileView:
    rule = "/profiles/<int:profile_id>"

    @allow("anonymous", "authenticated")
    def get(self, profile_id):
        result = document_view.get(profile_id)

        return _get_legacy_doc(result.json["document"], lang=request.args.get("l"))  #  not optimized at all

    @allow("authenticated")
    def put(self, profile_id):
        body = request.get_json()

        new_body = _from_legacy_doc(body)

        request._cached_json = (new_body, new_body)

        result = document_view.post(profile_id)

        return result


class ProfilesView:
    rule = "/profiles"

    @allow("authenticated", allow_blocked=True)
    def get(self):
        result = documents_view.get()

        return {
            "total": result["count"],
            "documents": [
                _get_legacy_doc(document, collection_view=True, preferred_lang=request.args.get("pl"))
                for document in result["documents"]
            ],
        }

    @allow("anonymous", "authenticated")
    def post(self):
        raise NotFound()  # just for test


def _get_preferred_locale(preferred_lang, locales):
    if preferred_lang in locales:
        return locales[preferred_lang]

    langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

    for lang in langs_priority:
        if lang in locales:
            return locales[lang]

    return None  # raise ?


def _from_legacy_doc(body):

    if "document" not in body:
        raise BadRequest()

    document = {"version_id": body["document"].pop("version"), "id": body["document"].pop("document_id")}

    if isinstance(document["id"], str):
        document["id"] = int(document["id"])

    document["data"] = body["document"]
    document["data"]["locales"] = {locale["lang"]: locale for locale in document["data"]["locales"]}
    if "geometry" in document["data"]:
        document["data"]["geometry"]["geom"] = json.loads(document["data"]["geometry"]["geom"])
    else:
        document["data"]["geometry"] = {"geom": "{}"}

    document["data"]["type"] = USERPROFILE_TYPE
    document["data"]["areas"] = document["data"].get("areas", {})
    document["data"]["name"] = document["data"].get("name", None)

    return {"comment": body.get("message", "default comment"), "document": document}


def _get_legacy_doc(document, collection_view=False, preferred_lang=None, lang=None):
    result = document["legacy"]

    if collection_view:
        del result["geometry"]

    locales = document["data"]["locales"]
    cooked_locales = document["cooked_data"]["locales"]

    if preferred_lang is not None:
        result["locales"] = [_get_preferred_locale(preferred_lang, locales)]

    if lang is not None:
        if lang in locales:
            result["locales"] = [locales[lang]]
        else:
            result["locales"] = []

    cook_lang = request.args.get("cook")

    if cook_lang:
        result["locales"] = [_get_preferred_locale(cook_lang, locales)]
        result["cooked"] = _get_preferred_locale(cook_lang, cooked_locales)

    return result
