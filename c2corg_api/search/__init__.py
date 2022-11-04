from flask_camp import current_api
from flask_camp.models import BaseModel, Document, User
from sqlalchemy import Column, ForeignKey, String, select
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY

from c2corg_api.models import (
    USERPROFILE_TYPE,
    AREA_TYPE,
    ARTICLE_TYPE,
    WAYPOINT_TYPE,
    BOOK_TYPE,
    IMAGE_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
    XREPORT_TYPE,
    ProfilePageLink,
)


class DocumentSearch(BaseModel):
    # Define a one-to-one relationship with document table
    # ondelete is mandatory, as a deletion of the document must delete the search item
    id = Column(ForeignKey(Document.id, ondelete="CASCADE"), index=True, nullable=True, primary_key=True)

    # We want to be able to search on a document type property
    # index is very import, obviously
    document_type = Column(String(16), index=True)

    # for profile document
    user_id = Column(ForeignKey(User.id, ondelete="CASCADE"), index=True, nullable=True)

    available_langs = Column(ARRAY(String()), index=True, default=[])

    activities = Column(ARRAY(String()), index=True, default=[])

    def update(self, new_version):
        self.available_langs = [lang for lang in new_version.data["locales"]]

        self.document_type = new_version.data["type"]

        if self.document_type == USERPROFILE_TYPE:
            self.user_id = new_version.data.get("user_id")
        elif self.document_type == ARTICLE_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == WAYPOINT_TYPE:
            pass
        elif self.document_type == AREA_TYPE:
            pass
        elif self.document_type == AREA_TYPE:
            pass
        elif self.document_type == BOOK_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == BOOK_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == IMAGE_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == OUTING_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == ROUTE_TYPE:
            self.activities = new_version.data["activities"]
        elif self.document_type == XREPORT_TYPE:
            # self.activities = new_version.data["activities"]
            pass  # TODO
        else:
            raise NotImplementedError(f"Please set how to search {self.document_type}")


def update_document_search_table(document, session=None):
    # TODO: on remove legacy, removes session parameters
    session = current_api.database.session if session is None else session

    search_item: DocumentSearch = session.query(DocumentSearch).get(document.id)

    if search_item is None:  # means the document is not yet created
        search_item = DocumentSearch(id=document.id)
        session.add(search_item)

    search_item.update(document.last_version)


def search(document_type=None, id=None, user_id=None):
    criterions = []

    if document_type is not None:
        criterions.append(DocumentSearch.document_type == document_type)

    if id is not None:
        criterions.append(DocumentSearch.id == id)

    if user_id is not None:
        criterions.append(DocumentSearch.user_id == user_id)

    query = select(DocumentSearch.id).where(and_(*criterions))

    result = list(current_api.database.session.execute(query))

    return [item[0] for item in result]
