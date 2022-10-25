from c2corg_api.legacy.models.user import User
from c2corg_api.legacy.models.user_profile import UserProfile, ArchiveUserProfile, USERPROFILE_TYPE
from c2corg_api.tests.legacy.views import BaseDocumentTestRest
from c2corg_api.legacy.models.document import ArchiveDocumentLocale, DocumentLocale
from c2corg_api.legacy.views.document import DocumentRest


class TestUserProfileRest(BaseDocumentTestRest):
    def setup_method(self):
        self.set_prefix_and_model("/profiles", USERPROFILE_TYPE, UserProfile, ArchiveUserProfile, ArchiveDocumentLocale)
        BaseDocumentTestRest.setup_method(self)
        self._add_test_data()

    def test_get_collection_paginated(self):
        self.assertResultsEqual(self.get_collection({"offset": 0, "limit": 0}, user="contributor"), [], 7)

        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 1}, user="contributor"), [self.profile4.document_id], 7
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 0, "limit": 2}, user="contributor"),
            [self.profile4.document_id, self.profile3.document_id],
            7,
        )
        self.assertResultsEqual(
            self.get_collection({"offset": 1, "limit": 3}, user="contributor"),
            [self.profile3.document_id, self.profile2.document_id, self.global_userids["contributor3"]],
            7,
        )

    def _add_test_data(self):
        user_id = self.global_userids["contributor"]
        self.profile1 = self.query_get(UserProfile, user_id=user_id)
        self.locale_en = self.profile1.get_locale("en")
        self.locale_fr = self.profile1.get_locale("fr")
        DocumentRest.create_new_version(self.profile1, user_id)

        self.profile2 = UserProfile(categories=["amateur"])
        self.session_add(self.profile2)
        self.profile3 = UserProfile(categories=["amateur"])
        self.session_add(self.profile3)
        self.profile4 = UserProfile(categories=["amateur"])
        self.profile4.locales.append(DocumentLocale(lang="en", description="You", title=""))
        self.profile4.locales.append(DocumentLocale(lang="fr", description="Toi", title=""))
        self.session_add(self.profile4)

        self.session.flush()

        # create users for the profiles
        self.user2 = User(
            name="user2",
            username="user2",
            email="user2@c2c.org",
            forum_username="user2",
            password="pass",
            email_validated=True,
            profile=self.profile2,
        )
        self.user3 = User(
            name="user3",
            username="user3",
            email="user3@c2c.org",
            forum_username="user3",
            password="pass",
            email_validated=False,
            profile=self.profile3,
        )
        self.user4 = User(
            name="user4",
            username="user4",
            email="user4@c2c.org",
            forum_username="user4",
            password="pass",
            email_validated=True,
            profile=self.profile4,
        )
        self.session_add_all([self.user2, self.user3, self.user4])

        self.session.flush()
