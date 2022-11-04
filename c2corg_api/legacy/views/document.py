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
