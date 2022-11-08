from flask_camp import allow

from c2corg_api.models import OUTING_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class OutingsView(DocumentCollectionView):
    rule = "/outings"
    document_type = OUTING_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class OutingView(DocumentView):
    rule = "/outings/<int:document_id>"
    document_type = OUTING_TYPE


class OutingVersionView(VersionView):
    rule = "/outings/<int:document_id>/<lang>/<int:version_id>"
    document_type = OUTING_TYPE
