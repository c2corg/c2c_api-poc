from c2corg_api.models.userprofile import UserProfile
from c2corg_api.tests.conftest import BaseTestClass


class Test_UserProfile(BaseTestClass):
    def test_cant_create(self, user):
        """profile page can't be created on their own"""
        self.login_user(user)

        data = UserProfile.get_default_data(user, categories=[], locale_langs=[])
        r = self.create_document(data, "comment", status=400).json

        assert r["description"] == "Profile page can't be created without an user"
