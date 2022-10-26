from flask_camp import current_api
from flask_camp.models import Document
from c2corg_api.hooks import before_document_save


def reset_search_index(session):
    for document in Document.query.all():
        before_document_save(document)

    current_api.database.session.commit()
