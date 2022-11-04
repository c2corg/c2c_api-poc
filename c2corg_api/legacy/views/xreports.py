from flask_camp import allow

from c2corg_api.models import XREPORT_TYPE

from c2corg_api.legacy.views._document_core import DocumentCollectionView, DocumentView, VersionView


class XreportsView(DocumentCollectionView):
    rule = "/xreports"
    document_type = XREPORT_TYPE

    @allow("anonymous")
    def get(self):
        return super().get()


class XreportView(DocumentView):
    rule = "/xreports/<int:document_id>"
    document_type = XREPORT_TYPE


class XreportVersionView(VersionView):
    rule = "/xreports/<int:document_id>/<lang>/<int:version_id>"
    document_type = XREPORT_TYPE
