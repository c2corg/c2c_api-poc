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

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {
            "quality": legacy_document.pop("quality", "draft"),
            "activities": legacy_document.pop("activities", []),
        }

        # clean
        legacy_document.pop("geometry", None)

        # other props
        result["data"] |= legacy_document

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        result = LegacyDocument.convert_to_legacy_doc(document)
        data = document["data"]

        result |= {
            "activities": data["activities"],
        }
        return result

    @property
    def activities(self):
        return self._document.last_version.data["activities"]

    @property
    def book_types(self):
        return self._document.last_version.data["book_types"]
