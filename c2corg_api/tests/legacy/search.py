from flask_camp import current_api
from flask_camp.models import Document
from c2corg_api.hooks import update_document_search_table


def reset_search_index(session):
    for document in Document.query.all():
        update_document_search_table(document)

    current_api.database.session.commit()
