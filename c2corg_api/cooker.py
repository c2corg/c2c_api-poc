from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE


def cooker(document, get_document):
    data = document["data"]

    if data["type"] == AREA_TYPE:
        document["legacy"] = {"locales": data["locales"]}

    elif data["type"] == USERPROFILE_TYPE:
        document["legacy"] = {
            "locales": data["locales"],
            "areas": data["areas"],
            "name": data["name"],
        }

    document["legacy"]["document_id"] = document["id"]
    document["legacy"]["protected"] = document["protected"]
    document["legacy"]["type"] = data["type"]
