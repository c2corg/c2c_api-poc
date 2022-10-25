from c2corg_api.legacy.models.user_profile import UserProfile as LegacyUserProfile
from c2corg_api.models import USERPROFILE_TYPE
from c2corg_api.search import search

elasticsearch_config = {"index": None}


class Search:
    def __init__(self, document_type) -> None:
        self.document_type = document_type

    def get(self, id, index=None, ignore=None):
        document_ids = search(document_type=self.document_type, id=id)

        if len(document_ids) == 0:
            if ignore == 404:
                return None
            else:
                raise Exception()

        if self.document_type == USERPROFILE_TYPE:
            return LegacyUserProfile(document_ids[0])

        raise NotImplementedError()


class SearchUser:
    @staticmethod
    def get(id, index):
        ...


search_documents = {
    # AREA_TYPE: SearchArea,
    # ARTICLE_TYPE: SearchArticle,
    # BOOK_TYPE: SearchBook,
    # IMAGE_TYPE: SearchImage,
    # OUTING_TYPE: SearchOuting,
    # XREPORT_TYPE: SearchXreport,
    # ROUTE_TYPE: SearchRoute,
    # MAP_TYPE: SearchTopoMap,
    USERPROFILE_TYPE: Search(USERPROFILE_TYPE),
    # WAYPOINT_TYPE: SearchWaypoint
}
