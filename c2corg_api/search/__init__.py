from flask_camp import current_api
from flask_camp.models import BaseModel, Document, User
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, UniqueConstraint, select, and_
from sqlalchemy.dialects.postgresql import ARRAY


def slugify(title, lang=None):
    return title.lower()


class DocumentSearch(BaseModel):
    # Define a one-to-one relationship with document table
    # ondelete is mandatory, as a deletion of the document must delete the search item
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)

    # We want to be able to search on a document type property
    # index is very import, obviously
    document_type = Column(String(16), index=True)

    timestamp = Column(DateTime(timezone=True), nullable=False)

    available_langs = Column(ARRAY(String()), index=True, default=[])

    # for profile document
    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=True)
    user_is_validated = Column(Boolean, index=True, default=False, nullable=True)

    # for xreports
    activities = Column(ARRAY(String()), index=True, default=[])
    event_activity = Column(String, index=True, nullable=True)


class DocumentLocaleSearch(BaseModel):
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)
    lang = Column(String, index=True, primary_key=True)
    title = Column(String, index=True)
    slugified_title = Column(String, index=True)

    # for route
    title_prefix = Column(String)

    __table_args__ = (UniqueConstraint("id", "lang", name="_document_locale_search_uc"),)

    def set_title(self, title):
        self.title = title
        self.slugified_title = slugify(self.title, self.lang)


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
