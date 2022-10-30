from flask_camp import current_api
from flask_camp.models import User, Document
from sqlalchemy import select

from c2corg_api.models import get_default_user_profile_data, ProfilePageLink, USERPROFILE_TYPE  # Do not remove
from c2corg_api.legacy.models.document import Document as LegacyDocument


class UserProfile(LegacyDocument):
    def __init__(self, categories=None, locale_langs=None, document=None):
        super().__init__(document=document)
        self._user = None

        if categories and document is None:
            self.create_new_model(
                data=get_default_user_profile_data(
                    self.default_author, categories=categories, locale_langs=locale_langs or []
                )
            )

    @staticmethod
    def from_document_id(profile_document_id):
        query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == profile_document_id)
        result = current_api.database.session.execute(query)
        user_id = list(result)[0][0]

        result = UserProfile()
        result._user = User.get(id=user_id)

        result._document = Document.get(id=profile_document_id)
        result._versions = list(result._document.versions)

        return result

    @property
    def user(self):
        from c2corg_api.legacy.models.user import User as LegacyUser

        return LegacyUser.from_user(User.get(id=self._document.last_version.data["user_id"]))

    @property
    def categories(self):
        return self._document.last_version.data["categories"]


class ArchiveUserProfile:
    ...
