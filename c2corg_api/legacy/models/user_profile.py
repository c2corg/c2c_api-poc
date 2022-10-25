from flask_camp import current_api
from flask_camp.models import User, Document
from sqlalchemy import select

from c2corg_api.models import get_default_user_profile_data
from c2corg_api.hooks import ProfilePageLink
from c2corg_api.models import USERPROFILE_TYPE  # Do not remove


class LocaleArrayProxy:
    def __init__(self, document):
        self._document = document

    def append(self, locale):
        self._document.last_version.data["locales"].append(locale.to_json())


class UserProfile:
    def __init__(self, categories=None):
        self._document = None
        self._user = None
        self.locales = None

        if categories:
            author = User.get(id=1)
            data = get_default_user_profile_data(author, categories=categories)
            self._document = Document.create("comment", data=data, author=author)
            self.locales = LocaleArrayProxy(self._document)

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
    def versions(self):
        return self._versions

    def get_locale(self, lang):
        ...


class ArchiveUserProfile:
    ...
