from .article import Article
from .book import Book
from .topo_map import TopoMap
from .userprofile import UserProfile
from .waypoint import Waypoint
from .xreport import Xreport

from .types import (
    AREA_TYPE,
    ARTICLE_TYPE,
    BOOK_TYPE,
    IMAGE_TYPE,
    MAP_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
    USERPROFILE_TYPE,
    WAYPOINT_TYPE,
    XREPORT_TYPE,
)

models = {
    ARTICLE_TYPE: Article(),
    BOOK_TYPE: Book(),
    MAP_TYPE: TopoMap(),
    USERPROFILE_TYPE: UserProfile(),
    WAYPOINT_TYPE: Waypoint(),
    XREPORT_TYPE: Xreport(),
}
