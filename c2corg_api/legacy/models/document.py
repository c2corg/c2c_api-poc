class DocumentLocale:
    def __init__(self, lang, title, description=""):
        self._data = {"lang": lang, "title": title, "description": description}

    def to_json(self):
        return self._data

    @property
    def lang(self):
        return self._data["lang"]


class ArchiveDocumentLocale:
    ...
