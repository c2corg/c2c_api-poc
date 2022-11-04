from flask_camp import allow

from c2corg_api.models import BOOK_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class BooksView(DocumentCollectionView):
    rule = "/books"
    document_type = BOOK_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class BookView(DocumentView):
    rule = "/books/<int:document_id>"
    document_type = BOOK_TYPE


class BookVersionView(VersionView):
    rule = "/books/<int:document_id>/<lang>/<int:version_id>"
    document_type = BOOK_TYPE
