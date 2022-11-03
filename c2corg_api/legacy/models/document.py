from c2corg_api.schemas import schema_validator


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
    def document_geometry_archive(self):
        return Geometry(self._version.data.get("geometry", {}))


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
        return LocaleDictProxy(self._document.last_version.data["locales"])

    @property
    def geometry(self):
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
    def __init__(self, json):
        self._json = json

    def append(self, locale):
        self._json[locale.lang] = locale.to_json()

    def get_locale(self, lang):
        result = self._json.get(lang)

        return None if result is None else DocumentLocale(json=result)

    def __len__(self):
        return len(self._json)

    def __str__(self):
        return str(self._json)


class DocumentLocale:
    def __init__(self, lang=None, title=None, description="", json=None):
        if json is not None:
            self._json = json
        else:
            self._json = {"lang": lang, "title": title, "description": description}

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
