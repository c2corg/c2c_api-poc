import pytest
from unittest.mock import Mock, MagicMock

from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.security.discourse_client import set_discourse_client, APIDiscourseClient
from c2corg_api.tests.legacy.views import BaseTestRest


class BaseBlockTest(BaseTestRest):
    def setup_method(self):
        super().setup_method()

        self.contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        self.contributor2 = self.query_get(User, user_id=self.global_userids["contributor2"])
        self.moderator = self.query_get(User, user_id=self.global_userids["moderator"])

        self.contributor2.blocked = True
        self.contributor2.ratelimit_times = 2

        self.session.commit()
        self.set_discourse_up()

    def set_discourse_client_mock(self, client):
        self.discourse_client = client
        set_discourse_client(client)

    def set_discourse_not_mocked(self):
        self.set_discourse_client_mock(self.original_discourse_client)

    def set_discourse_up(self):
        mock = Mock()
        mock.get_userid = MagicMock()
        mock.suspend = MagicMock()
        mock.unsuspend = MagicMock()
        self.set_discourse_client_mock(mock)

    def set_discourse_down(self):
        mock = APIDiscourseClient(self.settings)
        mock.get_userid = MagicMock(side_effect=Exception)
        self.set_discourse_client_mock(mock)

    def is_blocked(self, user_id):
        user = self.query_get(User, user_id=user_id)
        self.session_refresh(user)
        return user.blocked


class TestUserBlockRest(BaseBlockTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/block"

    def test_block_unauthorized(self):
        self.app_post_json(self._prefix, {}, status=403)

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, {}, headers=headers, status=403)

    def test_block(self):
        request_body = {"user_id": self.contributor.id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_blocked(self.contributor.id) is True

    def test_block_already_blocked_user(self):
        """Test that blocking an already blocked user does not raise an
        error.
        """
        request_body = {"user_id": self.contributor.id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_blocked(self.contributor.id) is True

    def test_block_discourse_error(self):
        self.set_discourse_down()

        request_body = {"user_id": self.contributor.id}

        headers = self.add_authorization_header(username="moderator")
        body = self.app_post_json(self._prefix, request_body, status=500, headers=headers)
        self.assertErrorsContain(body.json, "Internal Server Error")

        assert self.is_blocked(self.contributor.id) is False

    def test_block_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="moderator")
        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        assert self.get_body_error(body, "user_id") is not None


class TestUserUnblockRest(BaseBlockTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/unblock"

    def test_block_unauthorized(self):
        self.app_post_json(self._prefix, {}, status=403)

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, {}, headers=headers, status=403)

    def test_unblock(self):
        request_body = {"user_id": self.contributor2.id}
        assert self.is_blocked(self.contributor2.id) is True

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)
        assert self.is_blocked(self.contributor2.id) is False

    def test_unblock_not_blocked_user(self):
        """Test that unblocking a not blocked user does not raise an error."""
        request_body = {"user_id": self.contributor.id}

        headers = self.add_authorization_header(username="moderator")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_blocked(self.contributor.id) is False

    def test_unblock_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="moderator")
        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        assert self.get_body_error(body, "user_id") is not None

    def test_unblock_discourse_error(self):
        self.set_discourse_down()

        request_body = {"user_id": self.contributor2.id}
        assert self.is_blocked(self.contributor2.id) is True

        headers = self.add_authorization_header(username="moderator")
        body = self.app_post_json(self._prefix, request_body, status=500, headers=headers)
        self.assertErrorsContain(body.json, "Internal Server Error")

        assert self.is_blocked(self.contributor2.id) is True


@pytest.mark.skip(reason="Redundant, and not used in actual UI")
def TestUserBlockedRest(BaseBlockTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/blocked"

    def test_blocked_unauthorized(self):
        self.get(self._prefix + "/123", status=403, prefix="")

        headers = self.add_authorization_header(username="contributor")
        self.get(self._prefix, headers=headers, status=403, prefix="")

    def test_blocked(self):
        headers = self.add_authorization_header(username="moderator")
        response = self.get(self._prefix + "/{}".format(self.contributor2.id), status=200, headers=headers, prefix="")
        body = response.json

        assert body["blocked"] is True

    def test_blocked_not(self):
        headers = self.add_authorization_header(username="moderator")
        response = self.get(self._prefix + "/{}".format(self.contributor.id), status=200, headers=headers, prefix="")
        body = response.json

        assert body["blocked"] is False

    def test_blocked_invalid_user_id(self):
        headers = self.add_authorization_header(username="moderator")
        response = self.get(self._prefix + "/invalid-user-id", status=400, headers=headers, prefix="")

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("errors")
        assert self.get_error(errors, "id") is not None

    def test_blocked_wrong_user_id(self):
        headers = self.add_authorization_header(username="moderator")
        self.get(self._prefix + "/9999999999", status=400, headers=headers, prefix="")


@pytest.mark.skip(reason="Not used in actual UI")
def TestUserBlockedAllRest(BaseBlockTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/blocked"

    def test_blocked_unauthenticated(self):
        self.get(self._prefix, status=403, prefix="")

        headers = self.add_authorization_header(username="contributor")
        self.get(self._prefix, headers=headers, status=403, prefix="")

    def test_blocked(self):
        headers = self.add_authorization_header(username="moderator")
        response = self.get(self._prefix, status=200, headers=headers, prefix="")
        body = response.json

        blocked_users = body["blocked"]
        assert 1 == len(blocked_users)
        assert self.contributor2.id == blocked_users[0]["document_id"]
