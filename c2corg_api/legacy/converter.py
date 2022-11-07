from flask_camp import current_api

from c2corg_api.legacy.utils import get_legacy_model


def get_legacy_doc(document_id):
    result = current_api.get_cooked_document(document_id)
    return convert_to_legacy_doc(result)


def convert_to_legacy_doc(document):
    document_type = document["data"]["type"]
    return get_legacy_model(document_type).convert_to_legacy_doc(document)


def convert_from_legacy_doc(legacy_document, document_type, previous_data):
    return get_legacy_model(document_type).convert_from_legacy_doc(legacy_document, document_type, previous_data)
