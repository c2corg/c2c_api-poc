from .article import Article
from .book import Book
from .route import Route
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
    ROUTE_TYPE: Route(),
    USERPROFILE_TYPE: UserProfile(),
    WAYPOINT_TYPE: Waypoint(),
    XREPORT_TYPE: Xreport(),
}


def get_preferred_locale(preferred_lang, locales):

    if preferred_lang in locales:
        return locales[preferred_lang]

    langs_priority = ["fr", "en", "it", "de", "es", "ca", "eu", "zh"]

    for lang in langs_priority:
        if lang in locales:
            return locales[lang]

    return None
