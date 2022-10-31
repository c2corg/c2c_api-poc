from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import ARTICLE_TYPE


class ArchiveArticle:
    ...


class Article(LegacyDocument):
    def __init__(self, categories=None, activities=None, article_type=None, document=None):
        super().__init__(document=document)

        if document is None:
            self.create_new_model(
                data={"categories": categories, "activities": activities, "article_type": article_type, "locales": {}}
            )
