from c2corg_api.views.markdown import cook as markdown_cooker
from c2corg_api.models import ROUTE_TYPE, get_preferred_locale


def cooker(document, get_document):
    data = document["data"]
    cooked_locales = {lang: markdown_cooker(locale) for lang, locale in data["locales"].items()}
    associations = {}

    # import json
    # print(json.dumps(document["data"], indent=4))

    for document_id in document["data"].get("associations", []):
        associations[document_id] = get_document(document_id)  # TODO : cook it

    if data["type"] == ROUTE_TYPE:
        if data.get("main_waypoint_id") is not None:
            main_waypoint_id = data["main_waypoint_id"]

            if main_waypoint_id not in associations:
                associations[main_waypoint_id] = get_document(main_waypoint_id)

            main_waypoint = associations[main_waypoint_id]

            for lang, locale in cooked_locales.items():
                waypoint_locale = get_preferred_locale(lang, main_waypoint["data"]["locales"])
                if waypoint_locale is not None:
                    locale["title_prefix"] = waypoint_locale["title"]

    document["cooked_data"] = {
        "locales": cooked_locales,
        "associations": associations,
    }
