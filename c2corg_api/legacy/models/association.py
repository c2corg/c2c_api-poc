class AssociationLog:
    ...


class Association:
    def __init__(self, parent_document, child_document):
        self.parent_document, self.child_document = parent_document, child_document

    @classmethod
    def create(cls, parent_document, child_document):
        return cls(parent_document=parent_document, child_document=child_document)

    def propagate_in_documents(self):
        self._add_association(self.parent_document, self.child_document.document_id)
        self._add_association(self.child_document, self.parent_document.document_id)

    @staticmethod
    def _add_association(document, document_id):
        new_model = document._document.last_version

        if "associations" not in new_model.data:
            new_model.data["associations"] = []

        if document_id not in new_model.data["associations"]:
            new_model.data["associations"].append(document_id)
