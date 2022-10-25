import pytest
from c2corg_api.legacy.models.feed import FollowedUser
from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.views.user_follow import get_follower_relation


class BaseFollowTest(BaseTestRest):
    def setup_method(self):
        super().setup_method()

        self.contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        self.contributor2 = self.query_get(User, user_id=self.global_userids["contributor2"])
        self.moderator = self.query_get(User, user_id=self.global_userids["moderator"])

        self.session.add(FollowedUser(followed_user_id=self.contributor2.id, follower_user_id=self.contributor.id))

        self.session.flush()

    def is_following(self, followed_user_id, follower_user_id):
        return get_follower_relation(followed_user_id, follower_user_id) is not None


@pytest.mark.skip(reason="PITA, rewrite it")
def TestUserFollowRest(BaseFollowTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/follow"

    def test_follow_unauthenticated(self):
        self.app_post_json(self._prefix, {}, status=403)

    def test_follow(self):
        request_body = {"user_id": self.moderator.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_following(self.moderator.id, self.contributor.id) is True

    def test_follow_already_followed_user(self):
        """Test that following an already followed user does not raise an
        error.
        """
        request_body = {"user_id": self.contributor2.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_following(self.contributor2.id, self.contributor.id) is True

    def test_follow_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        assert self.get_body_error(body, "user_id") is not None


@pytest.mark.skip(reason="PITA, rewrite it")
def TestUserUnfollowRest(BaseFollowTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/unfollow"

    def test_follow_unauthenticated(self):
        self.app_post_json(self._prefix, {}, status=403)

    def test_unfollow(self):
        request_body = {"user_id": self.contributor2.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_following(self.moderator.id, self.contributor.id) is False

    def test_unfollow_not_followed_user(self):
        """Test that unfollowing a not followed user does not raise an error."""
        request_body = {"user_id": self.moderator.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        assert self.is_following(self.moderator.id, self.contributor.id) is False

    def test_follow_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        assert self.get_body_error(body, "user_id") is not None


@pytest.mark.skip(reason="Not used in actual UI")
def TestUserFollowingUserRest(BaseFollowTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/following-user"

    def test_follow_unauthenticated(self):
        self.get(self._prefix + "/123", status=403)

    def test_following(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix + "/{}".format(self.contributor2.id), status=200, headers=headers)
        body = response.json

        assert body["is_following"] is True

    def test_following_not(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix + "/{}".format(self.moderator.id), status=200, headers=headers)
        body = response.json

        assert body["is_following"] is False

    def test_following_invalid_user_id(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix + "/invalid-user-id", status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("errors")
        assert self.get_error(errors, "id") is not None

    def test_following_wrong_user_id(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix + "/9999999999", status=200, headers=headers)
        body = response.json

        assert body["is_following"] is False


@pytest.mark.skip(reason="Not used in actual UI")
def TestUserFollowingRest(BaseFollowTest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/following"

    def test_follow_unauthenticated(self):
        self.get(self._prefix, status=403)

    def test_following(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix, status=200, headers=headers)
        body = response.json

        following_users = body["following"]
        assert 1 == len(following_users)
        assert self.contributor2.id == following_users[0]["document_id"]

    def test_following_empty(self):
        headers = self.add_authorization_header(username="contributor2")
        response = self.get(self._prefix, status=200, headers=headers)
        body = response.json

        following_users = body["following"]
        assert 0 == len(following_users)
