from flask_camp._utils import JsonResponse


AREA_TYPE = "area"
ARTICLE_TYPE = "article"
BOOK_TYPE = "book"
IMAGE_TYPE = "image"
MAP_TYPE = "map"
OUTING_TYPE = "outing"
ROUTE_TYPE = "route"
WAYPOINT_TYPE = "waypoint"
XREPORT_TYPE = "xreport"
USERPROFILE_TYPE = "profile"


class BaseModelHooks:
    def after_get_document(self, response: JsonResponse):
        ...

    def on_creation(self, version):
        ...

    def on_new_version(self, old_version, new_version):
        ...

    def cook(self, document: dict, get_document):
        ...
