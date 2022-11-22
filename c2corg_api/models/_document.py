from flask_camp import current_api
from flask_camp.models import Document, DocumentVersion
from flask_camp.utils import JsonResponse
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session
from werkzeug.exceptions import BadRequest

from c2corg_api.search import DocumentSearch, DocumentLocaleSearch
from c2corg_api.schemas import schema_validator
from c2corg_api.views.markdown import cook as markdown_cooker


class BaseModelHooks:
    def after_get_document(self, response: JsonResponse):
        ...

    def before_create_document(self, document, version):
        document.data = {"topics": {}}
        document_type = version.data["type"]
        schema_validator.validate(version.data, f"{document_type}.json")
        self.update_document_search_table(version.document, version)
        flag_modified(version, "data")

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        document_type = old_version.data["type"]

        if document_type != new_version.data["type"]:
            raise BadRequest("'type' attribute can't be changed")

        schema_validator.validate(new_version.data, f"{document_type}.json")
        self.update_document_search_table(document, new_version)

    def get_search_items(self, document: Document, langs, session: Session = None) -> DocumentSearch:
        # TODO: on remove legacy, removes session parameters
        session = current_api.database.session if session is None else session

        search_item: DocumentSearch = session.query(DocumentSearch).get(document.id)
        search_locale_items = session.query(DocumentLocaleSearch).filter(DocumentLocaleSearch.id == document.id).all()

        if search_item is None:  # means the document is not yet created
            search_item = DocumentSearch(id=document.id)
            session.add(search_item)

        search_locale_items = {item.lang: item for item in search_locale_items}

        for lang in langs:
            if lang not in search_locale_items:
                # TODO: possible integrity error here
                search_locale_items[lang] = DocumentLocaleSearch(id=document.id, lang=lang)
                session.add(search_locale_items[lang])

        return search_item, search_locale_items

    def update_document_search_table(
        self, document: Document, version: DocumentVersion, session=None
    ) -> DocumentSearch:
        # TODO: on remove legacy, removes session parameters
        session = current_api.database.session if session is None else session

        langs = [lang for lang in version.data["locales"]]
        search_item, search_locale_items = self.get_search_items(document, langs, session)

        for lang in langs:
            search_locale_items[lang].title = version.data["locales"][lang].get("title", "")

        search_item.available_langs = langs
        search_item.document_type = version.data["type"]

        return search_item

    @staticmethod
    def get_document_without_redirection(document_id, get_document):
        # TODO flask-camp? add a folloew_redirection in get_document ?
        document = get_document(document_id)

        if "redirects_to" in document:
            return BaseModelHooks.get_document_without_redirection(document["redirects_to"], get_document)

        return document

    def get_cooked_locales(self, locales):
        return {lang: markdown_cooker(locale) for lang, locale in locales.items()}

    def get_cooked_associations(self, associations, get_document):
        cooked_associations = {}

        for name, value in associations.items():
            if isinstance(value, int):
                associations[name] = BaseModelHooks.get_document_without_redirection(value, get_document)
            else:
                cooked_associations[name] = {}
                for document_id in value:
                    cooked_associations[name][document_id] = BaseModelHooks.get_document_without_redirection(
                        document_id, get_document
                    )

        return cooked_associations

    def cook(self, document: dict, get_document):
        data = document["data"]
        document["cooked_data"] = {"locales": self.get_cooked_locales(data["locales"])}

        associations = data.get("associations")

        if isinstance(associations, dict):
            document["cooked_data"]["associations"] = self.get_cooked_associations(associations, get_document)
