from flask_camp.models import UserTag


class DocumentTag:
    def __init__(self, document_id, document_type, user_id):
        self._tag = UserTag(user_id=user_id, document_id=document_id, name="favorite")


class DocumentTagLog:
    def __init__(self, document_id, document_type, user_id, is_creation):
        pass
