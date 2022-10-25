from unittest.mock import patch

from c2corg_api.tests.legacy.views import BaseTestRest


class BaseFollowTest(BaseTestRest):
    def is_following(self, followed_user_id, follower_user_id):
        user = self.get(f"/v7/user/{follower_user_id}").json["user"]
        return followed_user_id in user["ui_preferences"]["feed"]["follow"]


class TestUserFollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.post("/users/follow", json={}, status=403)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_follow(self, sync_sso):
        user_id = self.global_userids["contributor"]
        user2_id = self.global_userids["contributor2"]

        self.optimized_login("contributor")

        self.post("/users/follow", json={"user_id": user2_id}, status=200)
        assert self.is_following(follower_user_id=user_id, followed_user_id=user2_id) is True

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_follow_already_followed_user(self, sync_sso):
        """Test that following an already followed user does not raise an error."""
        user_id = self.global_userids["contributor"]
        user2_id = self.global_userids["contributor2"]

        self.optimized_login("contributor")

        self.post("/users/follow", json={"user_id": user2_id}, status=200)
        self.post("/users/follow", json={"user_id": user2_id}, status=200)
        assert self.is_following(follower_user_id=user_id, followed_user_id=user2_id) is True

    def test_follow_invalid_user_id(self, user):
        self.optimized_login("contributor")
        self.post("/users/follow", json={"user_id": -1}, status=404)


class TestUserUnfollowRest(BaseFollowTest):
    def test_follow_unauthenticated(self):
        self.post("/users/unfollow", json={}, status=403)

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_unfollow(self, sync_sso):
        user_id = self.global_userids["contributor"]
        user2_id = self.global_userids["contributor2"]

        self.optimized_login("contributor")

        self.post("/users/unfollow", json={"user_id": user2_id}, status=200)
        assert self.is_following(follower_user_id=user_id, followed_user_id=user2_id) is False

    @patch("c2corg_api.security.discourse_client.APIDiscourseClient.sync_sso")
    def test_unfollow_already_followed_user(self, sync_sso):
        """Test that following an already followed user does not raise an error."""
        user_id = self.global_userids["contributor"]
        user2_id = self.global_userids["contributor2"]

        self.optimized_login("contributor")

        self.post("/users/unfollow", json={"user_id": user2_id}, status=200)
        self.post("/users/unfollow", json={"user_id": user2_id}, status=200)
        assert self.is_following(follower_user_id=user_id, followed_user_id=user2_id) is False

    def test_follow_invalid_user_id(self, user):
        self.optimized_login("contributor")
        self.post("/users/unfollow", json={"user_id": -1}, status=200)  # he's not followed, oso no error
