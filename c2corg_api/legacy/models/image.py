from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import IMAGE_TYPE


class Image(LegacyDocument):
    def __init__(
        self,
        filename=None,
        activities=None,
        height=1500,
        image_type="collaborative",
        locales=None,
        geometry=None,
        version=None,
    ):
        super().__init__(version=version)

        if version is None:
            data = {
                "type": IMAGE_TYPE,
                "quality": "draft",
                "activities": activities if activities is not None else [],
                "height": height,
                "width": None,
                "filename": filename,
                "locales": {} if locales is None else {l.lang: l._json for l in locales},
                "associations": {},
                "image_type": image_type,
            }

            if geometry is not None:
                data["geometry"] = geometry._json

            self.create_new_model(data=data)

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        result["data"] |= legacy_document

        for attribute in ["elevation", "author"]:
            if attribute in result["data"] and result["data"][attribute] is None:
                del result["data"][attribute]

        if "areas" in result["data"]:
            del result["data"]["areas"]  # TODO

        return result


class ArchiveImage:
    ...
