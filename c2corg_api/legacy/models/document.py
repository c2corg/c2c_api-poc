# pylint: disable=unused-import

import json
from flask_camp import current_api
from werkzeug.exceptions import BadRequest, NotFound

from c2corg_api.legacy.models.document_history import HistoryMetaData
from c2corg_api.schemas import schema_validator

from c2corg_api.models import (
    ARTICLE_TYPE,
    AREA_TYPE,
    BOOK_TYPE,
    IMAGE_TYPE,
    MAP_TYPE,
    OUTING_TYPE,
    ROUTE_TYPE,
    USERPROFILE_TYPE,
    XREPORT_TYPE,
    WAYPOINT_TYPE,
)


class _AlwaysTrue:
    def __eq__(self, o):
        return True


class Geometry:
    def __init__(self, json):
        self._json = json

    @property
    def version(self):
        return _AlwaysTrue()

    @property
    def geom_detail(self):
        return self._json.get("geom_detail")


class Document:
    def __init__(self, version=None):
        self._version = version
        self._expected_legacy_lang = None

    @property
    def _document(self):
        return self._version.document

    @_document.setter
    def _document(self, value):
        self._version = value.last_version

    def create_new_model(self, data, protected=False):
        from flask_camp.models import Document

        # print(json.dumps(data, indent=4))
        schema_validator.validate(data, f"{data['type']}.json")

        self._version = Document.create(comment="Creation", data=data, author=self.default_author).last_version
        self._document.protected = protected

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):

        legacy_document.pop("available_langs", None)

        legacy_types = {
            "a": AREA_TYPE,
            "c": ARTICLE_TYPE,
            "b": BOOK_TYPE,
            "i": IMAGE_TYPE,
            "m": MAP_TYPE,
            "o": OUTING_TYPE,
            "r": ROUTE_TYPE,
            "u": USERPROFILE_TYPE,
            "w": WAYPOINT_TYPE,
            "x": XREPORT_TYPE,
        }

        result = {
            "protected": legacy_document.pop("protected", False),
            "data": {},
        }

        legacy_type = legacy_document.pop("type", "")

        if legacy_type == "":
            result["data"]["type"] = document_type
        else:
            result["data"]["type"] = legacy_types[legacy_type]

        if "version" in legacy_document:  # new doc do not have any version id
            result["version_id"] = legacy_document.pop("version")

        if "document_id" in legacy_document and legacy_document["document_id"] != 0:
            result["id"] = int(legacy_document.pop("document_id"))
        else:
            legacy_document.pop("document_id", None)  # it can be zero

        # convert locales
        locales = legacy_document.pop("locales", [])
        for locale in locales:
            locale.pop("version", None)

            if "topic_id" in locale and locale["topic_id"] is None:
                del locale["topic_id"]

            if "title_prefix" in locale:
                del locale["title_prefix"]

            for prop in locale:
                if locale[prop] is None:
                    locale[prop] = ""

        result["data"]["locales"] = previous_data.get("locales", {}) | {locale["lang"]: locale for locale in locales}

        # convert associations
        legacy_associations = legacy_document.pop("associations", {})
        legacy_associations.pop("all_routes", None)
        legacy_associations.pop("recent_outings", None)

        if document_type in (USERPROFILE_TYPE, ARTICLE_TYPE, BOOK_TYPE, IMAGE_TYPE, OUTING_TYPE, XREPORT_TYPE):
            associations = {}

            for v6_key, array in legacy_associations.items():
                type_associations = set()
                if len(array) != 0:
                    for document in array:
                        type_associations.add(document["document_id"])

                    if v6_key == "users":
                        v7_key = "profile"
                    else:
                        v7_key = v6_key[:-1]
                    associations[v7_key] = list(type_associations)

            result["data"]["associations"] = associations

        else:
            associations = set()

            for array in legacy_associations.values():
                for document in array:
                    associations.add(document["document_id"])

            result["data"]["associations"] = list(associations)

        # convert geometry
        geometry = legacy_document.pop("geometry", None)
        if geometry is not None:
            result["data"]["geometry"] = {}
            if "geom" in geometry and geometry["geom"] is not None:
                result["data"]["geometry"]["geom"] = json.loads(geometry["geom"])
            if "geom_detail" in geometry and geometry["geom_detail"] is not None:
                result["data"]["geometry"]["geom_detail"] = json.loads(geometry["geom_detail"])

            if result["data"]["geometry"] == {}:
                del result["data"]["geometry"]

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        """Convert document (as dict) of the new model to the legacy v6 dict"""
        data = document["data"]

        v7_types = {
            AREA_TYPE: "a",
            ARTICLE_TYPE: "c",
            BOOK_TYPE: "b",
            IMAGE_TYPE: "i",
            MAP_TYPE: "m",
            OUTING_TYPE: "o",
            ROUTE_TYPE: "r",
            USERPROFILE_TYPE: "u",
            WAYPOINT_TYPE: "w",
            XREPORT_TYPE: "x",
        }

        result = {
            "document_id": document["id"],
            "version": document["version_id"],
            "protected": document["protected"],
            "type": v7_types[data["type"]],
            "locales": [
                locale | {"version": 0, "topic_id": locale.get("topic_id")} for locale in data["locales"].values()
            ],
            "available_langs": list(data["locales"].keys()),
            "associations": {
                "articles": [],
                "books": [],
                "images": [],
                "outings": [],
                "profiles": [],
                "routes": [],
                "users": [],
                "waypoints": [],
                "xreports": [],
            },
        }

        # print(json.dumps(document, indent=4))
        v7_associations = document["data"].get("associations")
        if isinstance(v7_associations, dict):
            for name, value in v7_associations.items():
                if isinstance(value, list):
                    for document_id in value:
                        result["associations"][name + "s"].append({"document_id": document_id})

        elif isinstance(v7_associations, list):  # TODO : must be removed
            associations = document["cooked_data"].get("associations")
            for _, associated_document in associations.items():
                result["associations"][associated_document["data"]["type"] + "s"].append(associated_document)

        if "geometry" in data:
            result["geometry"] = {"version": 0}

            if "geom" in data["geometry"]:
                result["geometry"]["geom"] = json.dumps(data["geometry"]["geom"])

            if "geom_detail" in data["geometry"]:
                result["geometry"]["geom_detail"] = json.dumps(data["geometry"]["geom_detail"])

        return result

    @property
    def protected(self):
        return self._document.protected

    @property
    def history_metadata(self):
        return HistoryMetaData(version=self._version)

    @property
    def default_author(self):
        from flask_camp.models import User

        return User.query.first()

    @property
    def type(self):
        return self._version.data["type"]

    @property
    def version(self):
        return self._version.id

    @property
    def comment(self):
        return self._version.comment

    @property
    def written_at(self):
        return self._version.timestamp

    @property
    def document_archive(self):
        return self

    @property
    def versions(self):
        return [self.__class__(version=version) for version in self._document.versions]

    @property
    def document_id(self):
        return self._version.document_id

    @property
    def document_locales_archive(self):
        locales = LocaleDictProxy(version=self._version)
        return locales.get_locale("en" if self._expected_legacy_lang is None else self._expected_legacy_lang)

    @property
    def locales(self):
        return LocaleDictProxy(version=self._version)

    @property
    def document_geometry_archive(self):
        return Geometry(self._version.data.get("geometry", {}))

    @property
    def geometry(self):
        if "geometry" not in self._version.data:
            return None

        return DocumentGeometry(json=self._version.data["geometry"])

    @geometry.setter
    def geometry(self, value):
        data = self._version.data
        data["geometry"] = value._json
        self._version.data = data

    def get_locale(self, lang):
        return self.locales.get_locale(lang)


