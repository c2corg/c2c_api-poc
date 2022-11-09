from flask_camp import current_api
from flask_camp.models import User, Document
from sqlalchemy import select

from c2corg_api.models.userprofile import UserProfile as NewUserProfile, USERPROFILE_TYPE  # Do not remove
from c2corg_api.legacy.models.document import Document as LegacyDocument
from c2corg_api.search import DocumentSearch


class UserProfile(LegacyDocument):
    def __init__(self, categories=None, locale_langs=None, version=None):
        super().__init__(version=version)
        self._user = None

        if version is None:
            self.create_new_model(
                data=NewUserProfile.get_default_data(
                    self.default_author, categories=categories, locale_langs=locale_langs or []
                )
            )

    @staticmethod
    def from_document_id(profile_document_id):
        query = select(DocumentSearch.user_id).where(DocumentSearch.id == profile_document_id)
        result = current_api.database.session.execute(query)
        user_id = list(result)[0][0]

        result = UserProfile(version=Document.get(id=profile_document_id).last_version)

        result._user = User.get(id=user_id)

        result._versions = list(result._version.document.versions)

        return result

    @staticmethod
    def convert_from_legacy_doc(legacy_document, document_type, previous_data):
        result = LegacyDocument.convert_from_legacy_doc(legacy_document, document_type, previous_data)

        for locale in result["data"]["locales"].values():
            locale.pop("version", None)
            locale.pop("title", None)
            locale.pop("topic_id", None)

        result["data"] |= {
            "areas": legacy_document.pop("areas", {}),
            "name": legacy_document.pop("name", previous_data["name"]),
        }

        # clean
        legacy_document.pop("quality", None)

        # other props
        result["data"] |= legacy_document

        return result

    @staticmethod
    def convert_to_legacy_doc(document):
        result = LegacyDocument.convert_to_legacy_doc(document)

        data = document["data"]

        result |= {
            "name": data["name"],
            "forum_username": data["name"],
            "areas": data["areas"],
        }
        for locale in result["locales"]:
            locale["topic_id"] = None

        return result

    @property
    def user(self):
        from c2corg_api.legacy.models.user import User as LegacyUser

        return LegacyUser.from_user(User.get(id=self._version.data["user_id"]))

    @property
    def categories(self):
        return self._version.data["categories"]


class ArchiveUserProfile:
    ...
