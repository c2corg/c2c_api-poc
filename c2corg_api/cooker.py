from c2corg_api.views.markdown import cook as markdown_cooker


def cooker(document, get_document):
    data = document["data"]

    document["cooked_data"] = {
        "locales": {lang: markdown_cooker(locale) for lang, locale in data["locales"].items()},
        "associations": {},
    }

    # import json

    # print(json.dumps(document["data"], indent=4))
    for document_id in document["data"].get("associations", []):
        document["cooked_data"]["associations"][document_id] = get_document(document_id)  # TODO : cook it
