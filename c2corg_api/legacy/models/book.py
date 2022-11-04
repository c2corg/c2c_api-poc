from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import BOOK_TYPE


class ArchiveBook:
    ...


class Book(LegacyDocument):
    def __init__(self, categories=None, activities=None, article_type=None, document=None):
        super().__init__(document=document)

        if document is None:
            self.create_new_model(
                data={
                    "type": BOOK_TYPE,
                    "quality": "draft",
                    # "categories": categories,
                    # "activities": activities,
                    # "article_type": article_type,
                    # "locales": {},
                    # "associations": [],
                    # "author": {"user_id": 666},
                }
            )

    # @property
    # def activities(self):
    #     return self._document.last_version.data["activities"]
