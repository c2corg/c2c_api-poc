from flask_camp import allow
from flask_login import current_user
from c2corg_api.models import XREPORT_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView
from c2corg_api.models.xreport import Xreport


class XreportsView(DocumentCollectionView):
    rule = "/xreports"
    document_type = XREPORT_TYPE

    @allow("anonymous", "authenticated")
    def get(self):
        return super().get()


class XreportView(DocumentView):
    rule = "/xreports/<int:document_id>"
    document_type = XREPORT_TYPE

    @allow("anonymous", "authenticated")
    def get(self, document_id):
        result = super().get(document_id)

        if result.data["author"]["user_id"] != current_user.id and not current_user.is_moderator:
            for field in Xreport.private_fields:
                result.data.pop(field)

        return result


class XreportVersionView(VersionView):
    rule = "/xreports/<int:document_id>/<lang>/<int:version_id>"
    document_type = XREPORT_TYPE

    @allow("anonymous", "authenticated")
    def get(self, document_id, lang, version_id):
        result = super().get(document_id, lang, version_id)

        if result.data["document"]["author"]["user_id"] != current_user.id and not current_user.is_moderator:
            for field in Xreport.private_fields:
                result.data["document"].pop(field)

        return result
