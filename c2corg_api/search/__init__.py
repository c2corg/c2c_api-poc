from flask_camp import current_api
from flask_camp.models import BaseModel, Document
from sqlalchemy import Column, ForeignKey, String, select


class DocumentSearch(BaseModel):
    # Define a one-to-one relationship with document table
    # ondelete is mandatory, as a deletion of the document must delete the search item
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)

    # We want to be able to search on a document type property
    # index is very import, obviously
    document_type = Column(String(16), index=True)


def search(document_type=None, id=None):
    query = select(DocumentSearch.id)

    if document_type is not None:
        query = query.where(DocumentSearch.document_type == document_type)

    if id is not None:
        query = query.where(Document.id == id)

    result = list(current_api.database.session.execute(query))

    return [item[0] for item in result]
