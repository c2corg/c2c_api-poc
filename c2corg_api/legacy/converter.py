from flask_camp import current_api
from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE


def get_legacy_doc(document_id):
    document = current_api.get_cooked_document(document_id)
    return convert_to_legacy_doc(document)


def convert_to_legacy_doc(document):
    """convert a json document from the new model to it's equivalent in legacy API"""

    data = document["data"]

    result = {
        "document_id": document["id"],
        "version": document["version_id"],
        "protected": document["protected"],
        "type": data["type"],
        "locales": [locale | {"version": 0} for locale in data["locales"].values()],
        "available_langs": list(data["locales"].keys()),
        "associations": [],
    }

    if data["type"] == AREA_TYPE:
        pass

    elif data["type"] == USERPROFILE_TYPE:
        result |= {
            "name": data["name"],
            "forum_username": data["name"],
            "areas": data["areas"],
            "geometry": data["geometry"] | {"version": 0},
        }

    return result
