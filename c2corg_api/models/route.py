from flask_camp.models import Document, DocumentVersion
from c2corg_api.models._document import BaseModelHooks


def get_preferred_locale(preferred_lang, locales):

    if preferred_lang in locales:
        return locales[preferred_lang]

    langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

    for lang in langs_priority:
        if lang in locales:
            return locales[lang]

    return None


class Route(BaseModelHooks):
    def update_document_search_table(self, document: Document, version: DocumentVersion, session=None):
        search_item = super().update_document_search_table(document, version, session=session)
        search_item.activities = version.data["activities"]

    def cook_associations(self, document: dict, get_document):
        super().cook_associations(document, get_document)

        data = document["data"]
        waypoints = document["cooked_data"]["associations"]["waypoint"]

        if data.get("main_waypoint_id") is not None:
            main_waypoint_id = data["main_waypoint_id"]

            if main_waypoint_id not in waypoints:
                waypoints[main_waypoint_id] = BaseModelHooks.get_document_without_redirection(
                    main_waypoint_id, get_document
                )

    def cook(self, document: dict, get_document):
        data = document["data"]

        if data.get("main_waypoint_id") is not None:
            cooked_locales = document["cooked_data"]["locales"]
            main_waypoint_id = data["main_waypoint_id"]
            main_waypoint = document["cooked_data"]["associations"]["waypoint"][main_waypoint_id]

            for lang, locale in cooked_locales.items():
                waypoint_locale = get_preferred_locale(lang, main_waypoint["data"]["locales"])
                if waypoint_locale is not None:
                    locale["title_prefix"] = waypoint_locale["title"]
