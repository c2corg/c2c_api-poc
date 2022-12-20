from c2corg_api.models import AREA_TYPE
from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentGeometry


class Area(LegacyDocument):
    def __init__(self, area_type=None, locales=None, geometry=None, version=None):
        super().__init__(version=version)
        if version is None:

            if geometry is None:
                geometry = DocumentGeometry(json={"geom_detail": {"type": "Polygon", "coordinates": []}})

            data = {
                "type": AREA_TYPE,
                "area_type": area_type or "admin_limits",
                "quality": "draft",
                "associations": {},
                "geometry": geometry._json,
            }

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

    @property
    def area_type(self):
        return self._version.data["area_type"]


class ArchiveArea:
    ...
