import json
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

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {
            "editor": legacy_document.pop("editor"),
            "scale": legacy_document.pop("scale"),
            "code": legacy_document.pop("code"),
        }

        if "geometry" in legacy_document:
            result["data"] |= {"geom_detail": json.loads(legacy_document["geometry"]["geom_detail"])}
        elif "geometry" in previous_data:
            result["data"]["geometry"] = previous_data["geometry"]

        if "associations" in result["data"]:
            del result["data"]["associations"]

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        result = LegacyDocument.convert_to_legacy_doc(document)
        data = document["data"]

        result |= {
            "editor": data["editor"],
            "scale": data["scale"],
            "code": data["code"],
        }

        if "geometry" in data:
            result["geometry"] = {"geom_detail": json.dumps(data["geometry"]["geom_detail"]), "version": 0}
        else:
            result["geometry"] = None

        del result["associations"]

        return result

    @property
    def code(self):
        return self._version.data["code"]

    @property
    def scale(self):
        return self._version.data["scale"]

    @property
    def editor(self):
        return self._version.data["editor"]
