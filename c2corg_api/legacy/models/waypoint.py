from c2corg_api.legacy.models.document import Document, DocumentGeometry, DocumentLocale
from c2corg_api.models import WAYPOINT_TYPE


class Waypoint(Document):
    def __init__(
        self,
        waypoint_type=None,
        elevation=None,
        rock_types=None,
        geometry=None,
        locales=None,
        protected=False,
        redirects_to=None,
        version=None,
    ):
        super().__init__(version=version)

        if version is None:
            if geometry is None:
                geometry = DocumentGeometry(json={"geom": {"type": "Point", "coordinates": [0, 0]}})

            data = {
                "type": WAYPOINT_TYPE,
                "waypoint_type": waypoint_type,
                "elevation": elevation,
                "geometry": geometry._json,
                "associations": {},
            }

            if locales is None:
                data["locales"] = {"fr": {"lang": "fr", "title": "default title"}}
            else:
                data["locales"] = {locale.lang: locale._json for locale in locales}

            if rock_types is not None:
                data["rock_types"] = rock_types

            self.create_new_model(data, protected=protected, redirects_to=redirects_to)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = Document.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        # other props
        result["data"] |= legacy_document

        optional_attributes = [
            "climbing_rating_max",
            "climbing_rating_median",
            "climbing_rating_min",
            "climbing_styles",
            "height_max",
            "height_median",
            "height_min",
            "maps_info",
            "phone",
            "routes_quantity",
            "url",
        ]

        for attribute in optional_attributes:
            if attribute in result["data"] and result["data"][attribute] is None:
                del result["data"][attribute]

        # TODO
        result["data"].pop("maps", None)
        result["data"].pop("areas", None)

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        data = document["data"]
        result = Document.convert_to_legacy_doc(document)
        result["elevation"] = data["elevation"]

        return result


class WaypointLocale(DocumentLocale):
    def __init__(self, lang=None, title="", description="", summary="", json=None):
        super().__init__(lang=lang, title=title, summary=summary, description=description, json=json)
