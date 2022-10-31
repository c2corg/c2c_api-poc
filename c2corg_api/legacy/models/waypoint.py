from c2corg_api.legacy.models.document import Document, DocumentGeometry


class Waypoint(Document):
    def __init__(self, waypoint_type=None, elevation=None, rock_types=None, geometry=None, document=None):
        super().__init__(document=document)

        if waypoint_type is not None and document is None:
            if geometry is None:
                geometry = DocumentGeometry(json={"geom": {}})

            self.create_new_model(
                {
                    "waypoint_type": waypoint_type,
                    "elevation": elevation,
                    "locales": {},
                    "rock_types": rock_types,
                    "geometry": geometry._json,
                }
            )