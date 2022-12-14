from flask_camp.models import Document
from sqlalchemy.orm.attributes import flag_modified

from c2corg_api.models import (
    USERPROFILE_TYPE,
    BOOK_TYPE,
    IMAGE_TYPE,
    MAP_TYPE,
    ARTICLE_TYPE,
    AREA_TYPE,
    IMAGE_TYPE,
    WAYPOINT_TYPE,
    ROUTE_TYPE,
    OUTING_TYPE,
    XREPORT_TYPE,
)


class AssociationLog:
    ...


class Association:
    def __init__(
        self,
        parent_document=None,
        child_document=None,
        parent_document_id=None,
        child_document_id=None,
        parent_document_type=None,
        child_document_type=None,
    ):
        if parent_document is None:
            self.parent_document = Document.get(id=parent_document_id)
        else:
            self.parent_document = parent_document._document

        if child_document is None:
            self.child_document = Document.get(id=child_document_id)
        else:
            self.child_document = child_document._document

    @classmethod
    def create(cls, parent_document, child_document):
        return cls(parent_document=parent_document, child_document=child_document)

    def propagate_in_documents(self):
        self._add_association(self.parent_document, self.child_document)
        self._add_association(self.child_document, self.parent_document)

    @staticmethod
    def _add_association(document, associated_document):
        new_model = document.last_version
        document_type = new_model.data["type"]
        associated_document_type = associated_document.last_version.data["type"]

        if document_type in (MAP_TYPE,):
            return

        if "associations" not in new_model.data:
            raise Exception()

        associations = new_model.data["associations"]

        def add_association(key, document_id):
            if key not in associations:
                associations[key] = []

            associations[key].append(document_id)

        if document_type == USERPROFILE_TYPE:
            if associated_document_type == AREA_TYPE:
                add_association("area", associated_document.id)

        elif document_type == ARTICLE_TYPE:
            if associated_document_type in (ARTICLE_TYPE, IMAGE_TYPE, WAYPOINT_TYPE, OUTING_TYPE, ROUTE_TYPE):
                add_association(associated_document_type, associated_document.id)

        elif document_type == BOOK_TYPE:
            if associated_document_type in (ARTICLE_TYPE, IMAGE_TYPE, WAYPOINT_TYPE, ROUTE_TYPE):
                add_association(associated_document_type, associated_document.id)

        elif document_type in (IMAGE_TYPE, OUTING_TYPE, XREPORT_TYPE, ROUTE_TYPE, WAYPOINT_TYPE):
            add_association(associated_document_type, associated_document.id)

        elif document_type == AREA_TYPE:
            if associated_document_type in (IMAGE_TYPE,):
                add_association(associated_document_type, associated_document.id)

        else:
            raise Exception(f"Please set association map for {document_type}")

        flag_modified(new_model, "data")

    def get_log(self, _):
        return None
