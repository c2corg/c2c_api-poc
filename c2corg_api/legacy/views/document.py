from copy import deepcopy

from flask_camp.models import DocumentVersion, User
from flask_camp import current_api
from sqlalchemy.orm.attributes import flag_modified

from c2corg_api.models import ARTICLE_TYPE, XREPORT_TYPE


class DocumentRest:

    # on v6, a document can be created and exists without a version.
    # it's not the case here, when a document is created, a first version must exists
    # on first call of create_new_version() for a given document, we do nothing as
    # the version still exists. On any other call, we actually create new versions

    create_new_version_called = set()

    @staticmethod
    def create_new_version(document, author):
        last_version = document._document.last_version

        if id(document) not in DocumentRest.create_new_version_called:
            DocumentRest.create_new_version_called.add(id(document))

            if last_version.data["type"] in (ARTICLE_TYPE, XREPORT_TYPE):
                last_version.data |= {"author": {"user_id": author}}
                flag_modified(last_version, "data")

        else:
            version = DocumentVersion(
                document=document._document,
                user=User.get(id=author),
                comment="no comment",
                data=deepcopy(last_version.data),
            )

            document._document.last_version = version
            document._version = version
            current_api.database.session.add(last_version)
            current_api.database.session.add(version)

    @staticmethod
    def update_version(document, user_id, comment, update_types, changed_langs):
        document._document.last_version.comment = comment
