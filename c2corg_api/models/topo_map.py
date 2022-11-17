from flask_camp.models import Document, DocumentVersion
from flask_login import current_user
from werkzeug.exceptions import Forbidden

from c2corg_api.models._document import BaseModelHooks


class TopoMap(BaseModelHooks):
    def before_create_document(self, document, version):
        super().before_create_document(document, version)
        if not current_user.is_moderator:
            raise Forbidden()

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        super().before_update_document(document, old_version, new_version)
        if not current_user.is_moderator:
            raise Forbidden()
