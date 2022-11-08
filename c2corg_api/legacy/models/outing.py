from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale as LegacyDocumentLocale
from c2corg_api.models import OUTING_TYPE


class ArchiveOuting:
    ...


class OutingLocale(LegacyDocumentLocale):
    ...


class Outing(LegacyDocument):
    def __init__(self, activities=None, date_start=None, date_end=None, geometry=None, version=None):
        super().__init__(version=version)

        if version is None:
            data = {
                "type": OUTING_TYPE,
                "quality": "draft",
                "activities": activities,
                "date_start": str(date_start),
                "date_end": str(date_end),
                "locales": {"fr": {"lang": "fr", "title": "..."}},
                "associations": [],
            }

            if geometry is not None:
                data["geometry"] = geometry._json

            self.create_new_model(data=data)

    @property
    def activities(self):
        return self._version.data["activities"]
