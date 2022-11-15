from flask_camp.models import Document, DocumentVersion
from c2corg_api.models._document import BaseModelHooks


class Book(BaseModelHooks):
    def update_document_search_table(self, document: Document, version: DocumentVersion, session=None):
        search_item = super().update_document_search_table(document, version, session=session)
        search_item.activities = version.data["activities"]
