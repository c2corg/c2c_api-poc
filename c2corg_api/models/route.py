from flask_camp import current_api
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
        search_item, search_locale_items = super().update_document_search_table(document, version, session=session)
        search_item.activities = version.data["activities"]

        if (main_waypoint_id := version.data.get("main_waypoint_id")) is not None:
            main_waypoint = current_api.get_document(main_waypoint_id)
            for lang, locale in search_locale_items.items():
                waypoint_locale = get_preferred_locale(lang, main_waypoint["data"]["locales"])
                locale.title_prefix = waypoint_locale["title"]

    def cook(self, document: dict, get_document):

        data = document["data"]
        main_waypoint_id = data.get("main_waypoint_id")

        if main_waypoint_id is not None:
            if main_waypoint_id not in data["associations"]["waypoint"]:
                data["associations"]["waypoint"].append(main_waypoint_id)

        super().cook(document, get_document)

        if main_waypoint_id is not None:
            cooked_locales = document["cooked_data"]["locales"]
            main_waypoint_id = data["main_waypoint_id"]
            main_waypoint = document["cooked_data"]["associations"]["waypoint"][main_waypoint_id]

            for lang, locale in cooked_locales.items():
                waypoint_locale = get_preferred_locale(lang, main_waypoint["data"]["locales"])
                if waypoint_locale is not None:
                    locale["title_prefix"] = waypoint_locale["title"]
