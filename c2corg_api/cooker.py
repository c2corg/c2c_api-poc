from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE


def cooker(document, get_document):
    data = document["data"]

    locales = [locale | {"version": 0} for locale in data["locales"]]

    document["legacy"] = {
        "locales": locales,
        "available_langs": [locale["lang"] for locale in locales],
        "document_id": document["id"],
        "protected": document["protected"],
        "type": data["type"],
        "version": 0,  # no equivalent ?
        "associations": [],
    }

    if data["type"] == AREA_TYPE:
        pass

    elif data["type"] == USERPROFILE_TYPE:
        document["legacy"] |= {
            "areas": data["areas"],
            "name": data["name"],
            "geometry": data["geometry"] | {"version": 0},
            "forum_username": data["name"],
        }