class DocumentGeometry:
    def __init__(self, geom=None, geom_detail=None, json=None):
        if json is None:
            import shapely.wkt
            from shapely.geometry import mapping

            json = {}

            if geom is not None:
                srid, shape_as_string = geom.split(";")
                assert srid == "SRID=3857"
                shape = shapely.wkt.loads(shape_as_string)

                json["geom"] = mapping(shape)

            if geom_detail is not None:
                srid, shape_as_string = geom_detail.split(";")
                assert srid == "SRID=3857"
                shape = shapely.wkt.loads(shape_as_string)

                json["geom_detail"] = mapping(shape)

        self._json = json

    @property
    def version(self):
        """Does not exists in the new model"""
        return 0


class LocaleDictProxy:
    def __init__(self, version):
        self._version = version
        self._document_type = version.data["type"]

    def append(self, locale):
        locale.set_document_type(self._document_type)
        self._version.data["locales"][locale.lang] = locale.to_json()
        self._version.data = self._version.data  # force update (need to find a better solution)

    def get_locale(self, lang):
        result = self._version.data["locales"].get(lang)

        return None if result is None else DocumentLocale(json=result)

    def __len__(self):
        return len(self._version.data["locales"])

    def __str__(self):
        return str(self._version.data["locales"])

    def __getitem__(self, i):
        json = list(self._version.data["locales"].values())[i]
        return DocumentLocale(json=json)


class DocumentLocale:
    def __init__(self, lang=None, title=None, summary=None, description="", document_topic=None, json=None):
        if json is not None:
            self._json = json
        else:
            self._json = {"lang": lang, "title": title, "description": description}
            if document_topic is not None and document_topic.topic_id is not None:
                self._json["topic_id"] = document_topic.topic_id
            if summary is not None:
                self._json["summary"] = summary

    def set_document_type(self, document_type):
        if document_type == USERPROFILE_TYPE:
            self._json.pop("title", None)
            self._json.pop("topic_id", None)

    def to_json(self):
        return self._json

    @property
    def version(self):
        """Does not exists in the new model"""
        return 0

    @property
    def lang(self):
        return self._json["lang"]

    @property
    def description(self):
        return self._json["description"]

    @property
    def title(self):
        return self._json.get("title", "")

    @title.setter
    def title(self, value):
        self._json["title"] = value

    @property
    def place(self):
        return self._json.get("place", "")


class ArchiveDocumentLocale:
    ...


class DocumentArchive:
    ...


class UpdateType:  # it'san enum in v6
    FIGURES = "figures"
    GEOM = "geom"
    LANG = "lang"
