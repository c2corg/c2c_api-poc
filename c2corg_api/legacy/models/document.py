from c2corg_api.schemas import schema_validator
from c2corg_api.models import USERPROFILE_TYPE, ARTICLE_TYPE


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
        return LocaleDictProxy(json=self._version.data["locales"], document_type=self._document_type).get_locale(
            "en"
        )  # damn :(

    @property
    def categories(self):
        return self._get_attribute("categories", {ARTICLE_TYPE: "categories"})

    @property
    def activities(self):
        return self._get_attribute("activities", {ARTICLE_TYPE: "activities"})

    @property
    def article_type(self):
        return self._get_attribute("article_type", {ARTICLE_TYPE: "article_type"})

    def _get_attribute(self, attribute_name, mapping):
        if self._document_type not in mapping:
            raise AttributeError(f"'{DocumentArchive}' has no attribute '{attribute_name}' for {self._document_type}")

        return self._version.data[mapping[self._document_type]]


class Document:
    def __init__(self, document=None):
        self._document = document

    def create_new_model(self, data):
        from flask_camp.models import Document

        schema_validator.validate(data, f"{data['type']}.json")

        self._document = Document.create(comment="Creation", data=data, author=self.default_author)

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
        return LocaleDictProxy(self._document.last_version.data["locales"], self.type)

    @property
    def geometry(self):
        if "geometry" not in self._document.last_version.data:
            return None

        return DocumentGeometry(json=self._document.last_version.data["geometry"])

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
    def __init__(self, json, document_type):
        self._json = json
        self._document_type = document_type

    def append(self, locale):
        locale.set_document_type(self._document_type)
        self._json[locale.lang] = locale.to_json()

    def get_locale(self, lang):
        result = self._json.get(lang)

        return None if result is None else DocumentLocale(json=result)

    def __len__(self):
        return len(self._json)

    def __str__(self):
        return str(self._json)

    def __getitem__(self, i):
        json = list(self._json.values())[i]
        return DocumentLocale(json=json)


class DocumentLocale:
    def __init__(self, lang=None, title=None, description="", json=None):
        if json is not None:
            self._json = json
        else:
            self._json = {"lang": lang, "title": title, "description": description, "topic_id": None}

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
