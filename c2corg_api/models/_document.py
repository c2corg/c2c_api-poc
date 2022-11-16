from flask_camp import current_api
from flask_camp.models import Document, DocumentVersion
from flask_camp.utils import JsonResponse
from werkzeug.exceptions import BadRequest

from c2corg_api.search import DocumentSearch
from c2corg_api.schemas import schema_validator


class BaseModelHooks:
    def after_get_document(self, response: JsonResponse):
        ...

    def before_create_document(self, version):
        document_type = version.data["type"]
        schema_validator.validate(version.data, f"{document_type}.json")
        self.update_document_search_table(version.document, version)

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        document_type = old_version.data["type"]

        if document_type != new_version.data["type"]:
            raise BadRequest("'type' attribute can't be changed")

        schema_validator.validate(new_version.data, f"{document_type}.json")
        self.update_document_search_table(document, new_version)

    def cook(self, document: dict, get_document):
        ...

    def get_search_item(self, document: Document, session=None) -> DocumentSearch:

        # TODO: on remove legacy, removes session parameters
        session = current_api.database.session if session is None else session

        search_item: DocumentSearch = session.query(DocumentSearch).get(document.id)

        if search_item is None:  # means the document is not yet created
            search_item = DocumentSearch(id=document.id)
            session.add(search_item)

        return search_item

    def update_document_search_table(
        self, document: Document, version: DocumentVersion, session=None
    ) -> DocumentSearch:
        # TODO: on remove legacy, removes session parameters
        session = current_api.database.session if session is None else session

        search_item = self.get_search_item(document, session)

        search_item.available_langs = [lang for lang in version.data["locales"]]
        search_item.document_type = version.data["type"]

        return search_item
