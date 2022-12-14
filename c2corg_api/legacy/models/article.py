from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import ARTICLE_TYPE


class ArchiveArticle:
    ...


class Article(LegacyDocument):
    def __init__(self, categories=None, activities=None, article_type=None, locales=None, version=None):
        super().__init__(version=version)

        if version is None:
            data = {
                "type": ARTICLE_TYPE,
                "quality": "draft",
                "categories": categories,
                "activities": activities,
                "article_type": article_type,
                "associations": {},
                "author": {"user_id": 666},
            }

            if locales is None:
                data["locales"] = {"fr": {"lang": "fr", "title": "..."}}
            else:
                data["locales"] = {locale.lang: locale._json for locale in locales}

            self.create_new_model(data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {
            "activities": legacy_document.pop("activities", []),
            "categories": legacy_document.pop("categories", []),
            "article_type": legacy_document.pop("article_type"),
            "quality": legacy_document.pop("quality", "draft"),
            "author": legacy_document.pop("author", previous_data.get("author", None)),
        }

        # other props
        result["data"] |= legacy_document

        # clean
        result["data"].pop("geometry", None)
        result["data"]["associations"].pop("profile", None)

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        result = LegacyDocument.convert_to_legacy_doc(document)
        data = document["data"]

        result |= {
            "categories": data["categories"],
            "activities": data["activities"],
            "article_type": data["article_type"],
            "author": data["author"],
        }

        return result

    @property
    def activities(self):
        return self._version.data["activities"]

    @property
    def categories(self):
        return self._version.data["categories"]

    @property
    def article_type(self):
        return self._version.data["article_type"]
