from .article import Article
from .book import Book
from .userprofile import UserProfile
from .xreport import Xreport

from .types import (
    AREA_TYPE,
    ARTICLE_TYPE,
    BOOK_TYPE,
    IMAGE_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
    WAYPOINT_TYPE,
    XREPORT_TYPE,
    USERPROFILE_TYPE,
)

models = {
    ARTICLE_TYPE: Article,
    BOOK_TYPE: Book,
    USERPROFILE_TYPE: UserProfile,
    XREPORT_TYPE: Xreport,
}
