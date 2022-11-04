from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import OUTING_TYPE


class ArchiveOuting:
    ...


class Outing(LegacyDocument):
    def __init__(self, document=None):
        super().__init__(document=document)

        if document is None:
            self.create_new_model(
                data={
                    "type": OUTING_TYPE,
                    "quality": "draft",
                    # "activities": activities,
                    # "outing_types": outing_types,
                    "locales": {"fr": {"lang": "fr", "title": "..."}},
                    "associations": [],
                }
            )

    @property
    def activities(self):
        return self._document.last_version.data["activities"]
