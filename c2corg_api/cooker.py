from c2corg_api.views.markdown import cook as markdown_cooker


def cooker(document, get_document):
    data = document["data"]

    document["cooked_data"] = {"locales": {lang: markdown_cooker(locale) for lang, locale in data["locales"].items()}}
