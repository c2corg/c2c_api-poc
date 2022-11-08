from flask_camp import allow

from c2corg_api.models import MAP_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class MapsView(DocumentCollectionView):
    rule = "/maps"
    document_type = MAP_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()

    @allow("moderator")
    def post(self):
        return super().post()


class MapView(DocumentView):
    rule = "/maps/<int:document_id>"
    document_type = MAP_TYPE


class MapVersionView(VersionView):
    rule = "/maps/<int:document_id>/<lang>/<int:version_id>"
    document_type = MAP_TYPE
