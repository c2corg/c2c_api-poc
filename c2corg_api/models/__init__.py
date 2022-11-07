from .userprofile import UserProfile, USERPROFILE_TYPE


AREA_TYPE = "area"
ARTICLE_TYPE = "article"
BOOK_TYPE = "book"
IMAGE_TYPE = "image"
OUTING_TYPE = "outing"
ROUTE_TYPE = "route"
WAYPOINT_TYPE = "waypoint"
XREPORT_TYPE = "xreport"

ALL_TYPES = set(
    [
        AREA_TYPE,
        ARTICLE_TYPE,
        BOOK_TYPE,
        IMAGE_TYPE,
        OUTING_TYPE,
        ROUTE_TYPE,
        USERPROFILE_TYPE,
        WAYPOINT_TYPE,
        XREPORT_TYPE,
    ]
)
