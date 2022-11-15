from flask_camp.models import Document
from c2corg_api.models import models


def reset_search_index(session):

    for document in session.query(Document).all():
        if not document.is_redirection:
            document_type = document.last_version.data["type"]

            models[document_type].update_document_search_table(document, document.last_version, session=session)

    session.commit()


def force_search_index():
    ...
