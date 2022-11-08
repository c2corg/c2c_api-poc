from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import MAP_TYPE


class ArchiveTopoMap:
    ...


class TopoMap(LegacyDocument):
    def __init__(self, editor=None, scale=None, code=None, version=None):
        super().__init__(version=version)

        if version is None:
            super().create_new_model(
                {
                    "type": MAP_TYPE,
                    "editor": editor,
                    "geometry": {"geom_detail": {"type": "Polygon", "coordinates": []}},
                    "scale": scale,
                    "code": code,
                    "locales": {},
                }
            )
