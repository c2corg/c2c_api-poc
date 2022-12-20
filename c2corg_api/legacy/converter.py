from flask_camp import current_api

from c2corg_api.legacy.utils import get_legacy_model
from c2corg_api.models import USERPROFILE_TYPE, MAP_TYPE, AREA_TYPE


def _get_preferred_locale_as_array(preferred_lang, locales):

    if preferred_lang in locales:
        return [locales[preferred_lang]]

    langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

    for lang in langs_priority:
        if lang in locales:
            return [locales[lang]]

    return []


def get_legacy_doc(document_id):
    result = current_api.get_cooked_document(document_id)
    return convert_to_legacy_doc(result)


def convert_to_legacy_doc(document, collection_view=False, preferred_lang=None, lang=None, cook_lang=None):
    document_type = document["data"]["type"]

    result = get_legacy_model(document_type).convert_to_legacy_doc(document)

    locales = {locale["lang"]: locale for locale in result["locales"]}

    if lang is not None:
        if lang in locales:
            result["locales"] = [locales[lang]]
        else:
            result["locales"] = []

    if preferred_lang is not None:
        result["locales"] = _get_preferred_locale_as_array(preferred_lang, locales)

    if cook_lang is not None:
        cooked_locales = document["cooked_data"]["locales"]
        result["locales"] = _get_preferred_locale_as_array(cook_lang, locales)
        cooked = _get_preferred_locale_as_array(cook_lang, cooked_locales)
        result["cooked"] = None if len(cooked) == 0 else cooked[0]

    if collection_view:
        if document["data"]["type"] in (USERPROFILE_TYPE, MAP_TYPE, AREA_TYPE):
            if "geometry" in result:
                del result["geometry"]

    return result


def convert_from_legacy_doc(legacy_document, document_type, previous_data):
    return get_legacy_model(document_type).convert_from_legacy_doc(legacy_document, document_type, previous_data)
