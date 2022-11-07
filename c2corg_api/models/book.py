class Book:
    @classmethod
    def on_creation(cls, version):
        ...

    @classmethod
    def on_new_version(cls, old_version, new_version):
        ...
