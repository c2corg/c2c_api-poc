from flask_camp import current_api
from flask_camp.models import Document
from c2corg_api.hooks import on_document_save


def reset_search_index(session):
    for document in Document.query.all():
        on_document_save(document, document.last_version, document.last_version)

    current_api.database.session.commit()
