from flask import request
from flask_camp import allow
from flask_camp.views.content import documents, document


class ProfileView:
    rule = "/profiles/<int:profile_id>"

    @allow("anonymous", "authenticated")
    def get(self, profile_id):
        result = document.get(profile_id)

        return _get_legacy_doc(result.json["document"], pl=request.args.get("l"))  #  not optimized at all


class ProfilesView:
    rule = "/profiles"

    @allow("authenticated", allow_blocked=True)
    def get(self):
        result = documents.get()

        return {
            "total": result["count"],
            "documents": [
                _get_legacy_doc(document, collection_view=True, pl=request.args.get("pl"))
                for document in result["documents"]
            ],
        }


def _get_legacy_doc(document, collection_view=False, pl=None):
    result = document["legacy"]

    if pl is not None:
        locales = [locale for locale in result["locales"] if locale["lang"] == pl]
        if len(locales) == 0:
            locales = [locale for locale in result["locales"] if locale["lang"] == "fr"]  # TODO preferred lang

        result["locales"] = locales

    if collection_view:
        del result["geometry"]

    cook_lang = request.args.get("cook")

    if cook_lang:
        locales = document["data"]["locales"]
        cooked_locales = document["cooked_data"]["locales"]

        if cook_lang not in locales:
            langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

            for lang in langs_priority:
                if lang in locales:
                    cook_lang = lang
                    break

        result["locales"] = [locales.get(cook_lang)]
        result["cooked"] = cooked_locales.get(cook_lang)

    return result
