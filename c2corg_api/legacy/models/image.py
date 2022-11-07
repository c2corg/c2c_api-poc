from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.models import IMAGE_TYPE


class Image(LegacyDocument):
    def __init__(self, filename=None, activities=None, height=1500, image_type="collaborative", version=None):
        super().__init__(version=version)

        if version is None:
            self.create_new_model(
                data={
                    "type": IMAGE_TYPE,
                    "quality": "draft",
                    "activities": activities,
                    "height": height,
                    "width": None,
                    "filename": filename,
                    "locales": {},
                    "associations": [],
                    "image_type": image_type,
                }
            )
