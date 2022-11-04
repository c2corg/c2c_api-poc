import json
from flask_camp import current_api
from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE, ARTICLE_TYPE
from werkzeug.exceptions import BadRequest


def get_legacy_doc(document_id):
    result = current_api.get_cooked_document(document_id)
    return convert_to_legacy_doc(result)


def convert_to_legacy_doc(document):
    """convert a json result from the new model to it's equivalent in legacy API"""

    data = document["data"]

    result = {
        "document_id": document["id"],
        "version": document["version_id"],
        "protected": document["protected"],
        "type": data["type"],
        "locales": [locale | {"version": 0} for locale in data["locales"].values()],
        "available_langs": list(data["locales"].keys()),
        "associations": {
            "articles": [],
            "books": [],
            "images": [],
            "waypoints": [],
            "routes": [],
            "xreports": [],
            "users": [],
        },
    }

    # print(json.dumps(document, indent=4))
    for _, associated_document in document["cooked_data"]["associations"].items():
        result["associations"][associated_document["data"]["type"] + "s"].append(associated_document)

    if data["type"] == AREA_TYPE:
        pass

    elif data["type"] == USERPROFILE_TYPE:
        result |= {
            "name": data["name"],
            "forum_username": data["name"],
            "areas": data["areas"],
            "geometry": data["geometry"] | {"version": 0},
        }
    elif data["type"] == ARTICLE_TYPE:
        result |= {
            "categories": data["categories"],
            "activities": data["activities"],
            "article_type": data["article_type"],
        }

        result |= {"author": {"user_id": data.get("author", None)}}

    return result


def convert_from_legacy_doc(legacy_document, document_type, expected_document_id=None):

    result = {
        "data": {
            "type": legacy_document.pop("type", document_type),
        },
    }

    if result["data"]["type"] == "":
        result["data"]["type"] = document_type

    if "version" in legacy_document:  # new doc do not have any version id
        result["version_id"] = legacy_document.pop("version")

    if "document_id" in legacy_document and legacy_document["document_id"] != 0:
        result["id"] = int(legacy_document.pop("document_id"))

        if result["id"] != expected_document_id:
            raise BadRequest("Id in body does not match id in URI")

        old_version = current_api.get_document(result["id"])
        old_data = old_version["data"]
    else:
        old_data = {}

    old_locales = old_data.get("locales", {})

    if document_type == USERPROFILE_TYPE:  # rely on old version to get document type
        result["data"] |= {
            "locales": old_locales | {locale["lang"]: locale for locale in legacy_document.pop("locales", {})},
            "areas": legacy_document.pop("areas", {}),
            "name": legacy_document.pop("name", old_data["name"]),
            "geometry": {"geom": "{}"},
            "associations": [],  # TODO
        }

        if "geometry" in legacy_document:
            result["data"]["geometry"]["geom"] = json.loads(legacy_document.pop("geometry")["geom"])

        # other props
        result["data"] |= legacy_document
    elif document_type == ARTICLE_TYPE:
        result["data"] |= {
            "locales": old_locales | {locale["lang"]: locale for locale in legacy_document.pop("locales", {})},
            "associations": [],  # TODO
            "activities": legacy_document.pop("activities", []),
            "categories": legacy_document.pop("categories", []),
            "article_type": legacy_document["article_type"],
        }
    else:
        raise NotImplementedError(f"Dont know how to convert {document_type}")

    return result
