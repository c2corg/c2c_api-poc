from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale, DocumentGeometry
from c2corg_api.models import ROUTE_TYPE


class RouteLocale(DocumentLocale):
    def __init__(self, lang=None, title="", summary=None, description="", gear="", title_prefix="", json=None):
        super().__init__(lang=lang, title=title, summary=summary, description=description, json=json)
        self._json["gear"] = gear
        self._json["title_prefix"] = title_prefix


class Route(LegacyDocument):
    def __init__(
        self,
        activities=None,
        elevation_max=None,
        elevation_min=None,
        height_diff_up=None,
        height_diff_down=None,
        durations=None,
        locales=None,
        geometry: DocumentGeometry = None,
        main_waypoint_id=None,
        version=None,
    ):
        super().__init__(version=version)

        if version is None:

            data = {
                "type": ROUTE_TYPE,
                "activities": activities,
                "locales": {} if locales is None else {locale.lang: locale._json for locale in locales},
                "associations": [],
                "quality": "draft",
            }

            if geometry is not None:
                data["geometry"] = geometry._json
                if "geom" not in data["geometry"]:
                    data["geometry"]["geom"] = DocumentGeometry(geom="SRID=3857;POINT(0 0)")._json["geom"]
            else:
                data["geometry"] = DocumentGeometry(geom="SRID=3857;POINT(0 0)")._json

            if main_waypoint_id is not None:
                data["main_waypoint_id"] = main_waypoint_id
            if elevation_max is not None:
                data["elevation_max"] = elevation_max
            if elevation_min is not None:
                data["elevation_min"] = elevation_min
            if height_diff_up is not None:
                data["height_diff_up"] = height_diff_up
            if height_diff_down is not None:
                data["height_diff_down"] = height_diff_down
            if durations is not None:
                data["durations"] = durations

            self.create_new_model(data)
