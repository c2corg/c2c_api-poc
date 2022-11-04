import json
from c2corg_api.models import AREA_TYPE, USERPROFILE_TYPE, ARTICLE_TYPE


class DocumentRest:
    @staticmethod
    def create_new_version(document, author):
        last_version = document._document.last_version
        data = last_version.data
        if last_version.data["type"] == ARTICLE_TYPE:
            data |= {"author": {"user_id": author}}
        else:
            pass

        last_version._data = json.dumps(data)
