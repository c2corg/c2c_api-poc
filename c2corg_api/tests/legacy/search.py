from flask_camp.models import Document
from c2corg_api.search import update_document_search_table


def reset_search_index(session):

    for document in session.query(Document).all():
        update_document_search_table(document, session=session)

    session.commit()


def force_search_index():
    ...
