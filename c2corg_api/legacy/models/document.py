class DocumentLocale:
    def __init__(self, lang, title):
        self._data = {"lang": lang, "title": title}

    def to_json(self):
        return self._data
