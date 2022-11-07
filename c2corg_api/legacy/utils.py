from c2corg_api.legacy.models.area import Area
from c2corg_api.legacy.models.article import Article
from c2corg_api.legacy.models.book import Book
from c2corg_api.legacy.models.document import Document
from c2corg_api.legacy.models.outing import Outing
from c2corg_api.legacy.models.route import Route
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.legacy.models.xreport import Xreport

from c2corg_api.models import (
    AREA_TYPE,
    BOOK_TYPE,
    USERPROFILE_TYPE,
    ARTICLE_TYPE,
    XREPORT_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
)

_legacy_models = {
    AREA_TYPE: Area,
    BOOK_TYPE: Book,
    USERPROFILE_TYPE: UserProfile,
    ARTICLE_TYPE: Article,
    XREPORT_TYPE: Xreport,
    OUTING_TYPE: Outing,
    ROUTE_TYPE: Route,
}


def get_legacy_model(document_type) -> Document:
    return _legacy_models[document_type]
