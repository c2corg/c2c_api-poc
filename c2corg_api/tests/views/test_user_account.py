from unittest.mock import patch
from c2corg_api.tests.conftest import BaseTestClass


class TestUserAccountRest(BaseTestClass):
    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.suspend")
    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_read_account_info_blocked_account(self, suspend, sync_sso, moderator, user):
        self.login_user(moderator)
        self.block_user(user, comment="block him")

        self.login_user(user)
        self.get_current_user(status=200)
