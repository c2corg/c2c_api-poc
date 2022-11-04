from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale
from c2corg_api.models import XREPORT_TYPE


class XreportLocale(DocumentLocale):
    def __init__(self, lang=None, title="", description="", place="", json=None):
        super().__init__(lang=lang, title=title, description=description, json=json)
        self._json["place"] = place


class ArchiveXreportLocale:
    ...


class ArchiveXreport:
    ...


class Xreport(LegacyDocument):
    def __init__(
        self,
        event_activity=None,
        event_type=None,
        nb_participants=None,
        nb_impacted=None,
        age=None,
        date=None,
        document=None,
    ):
        super().__init__(document=document)

        if document is None:
            data = {
                "type": XREPORT_TYPE,
                "quality": "draft",
                "event_activity": event_activity,
                "event_type": event_type,
                "locales": {"fr": {"lang": "fr", "title": "..."}},
                "associations": [],
            }

            if nb_participants is not None:
                data["nb_participants"] = nb_participants

            if nb_impacted is not None:
                data["nb_impacted"] = nb_impacted

            if age is not None:
                data["age"] = age

            self.create_new_model(data=data)

    # @property
    # def activities(self):
    #     return self._document.last_version.data["activities"]

    # @property
    # def xreport_types(self):
    #     return self._document.last_version.data["xreport_types"]
