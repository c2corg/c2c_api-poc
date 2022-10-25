import pytest

from c2corg_api.tests.conftest import BaseTestClass


class Test_User(BaseTestClass):
    @pytest.mark.skip("TODO : set up discourse in dev env")
    def test_login_blocked_account(self, moderator, user):
        self.login_user(moderator, status=200)
        self.block_user(user, comment="Block him!")
        self.logout_user()

        self.login_user(user, status=200)

    @pytest.mark.skip("TODO : set up discourse in dev env")
    def test_login_discourse_success(self, user):
        self.login_user(user, status=200)
        r = self.get("/discourse/login_url").json
        assert "url" in r

    @pytest.mark.skip("TODO : set up discourse in dev env")
    def test_legacy_login(self, user):
        # this test was not performed in v6 test suite
        self.post("/users/login", prefix="", json={"username": user.name, "password": "password"}, status=200)
        r = self.get("/discourse/login_url").json
        assert "redirect_internal" in r
