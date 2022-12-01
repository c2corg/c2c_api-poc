from c2corg_api.models import AREA_TYPE
from c2corg_api.legacy.models.document import Document as LegacyDocument


class Area(LegacyDocument):
    def __init__(self, area_type, locales=None):
        super().__init__()
        data = {
            "type": AREA_TYPE,
            "area_type": area_type,
            "associations": {},
        }

        if locales is None:
            data["locales"] = {"fr": {"lang": "fr", "title": "..."}}
        else:
            data["locales"] = {locale.lang: locale._json for locale in locales}

        self.create_new_model(data=data)


class ArchiveArea:
    ...
