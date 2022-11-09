class DocumentVersion:
    ...


class HistoryMetaData:
    def __init__(self, version):
        self._version = version

    @property
    def id(self):
        return self._version.data["version_id"]

    @property
    def document_id(self):
        return self._version.data["document_id"]

    @property
    def user_id(self):
        return self._version.data["author"]["user_id"]
