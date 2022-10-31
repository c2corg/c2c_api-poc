# from flask import request
from flask_camp import allow

# from flask_camp.views.content import document as document_view
# from werkzeug.exceptions import NotFound
from c2corg_api.models import ARTICLE_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, LegacyView


class ArticlesView(DocumentCollectionView):
    rule = "/articles"
    document_type = ARTICLE_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class ArticleView(LegacyView):
    rule = "/articles/<document_id>"
