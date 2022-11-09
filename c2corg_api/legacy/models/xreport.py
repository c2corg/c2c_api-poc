import json
from flask_login import current_user

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
        version=None,
    ):
        super().__init__(version=version)

        if version is None:
            data = {
                "anonymous": False,
                "type": XREPORT_TYPE,
                "date": str(date) if date is not None else None,
                "quality": "draft",
                "event_activity": event_activity,
                "event_type": event_type,
                "locales": {"fr": {"lang": "fr", "title": "..."}},
                "associations": [],
                "author": {"user_id": 666},
            }

            if nb_participants is not None:
                data["nb_participants"] = nb_participants

            if nb_impacted is not None:
                data["nb_impacted"] = nb_impacted

            if age is not None:
                data["age"] = age

            self.create_new_model(data=data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {
            "quality": legacy_document.pop("quality", "draft"),
            "author": legacy_document.pop("author", previous_data.get("author", "MISSING_AUTHOR")),
            "anonymous": legacy_document.pop("anonymous", previous_data.get("anonymous", False)),
        }

        if "geometry" in legacy_document:
            result["data"]["geometry"] = {"geom": json.loads(legacy_document["geometry"]["geom"])}

        optionnal_properties = ["date", "supervision", "rescue"]
        for prop in optionnal_properties:
            if prop in legacy_document and legacy_document[prop] is None:
                legacy_document.pop(prop)

            elif prop in legacy_document or prop in previous_data:
                result["data"][prop] = legacy_document.pop(prop, previous_data.get(prop, None))

        # other props
        result["data"] |= legacy_document

        result["data"].pop("nb_outings", None)
        result["data"].pop("areas", None)

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        result = LegacyDocument.convert_to_legacy_doc(document)
        data = document["data"]

        result |= {
            "author": data["author"],
            "event_activity": data["event_activity"],
            "event_type": data["event_type"],
            "nb_participants": data.get("nb_participants"),
            "nb_impacted": data.get("nb_impacted"),
            "rescue": data.get("rescue"),
        }

        if "geometry" in data:
            result["geometry"] = {"geom": json.dumps(data["geometry"]["geom"])}
        else:
            result["geometry"] = None

        if "date" in data:
            result["date"] = data["date"]

        if "supervision" in data:
            result["supervision"] = data["supervision"]

        # private field
        for field in ["author_status", "activity_rate", "age", "gender", "previous_injuries", "autonomy"]:
            if field in data:
                result[field] = data[field]
            elif current_user.is_moderator or current_user.id == data["author"]["user_id"]:
                # in old model, empty values are reported as none
                result[field] = None

        if result["geometry"] is not None:
            result["geometry"] |= {"version": 0}

        return result

    @property
    def event_type(self):
        return self._version.data["event_type"]

    @property
    def event_activity(self):
        return self._version.data["event_activity"]

    @property
    def nb_impacted(self):
        return self._version.data["nb_impacted"]

    @property
    def nb_participants(self):
        return self._version.data["nb_participants"]

    @property
    def autonomy(self):
        return self._version.data["autonomy"]

    @property
    def activity_rate(self):
        return self._version.data["activity_rate"]

    @property
    def supervision(self):
        return self._version.data["supervision"]

    @property
    def age(self):
        return self._version.data["age"]

    @property
    def qualification(self):
        return self._version.data["qualification"]
