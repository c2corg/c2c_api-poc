import json
from c2corg_api.models import ARTICLE_TYPE, XREPORT_TYPE


class DocumentRest:
    @staticmethod
    def create_new_version(document, author):
        last_version = document._document.last_version
        data = last_version.data
        if last_version.data["type"] in (ARTICLE_TYPE, XREPORT_TYPE):
            data |= {"author": {"user_id": author}}
        else:
            pass

        last_version._data = json.dumps(data)

    @staticmethod
    def update_version(document, user_id, comment, update_types, changed_langs):
        from flask_camp.models import Document, DocumentVersion, User
        from flask_camp import current_api

        document = document._document

        version = DocumentVersion(
            document=document,
            user=User.get(id=user_id),
            comment=comment,
            data=document.last_version.data,
        )

        current_api.database.session.add(version)
        document.last_version = version
