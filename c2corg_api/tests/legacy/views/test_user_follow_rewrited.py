from unittest.mock import patch

from c2corg_api.tests.conftest import BaseTestClass


class BaseFollowTest(BaseTestClass):
    def is_following(self, followed_user, follower_user):
        user = self.get_user(follower_user).json["user"]
        return followed_user.id in user["ui_preferences"]["feed"]["follow"]

    def post(self, url, **kwargs):
        prefix = "" if url in ("/users/follow", "/users/unfollow") else "/v7"
        super().post(url, prefix=prefix, **kwargs)


class TestUserFollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.post("/users/follow", json={}, status=403)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_follow(self, sync_sso, user, user_2):
        self.login_user(user)
        self.post("/users/follow", json={"user_id": user_2.id}, status=200)
        assert self.is_following(follower_user=user, followed_user=user_2) is True

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_follow_already_followed_user(self, sync_sso, user, user_2):
        """Test that following an already followed user does not raise an error."""
        self.login_user(user)
        self.post("/users/follow", json={"user_id": user_2.id}, status=200)
        self.post("/users/follow", json={"user_id": user_2.id}, status=200)
        assert self.is_following(follower_user=user, followed_user=user_2) is True

    def test_follow_invalid_user_id(self, user):
        self.login_user(user)
        self.post("/users/follow", json={"user_id": -1}, status=404)


class TestUserUnfollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.post("/users/unfollow", json={}, status=403)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_unfollow(self, sync_sso, user, user_2):
        self.login_user(user)
        self.post("/users/unfollow", json={"user_id": user_2.id}, status=200)
        assert self.is_following(follower_user=user, followed_user=user_2) is False

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_unfollow_already_followed_user(self, sync_sso, user, user_2):
        """Test that following an already followed user does not raise an error."""
        self.login_user(user)
        self.post("/users/unfollow", json={"user_id": user_2.id}, status=200)
        self.post("/users/unfollow", json={"user_id": user_2.id}, status=200)
        assert self.is_following(follower_user=user, followed_user=user_2) is False

    def test_follow_invalid_user_id(self, user):
        self.login_user(user)
        self.post("/users/unfollow", json={"user_id": -1}, status=200)  # he's not followed, oso no error
