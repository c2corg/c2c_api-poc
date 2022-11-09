from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale, DocumentGeometry
from c2corg_api.models import ROUTE_TYPE


class RouteLocale(DocumentLocale):
    def __init__(self, lang=None, title="", summary=None, description="", gear="", title_prefix="", json=None):
        super().__init__(lang=lang, title=title, summary=summary, description=description, json=json)
        self._json["gear"] = gear


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
                data["durations"] = durations if isinstance(durations, list) else [durations]

            self.create_new_model(data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= legacy_document

        for attribute in [
            "configuration",
            "elevation_min",
            "exposition_rock_rating",
            "route_length",
            "height_diff_difficulties",
            "height_diff_access",
            "lift_access",
            "hiking_mtb_exposition",
            "difficulties_height",
            "height_diff_down",
            "height_diff_up",
            "risk_rating",
            "route_types",
            "aid_rating",
            "ice_rating",
            "mixed_rating",
            "equipment_rating",
            "rock_types",
        ]:
            if attribute in result["data"] and result["data"][attribute] is None:
                del result["data"][attribute]

        if "areas" in result["data"]:
            del result["data"]["areas"]  # TODO

        if "maps" in result["data"]:
            del result["data"]["maps"]

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        data = document["data"]
        cooked_data = document["cooked_data"]

        for lang, locale in data["locales"].items():
            locale["title_prefix"] = cooked_data["locales"][lang].get("title_prefix")

        result = LegacyDocument.convert_to_legacy_doc(document)
        result |= {
            "activities": data["activities"],
            "main_waypoint_id": data.get("main_waypoint_id"),
            "elevation_max": data.get("elevation_max"),
            "elevation_min": data.get("elevation_min"),
            "height_diff_up": data.get("height_diff_up"),
            "height_diff_down": data.get("height_diff_down"),
            "durations": data.get("durations"),
        }

        return result
