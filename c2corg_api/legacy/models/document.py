# pylint: disable=unused-import

import json
from flask_camp import current_api
from werkzeug.exceptions import BadRequest, NotFound
from c2corg_api.schemas import schema_validator
from c2corg_api.models import (
    USERPROFILE_TYPE,
    ARTICLE_TYPE,
    BOOK_TYPE,
    ROUTE_TYPE,
    WAYPOINT_TYPE,
    AREA_TYPE,
    IMAGE_TYPE,
    XREPORT_TYPE,
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


class DocumentArchive:
    def __init__(self, version):
        self._version = version
        self._expected_legacy_lang = None

    @property
    def _document_type(self):
        return self._version.data["type"]

    @property
    def document_geometry_archive(self):
        return Geometry(self._version.data.get("geometry", {}))

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
    def document_locales_archive(self):
        locales = LocaleDictProxy(version=self._version)
        return locales.get_locale("en" if self._expected_legacy_lang is None else self._expected_legacy_lang)

    @property
    def categories(self):
        return self._get_attribute("categories", {ARTICLE_TYPE: "categories"})

    @property
    def activities(self):
        return self._get_attribute("activities", {ARTICLE_TYPE: "activities", BOOK_TYPE: "activities"})

    @property
    def article_type(self):
        return self._get_attribute("article_type", {ARTICLE_TYPE: "article_type"})

    @property
    def book_types(self):
        return self._get_attribute("book_types", {BOOK_TYPE: "book_types"})

    def _get_attribute(self, attribute_name, mapping):
        if self._document_type not in mapping:
            raise AttributeError(f"'{DocumentArchive}' has no attribute '{attribute_name}' for {self._document_type}")

        return self._version.data[mapping[self._document_type]]

    @property
    def event_type(self):
        return self._get_attribute("event_type", {XREPORT_TYPE: "event_type"})

    @property
    def event_activity(self):
        return self._get_attribute("event_activity", {XREPORT_TYPE: "event_activity"})

    @property
    def nb_participants(self):
        return self._get_attribute("nb_participants", {XREPORT_TYPE: "nb_participants"})

    @property
    def autonomy(self):
        return self._get_attribute("autonomy", {XREPORT_TYPE: "autonomy"})

    @property
    def activity_rate(self):
        return self._get_attribute("activity_rate", {XREPORT_TYPE: "activity_rate"})

    @property
    def supervision(self):
        return self._get_attribute("supervision", {XREPORT_TYPE: "supervision"})

    @property
    def age(self):
        return self._get_attribute("age", {XREPORT_TYPE: "age"})

    @property
    def qualification(self):
        return self._get_attribute("qualification", {XREPORT_TYPE: "qualification"})


class Document:
    def __init__(self, document=None):
        self._document = document

    def create_new_model(self, data):
        from flask_camp.models import Document

        # print(json.dumps(data, indent=4))
        schema_validator.validate(data, f"{data['type']}.json")

        self._document = Document.create(comment="Creation", data=data, author=self.default_author)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):

        result = {
            "protected": legacy_document.pop("protected", False),
            "data": {
                "type": legacy_document.pop("type", document_type),
            },
        }

        if result["data"]["type"] == "":
            result["data"]["type"] = document_type

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

        result["data"]["locales"] = previous_data.get("locales", {}) | {locale["lang"]: locale for locale in locales}

        # convert associations
        legacy_associations = legacy_document.pop("associations", {})
        associations = set()

        legacy_associations.pop("all_routes", None)
        legacy_associations.pop("recent_outings", None)

        for array in legacy_associations.values():
            for document in array:
                associations.add(document["document_id"])

        result["data"]["associations"] = list(associations)

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        """Convert document (as dict) of the new model to the legacy v6 dict"""
        data = document["data"]

        result = {
            "document_id": document["id"],
            "version": document["version_id"],
            "protected": document["protected"],
            "type": data["type"],
            "locales": [locale | {"version": 0} for locale in data["locales"].values()],
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
        for _, associated_document in document["cooked_data"]["associations"].items():
            result["associations"][associated_document["data"]["type"] + "s"].append(associated_document)

        return result

    @property
    def default_author(self):
        from flask_camp.models import User

        return User.query.first()

    @property
    def type(self):
        return self._document.last_version.data["type"]

    @property
    def version(self):
        return self._document.last_version_id

    @property
    def versions(self):
        return [DocumentArchive(version) for version in self._document.versions]

    @property
    def document_id(self):
        return self._document.id

    @property
    def locales(self):
        return LocaleDictProxy(version=self._document.last_version)

    @property
    def geometry(self):
        if "geometry" not in self._document.last_version.data:
            return None

        return DocumentGeometry(json=self._document.last_version.data["geometry"])

    @geometry.setter
    def geometry(self, value):
        data = self._document.last_version.data
        data["geometry"] = value._json
        self._document.last_version.data = data

    def get_locale(self, lang):
        return self.locales.get_locale(lang)


class DocumentGeometry:
    def __init__(self, geom=None, json=None):
        if json is None:
            import shapely.wkt
            from shapely.geometry import mapping

            srid, shape_as_string = geom.split(";")
            assert srid == "SRID=3857"
            shape = shapely.wkt.loads(shape_as_string)

            json = {"geom": mapping(shape)}

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
    def __init__(self, lang=None, title=None, description="", document_topic=None, json=None):
        if json is not None:
            self._json = json
        else:
            self._json = {"lang": lang, "title": title, "description": description, "topic_id": None}
            if document_topic is not None:
                self._json["topic_id"] = document_topic.topic_id

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


class ArchiveDocumentLocale:
    ...
