from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import BOOK_TYPE


class ArchiveBook:
    ...


class Book(LegacyDocument):
    def __init__(self, activities=None, book_types=None, version=None):
        super().__init__(version=version)

        if version is None:
            self.create_new_model(
                data={
                    "type": BOOK_TYPE,
                    "quality": "draft",
                    "activities": activities,
                    "book_types": book_types,
                    "locales": {"fr": {"lang": "fr", "title": "..."}},
                    "associations": {},
                }
            )

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {
            "quality": legacy_document.pop("quality", "draft"),
            "activities": legacy_document.pop("activities", []),
        }

        # other props
        result["data"] |= legacy_document

        for attribute in ["editor", "url"]:
            if attribute in result["data"] and result["data"][attribute] is None:
                del result["data"][attribute]

        # clean
        result["data"].pop("geometry", None)

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
        return self._version.data["activities"]

    @property
    def book_types(self):
        return self._version.data["book_types"]
