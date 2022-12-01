from flask_camp import allow

from c2corg_api.models import AREA_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class AreasView(DocumentCollectionView):
    rule = "/areas"
    document_type = AREA_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class AreaView(DocumentView):
    rule = "/areas/<int:document_id>"
    document_type = AREA_TYPE


class AreaVersionView(VersionView):
    rule = "/areas/<int:document_id>/<lang>/<int:version_id>"
    document_type = AREA_TYPE
