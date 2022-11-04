from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import OUTING_TYPE


class ArchiveOuting:
    ...


class Outing(LegacyDocument):
    def __init__(self, document=None, activities=None, date_start=None, date_end=None):
        super().__init__(document=document)

        if document is None:
            data = {
                "type": OUTING_TYPE,
                "quality": "draft",
                "activities": activities,
                "date_start": str(date_start),
                "date_end": str(date_end),
                "locales": {"fr": {"lang": "fr", "title": "..."}},
                "associations": [],
            }

            self.create_new_model(data=data)

    @property
    def activities(self):
        return self._document.last_version.data["activities"]
