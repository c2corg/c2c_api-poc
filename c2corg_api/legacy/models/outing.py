from c2corg_api.legacy.models.document import (
    Document as LegacyDocument,
    DocumentLocale as LegacyDocumentLocale,
    DocumentGeometry,
)
from c2corg_api.models import OUTING_TYPE


class ArchiveOuting:
    ...


class OutingLocale(LegacyDocumentLocale):
    ...


class ArchiveOutingLocale:
    ...


class Outing(LegacyDocument):
    def __init__(
        self,
        activities=None,
        date_start=None,
        date_end=None,
        geometry=None,
        condition_rating=None,
        elevation_max=None,
        elevation_min=None,
        elevation_access=None,
        height_diff_up=None,
        height_diff_down=None,
        locales=None,
        public_transport=None,
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
                "associations": {},
                "disable_comments": False,
            }

            if locales is None:
                data["locales"] = {"fr": {"lang": "fr", "title": "default title"}}
            else:
                data["locales"] = {locale.lang: locale._json for locale in locales}

            if geometry is not None:
                data["geometry"] = geometry._json
            else:
                data["geometry"] = DocumentGeometry(geom="SRID=3857;POINT(0 0)")._json

            if condition_rating is not None:
                data["condition_rating"] = condition_rating
            if elevation_access is not None:
                data["elevation_access"] = elevation_access
            if elevation_max is not None:
                data["elevation_max"] = elevation_max
            if elevation_min is not None:
                data["elevation_min"] = elevation_min
            if height_diff_up is not None:
                data["height_diff_up"] = height_diff_up
            if height_diff_down is not None:
                data["height_diff_down"] = height_diff_down
            if public_transport is not None:
                data["public_transport"] = public_transport

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
