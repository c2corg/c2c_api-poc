from flask_camp import allow
from c2corg_api.views import search
from c2corg_api.legacy.converter import convert_to_legacy_doc

rule = "/search"


@allow("anonymous", "authenticated")
def get():

    result = search.get()

    result = {
        f"{document_type}s": {"total": 666, "documents": [convert_to_legacy_doc(document) for document in documents]}
        for document_type, documents in result.items()
    }

    return result
