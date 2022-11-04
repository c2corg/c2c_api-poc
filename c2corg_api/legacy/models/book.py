from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import BOOK_TYPE


class ArchiveBook:
    ...


class Book(LegacyDocument):
    def __init__(self, activities=None, book_types=None, document=None):
        super().__init__(document=document)

        if document is None:
            self.create_new_model(
                data={
                    "type": BOOK_TYPE,
                    "quality": "draft",
                    "activities": activities,
                    "book_types": book_types,
                    "locales": {"fr": {"lang": "fr", "title": "..."}},
                    "associations": [],
                }
            )

    @property
    def activities(self):
        return self._document.last_version.data["activities"]
