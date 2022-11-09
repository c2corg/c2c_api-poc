from c2corg_api.legacy.models.area import Area
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.book import Book
from c2corg_api.legacy.models.document import Document
from c2corg_api.legacy.models.topo_map import TopoMap
from c2corg_api.legacy.models.outing import Outing
from c2corg_api.legacy.models.route import Route
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.legacy.models.waypoint import Waypoint
from c2corg_api.legacy.models.xreport import Xreport

from c2corg_api.models import (
    AREA_TYPE,
    ARTICLE_TYPE,
    BOOK_TYPE,
    MAP_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
    USERPROFILE_TYPE,
    WAYPOINT_TYPE,
    XREPORT_TYPE,
)

_legacy_models = {
    AREA_TYPE: Area,
    ARTICLE_TYPE: Article,
    BOOK_TYPE: Book,
    MAP_TYPE: TopoMap,
    OUTING_TYPE: Outing,
    ROUTE_TYPE: Route,
    USERPROFILE_TYPE: UserProfile,
    WAYPOINT_TYPE: Waypoint,
    XREPORT_TYPE: Xreport,
}


def get_legacy_model(document_type) -> Document:
    return _legacy_models[document_type]
