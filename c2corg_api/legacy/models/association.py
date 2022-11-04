from flask_camp.models import Document


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
        self._add_association(self.parent_document, self.child_document.id)
        self._add_association(self.child_document, self.parent_document.id)

    @staticmethod
    def _add_association(document, document_id):
        new_model = document.last_version

        if "associations" not in new_model.data:
            new_model.data["associations"] = []

        if document_id not in new_model.data["associations"]:
            new_model.data["associations"].append(document_id)

        new_model.data = new_model.data  # propagagte json modification
