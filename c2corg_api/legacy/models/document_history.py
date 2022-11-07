class DocumentVersion:
    ...

class HistoryMetaData:
    def __init__(self, version):
        self._version = version

    @property
    def user_id(self):
        return self._version.data["author"]["user_id"] 
