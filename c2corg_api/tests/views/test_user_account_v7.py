import pytest

from c2corg_api.tests.conftest import BaseTestClass


class TestUserAccountRest(BaseTestClass):
    def test_read_account_info_blocked_account(self, moderator, user):
        self.login_user(moderator)
        self.block_user(user, comment="block him")

        self.login_user(user)
        self.get_current_user(status=200)
