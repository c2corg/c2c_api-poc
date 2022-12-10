from flask_camp.models import Document, DocumentVersion
from flask_login import current_user
from werkzeug.exceptions import Forbidden
from c2corg_api.models._document import BaseModelHooks


class Area(BaseModelHooks):
    def update_document_search_table(self, document: Document, version: DocumentVersion, session=None):
        search_item, _ = super().update_document_search_table(document, version, session=session)
        search_item.area_type = version.data["area_type"]

    def before_update_document(self, document: Document, old_version: DocumentVersion, new_version: DocumentVersion):
        old_geometry = old_version.data["geometry"]
        new_geometry = new_version.data["geometry"]

        if not current_user.is_moderator:
            if old_geometry != new_geometry:
                raise Forbidden("No permission to change the geometry")

        return super().before_update_document(document, old_version, new_version)
