from c2corg_api.tests.conftest import BaseTestClass


class Test_User(BaseTestClass):
    def test_login_blocked_account(self, moderator, user):
        self.login_user(moderator, status=200)
        self.block_user(user, comment="Block him!")
        self.logout_user()

        self.login_user(user, status=200)
