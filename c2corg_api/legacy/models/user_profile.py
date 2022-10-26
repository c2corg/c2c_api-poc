from flask_camp import current_api
from flask_camp.models import User, Document
from sqlalchemy import select

from c2corg_api.models import get_default_user_profile_data, ProfilePageLink
from c2corg_api.models import USERPROFILE_TYPE  # Do not remove


class LocaleProxy:
    def __init__(self, json):
        self._json = json

    @property
    def lang(self):
        return self._json["lang"]


class LocaleArrayProxy:
    def __init__(self, document):
        self._document = document

    def append(self, locale):
        item = locale.to_json()
        locales = self._document.last_version.data["locales"]
        locales = [locale for locale in locales if locale["lang"] != item["lang"]]
        locales.append(item)
        self._document.last_version.data["locales"] = locales

    def get_locale(self, lang):
        for locale in self._document.last_version.data["locales"]:
            if locale["lang"] == lang:
                return LocaleProxy(locale)


class UserProfile:
    def __init__(self, categories=None, locale_langs=None):
        self._document = None
        self._user = None

        if categories:
            author = User.get(id=1)
            data = get_default_user_profile_data(author, categories=categories, locale_langs=locale_langs or [])
            self._document = Document.create("comment", data=data, author=author)

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
    def document_id(self):
        return self._document.id

    @property
    def versions(self):
        return self._versions

    @property
    def locales(self):
        return LocaleArrayProxy(self._document)

    def get_locale(self, lang):
        return self.locales.get_locale(lang)

    @property
    def user(self):
        from c2corg_api.legacy.models.user import User as LegacyUser

        return LegacyUser.from_user(User.get(id=self._document.last_version.data["user_id"]))


class ArchiveUserProfile:
    ...
