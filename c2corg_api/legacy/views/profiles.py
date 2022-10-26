from flask import request
from flask_camp import allow
from flask_camp.views.content import documents, document
from werkzeug.exceptions import NotFound


class ProfileView:
    rule = "/profiles/<int:profile_id>"

    @allow("anonymous", "authenticated")
    def get(self, profile_id):
        result = document.get(profile_id)

        return _get_legacy_doc(result.json["document"], lang=request.args.get("l"))  #  not optimized at all


class ProfilesView:
    rule = "/profiles"

    @allow("authenticated", allow_blocked=True)
    def get(self):
        result = documents.get()

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
