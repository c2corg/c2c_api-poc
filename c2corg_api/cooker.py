from c2corg_api.views.markdown import cook as markdown_cooker
from c2corg_api.models import ROUTE_TYPE, get_preferred_locale, models


def cooker(document, get_document):
    data = document["data"]
    document_type = data["type"]
    cooked_locales = {lang: markdown_cooker(locale) for lang, locale in data["locales"].items()}

    document["cooked_data"] = {
        "locales": cooked_locales,
    }

    # import json
    # print(json.dumps(document["data"], indent=4))

    associations = document["data"].get("associations")

    if isinstance(associations, dict):
        cooked_associations = {}

        for name, value in associations.items():
            if isinstance(value, int):
                associations[name] = get_document(value)
            else:
                associations[name] = {}
                for document_id in value:
                    associations[name][document_id] = get_document(document_id)

        document["cooked_data"]["associations"] = cooked_associations

    elif isinstance(associations, list):  # TODO : remove this part
        cooked_associations = {}
        for document_id in associations:
            cooked_associations[document_id] = get_document(document_id)

        document["cooked_data"]["associations"] = cooked_associations

    models[document_type].cook(document, get_document)

    if document_type == ROUTE_TYPE:  # move this into Route.cook
        if data.get("main_waypoint_id") is not None:
            main_waypoint_id = data["main_waypoint_id"]

            if main_waypoint_id not in cooked_associations:
                cooked_associations[main_waypoint_id] = get_document(main_waypoint_id)

            main_waypoint = cooked_associations[main_waypoint_id]

            for lang, locale in cooked_locales.items():
                waypoint_locale = get_preferred_locale(lang, main_waypoint["data"]["locales"])
                if waypoint_locale is not None:
                    locale["title_prefix"] = waypoint_locale["title"]
