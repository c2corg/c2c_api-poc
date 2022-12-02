from c2corg_api.models import AREA_TYPE
from c2corg_api.legacy.models.document import Document as LegacyDocument


class Area(LegacyDocument):
    def __init__(self, area_type, locales=None):
        super().__init__()
        data = {"type": AREA_TYPE, "area_type": area_type, "quality": "draft", "associations": {}}

        if locales is None:
            data["locales"] = {"fr": {"lang": "fr", "title": "..."}}
        else:
            data["locales"] = {locale.lang: locale._json for locale in locales}

        self.create_new_model(data=data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)
        result["data"]["area_type"] = legacy_document.pop("area_type", previous_data.get("area_type", "admin_limits"))

        return result


class ArchiveArea:
    ...
