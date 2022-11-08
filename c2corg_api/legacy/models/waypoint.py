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
        version=None,
    ):
        super().__init__(version=version)

        if version is None:
            if geometry is None:
                geometry = DocumentGeometry(json={"geom": {}})

            self.create_new_model(
                {
                    "type": WAYPOINT_TYPE,
                    "waypoint_type": waypoint_type,
                    "elevation": elevation,
                    "locales": {} if locales is None else {locale.lang: locale._json for locale in locales},
                    "rock_types": rock_types,
                    "geometry": geometry._json,
                    "associations": [],
                },
                protected=protected,
            )


class WaypointLocale(DocumentLocale):
    def __init__(self, lang=None, title="", description="", json=None):
        super().__init__(lang=lang, title=title, description=description, json=json)
