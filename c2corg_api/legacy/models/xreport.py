from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale
from c2corg_api.models import XREPORT_TYPE


class XreportLocale(DocumentLocale):
    def __init__(self, lang=None, title="", description="", json=None):
        super().__init__(lang=lang, title=title, description=description, json=json)


class ArchiveXreportLocale:
    ...


class ArchiveXreport:
    ...


class Xreport(LegacyDocument):
    def __init__(self, activities=None, xreport_types=None, document=None):
        super().__init__(document=document)

        if document is None:
            self.create_new_model(
                data={
                    "type": XREPORT_TYPE,
                    "quality": "draft",
                    # "activities": activities,
                    # "xreport_types": xreport_types,
                    "locales": {"fr": {"lang": "fr", "title": "..."}},
                    "associations": [],
                }
            )

    # @property
    # def activities(self):
    #     return self._document.last_version.data["activities"]

    # @property
    # def xreport_types(self):
    #     return self._document.last_version.data["xreport_types"]
