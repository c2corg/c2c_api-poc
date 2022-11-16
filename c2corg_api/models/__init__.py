from .article import Article
from .book import Book
from .route import Route
from .image import Image
from .outing import Outing
from .topo_map import TopoMap
from .userprofile import UserProfile
from .waypoint import Waypoint
from .xreport import Xreport
from ._document import BaseModelHooks

from ._core import (
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
    AREA_TYPE: BaseModelHooks(),
    ARTICLE_TYPE: Article(),
    BOOK_TYPE: Book(),
    IMAGE_TYPE: Image(),
    MAP_TYPE: TopoMap(),
    OUTING_TYPE: Outing(),
    ROUTE_TYPE: Route(),
    USERPROFILE_TYPE: UserProfile(),
    WAYPOINT_TYPE: Waypoint(),
    XREPORT_TYPE: Xreport(),
}
