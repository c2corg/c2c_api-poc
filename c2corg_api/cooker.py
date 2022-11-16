from c2corg_api.models import models


def cooker(document, get_document):
    document["cooked_data"] = {}

    document_type = document["data"]["type"]
    model = models[document_type]
    model.cook_locales(document)
    model.cook_associations(document, get_document)
    model.cook(document, get_document)

    # import json
    # print(json.dumps(document, indent=4))
