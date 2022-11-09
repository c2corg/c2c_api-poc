from flask_camp import allow

from c2corg_api.models import WAYPOINT_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class WaypointsView(DocumentCollectionView):
    rule = "/waypoints"
    document_type = WAYPOINT_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class WaypointView(DocumentView):
    rule = "/waypoints/<int:document_id>"
    document_type = WAYPOINT_TYPE


class WaypointVersionView(VersionView):
    rule = "/waypoints/<int:document_id>/<lang>/<int:version_id>"
    document_type = WAYPOINT_TYPE
