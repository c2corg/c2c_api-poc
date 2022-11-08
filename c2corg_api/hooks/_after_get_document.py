from flask_camp._utils import JsonResponse
from c2corg_api.models import models


def after_get_document(response: JsonResponse):
    models[response.data["document"]["data"]["type"]].after_get_document(response)
