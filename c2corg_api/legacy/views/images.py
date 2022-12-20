from flask_camp import allow

from c2corg_api.models import IMAGE_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class ImagesView(DocumentCollectionView):
    rule = "/images"
    document_type = IMAGE_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class ImageView(DocumentView):
    rule = "/images/<int:document_id>"
    document_type = IMAGE_TYPE


class ImageVersionView(VersionView):
    rule = "/images/<int:document_id>/<lang>/<int:version_id>"
    document_type = IMAGE_TYPE
