from flask_camp import current_api
from flask_camp.models import User, Document
from c2corg_api.app import ProfilePageLink
from c2corg_api.models import USERPROFILE_TYPE
from sqlalchemy import select


class UserProfile:
    def __init__(self, profile_document_id) -> None:
        query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == profile_document_id)
        result = current_api.database.session.execute(query)
        user_id = list(result)[0][0]
        self._user = User.get(id=user_id)

        self._profile_page = Document.get(id=profile_document_id)
        self._versions = list(self._profile_page.versions)

    @property
    def versions(self):
        return self._versions
