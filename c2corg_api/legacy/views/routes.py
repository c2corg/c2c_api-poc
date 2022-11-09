from flask_camp import allow

from c2corg_api.models import ROUTE_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class RoutesView(DocumentCollectionView):
    rule = "/routes"
    document_type = ROUTE_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class RouteView(DocumentView):
    rule = "/routes/<int:document_id>"
    document_type = ROUTE_TYPE


class RouteVersionView(VersionView):
    rule = "/routes/<int:document_id>/<lang>/<int:version_id>"
    document_type = ROUTE_TYPE
