from flask_camp import allow
from werkzeug.exceptions import NotFound
from c2corg_api.models import USERPROFILE_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView


class ProfilesView(DocumentCollectionView):
    rule = "/profiles"
    document_type = USERPROFILE_TYPE

    @allow("authenticated", allow_blocked=True)
    def get(self):
        return super().get()

    @allow("anonymous", "authenticated")
    def post(self):
        raise NotFound()  # just for test


class ProfileView(DocumentView):
    rule = "/profiles/<int:document_id>"
    document_type = USERPROFILE_TYPE
