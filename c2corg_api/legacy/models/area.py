from flask_camp.models import Document, User
from c2corg_api.models import AREA_TYPE


class Area:
    def __init__(self, area_type, locales):
        data = {"type": AREA_TYPE, "area_type": area_type, "locales": [locale.to_json() for locale in locales]}

        self._document = Document.create(comment="Creation", data=data, author=User.query.first())

    @property
    def document_id(self):
        return self._document.id
