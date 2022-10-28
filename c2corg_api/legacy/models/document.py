class Document:
    def __init__(self):
        self._document = None

    def create_new_model(self, data):
        from flask_camp.models import Document

        self._document = Document.create(comment="Creation", data=data, author=self.default_author)

    @property
    def default_author(self):
        from flask_camp.models import User

        return User.query.first()

    @property
    def version(self):
        return self._document.last_version_id

    @property
    def document_id(self):
        return self._document.id

    @property
    def locales(self):
        return LocaleDictProxy(self._document.last_version.data["locales"])

    @property
    def geometry(self):
        return DocumentGeometry(self._document.last_version.data["geometry"])

    def get_locale(self, lang):
        return self.locales.get_locale(lang)


class DocumentGeometry:
    def __init__(self, json):
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


class ArchiveDocumentLocale:
    ...
