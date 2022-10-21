from flask_camp.models import Document, User


class Area:
    def __init__(self, area_type, locales):
        data = {"area_type": area_type, "locales": [locale.to_json() for locale in locales]}

        self._document = Document.create(comment="Creation", data=data, author=User.query.first())
