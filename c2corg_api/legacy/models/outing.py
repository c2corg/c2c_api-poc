from c2corg_api.legacy.models.document import Document as LegacyDocument, DocumentLocale as LegacyDocumentLocale
from c2corg_api.models import OUTING_TYPE


class ArchiveOuting:
    ...


class OutingLocale(LegacyDocumentLocale):
    ...


class Outing(LegacyDocument):
    def __init__(
        self,
        activities=None,
        date_start=None,
        date_end=None,
        geometry=None,
        elevation_max=None,
        elevation_min=None,
        height_diff_up=None,
        height_diff_down=None,
        version=None,
    ):
        super().__init__(version=version)

        if version is None:
            data = {
                "type": OUTING_TYPE,
                "quality": "draft",
                "activities": activities,
                "date_start": str(date_start),
                "date_end": str(date_end),
                "locales": {"fr": {"lang": "fr", "title": "..."}},
                "associations": {},
                "disable_comments": False,
            }

            if geometry is not None:
                data["geometry"] = geometry._json

            if elevation_max is not None:
                data["elevation_max"] = elevation_max
            if elevation_max is not None:
                data["elevation_min"] = elevation_min
            if elevation_max is not None:
                data["height_diff_up"] = height_diff_up
            if elevation_max is not None:
                data["height_diff_down"] = height_diff_down

            self.create_new_model(data=data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= {"disable_comments": legacy_document.pop("disable_comments", False)}

        # other props
        result["data"] |= legacy_document

        optional_attributes = [
            "access_condition",
            "avalanche_signs",
            "condition_rating",
            "elevation_access",
            "elevation_down_snow",
            "elevation_max",
            "elevation_min",
            "elevation_up_snow",
            "engagement_rating",
            "frequentation",
            "glacier_rating",
            "global_rating",
            "height_diff_difficulties",
            "height_diff_down",
            "height_diff_up",
            "hut_status",
            "length_total",
            "lift_status",
            "partial_trip",
            "participant_count",
            "public_transport",
            "snow_quality",
            "snow_quantity",
            "snowshoe_rating",
        ]

        for attribute in optional_attributes:
            if result["data"].get(attribute, None) is None:
                result["data"].pop(attribute, None)

        # TODO
        result["data"].pop("areas", None)

        return result

    @property
    def activities(self):
        return self._version.data["activities"]
