from copy import deepcopy
from unittest.mock import patch

from flask_camp.models import Document

from c2corg_api.tests.conftest import BaseTestClass


class BaseFollowTest(BaseTestClass):
    def is_following(self, followed_user, follower_user):
        user = self.get_user(follower_user).json["user"]
        assert followed_user.id in user["ui_preferences"]["feed"]["follow"]


class TestUserFollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.post("/users/follow", json={}, status=403)

    def test_follow(self, user, user_2):
        self.login_user(user)
        self.post("/users/follow", json={"user_id": user_2.id}, status=200)
        assert self.is_following(follower_user=user, followed_user=user_2) is True

    def test_follow_already_followed_user(self):
        """Test that following an already followed user does not raise an
        error.
        """
        request_body = {"user_id": self.contributor2.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json("/users/follow", request_body, status=200, headers=headers)

        self.assertTrue(self.is_following(self.contributor2.id, self.contributor.id))

    def test_follow_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json("/users/follow", request_body, status=400, headers=headers)

        body = response.json
        self.assertEqual(body.get("status"), "error")
        errors = body.get("errors")
        self.assertIsNotNone(self.get_error(errors, "user_id"))


class TestUserUnfollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.app_post_json("/users/follow", {}, status=403)

    def test_unfollow(self):
        request_body = {"user_id": self.contributor2.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json("/users/follow", request_body, status=200, headers=headers)

        self.assertFalse(self.is_following(self.moderator.id, self.contributor.id))

    def test_unfollow_not_followed_user(self):
        """Test that unfollowing a not followed user does not raise an error."""
        request_body = {"user_id": self.moderator.id}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json("/users/follow", request_body, status=200, headers=headers)

        self.assertFalse(self.is_following(self.moderator.id, self.contributor.id))

    def test_follow_invalid_user_id(self):
        request_body = {"user_id": -1}

        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json("/users/follow", request_body, status=400, headers=headers)

        body = response.json
        self.assertEqual(body.get("status"), "error")
        errors = body.get("errors")
        self.assertIsNotNone(self.get_error(errors, "user_id"))


class TestUserFollowingUserRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.app.get("/users/follow" + "/123", status=403)

    def test_following(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.app.get("/users/follow" + "/{}".format(self.contributor2.id), status=200, headers=headers)
        body = response.json

        self.assertTrue(body["is_following"])

    def test_following_not(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.app.get("/users/follow" + "/{}".format(self.moderator.id), status=200, headers=headers)
        body = response.json

        self.assertFalse(body["is_following"])

    def test_following_invalid_user_id(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.app.get("/users/follow" + "/invalid-user-id", status=400, headers=headers)

        body = response.json
        self.assertEqual(body.get("status"), "error")
        errors = body.get("errors")
        self.assertIsNotNone(self.get_error(errors, "id"))

    def test_following_wrong_user_id(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.app.get("/users/follow" + "/9999999999", status=200, headers=headers)
        body = response.json

        self.assertFalse(body["is_following"])


class TestUserFollowingRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.app.get("/users/follow", status=403)

    def test_following(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.app.get("/users/follow", status=200, headers=headers)
        body = response.json

        following_users = body["following"]
        self.assertEqual(1, len(following_users))
        self.assertEqual(self.contributor2.id, following_users[0]["document_id"])

    def test_following_empty(self):
        headers = self.add_authorization_header(username="contributor2")
        response = self.app.get("/users/follow", status=200, headers=headers)
        body = response.json

        following_users = body["following"]
        self.assertEqual(0, len(following_users))
