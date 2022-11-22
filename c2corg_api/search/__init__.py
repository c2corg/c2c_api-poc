from flask_camp import current_api
from flask_camp.models import BaseModel, Document, User
from sqlalchemy import Column, ForeignKey, String, select, Boolean, UniqueConstraint, and_
from sqlalchemy.dialects.postgresql import ARRAY


class DocumentSearch(BaseModel):
    # Define a one-to-one relationship with document table
    # ondelete is mandatory, as a deletion of the document must delete the search item
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)

    # We want to be able to search on a document type property
    # index is very import, obviously
    document_type = Column(String(16), index=True)

    # for profile document
    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=True)
    user_is_validated = Column(Boolean, index=True, default=False, nullable=True)

    available_langs = Column(ARRAY(String()), index=True, default=[])

    activities = Column(ARRAY(String()), index=True, default=[])
    event_activity = Column(String, index=True, nullable=True)  # for xreports


class DocumentLocaleSearch(BaseModel):
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)
    lang = Column(String, index=True, primary_key=True)
    title = Column(String, index=True)

    __table_args__ = (UniqueConstraint("id", "lang", name="_document_locale_search_uc"),)


def search(document_type=None, id=None, user_id=None):
    criterions = []

    if document_type is not None:
        criterions.append(DocumentSearch.document_type == document_type)

        if document_type == "profile":  # TODO
            criterions.append(DocumentSearch.user_is_validated == True)

    if id is not None:
        criterions.append(DocumentSearch.id == id)

    if user_id is not None:
        criterions.append(DocumentSearch.user_id == user_id)

    query = select(DocumentSearch.id).where(and_(*criterions))

    result = list(current_api.database.session.execute(query))

    return [item[0] for item in result]
