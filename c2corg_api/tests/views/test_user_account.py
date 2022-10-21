import pytest
from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.legacy.models.user_profile import USERPROFILE_TYPE
from c2corg_api.legacy.search import search_documents, elasticsearch_config
from c2corg_api.tests.views.test_user import BaseUserTestRest, forum_username_tests

from unittest.mock import patch


class TestUserAccountRest(BaseUserTestRest):
    def test_read_account_info(self):
        url = "/users/account"
        body = self.get_json_with_contributor(url, status=200)
        assert body.get("name") == "contributor"
        assert body.get("email") == "contributor@camptocamp.org"
        assert body.get("forum_username") == "contributor"
        assert body.get("is_profile_public") == False

    @pytest.mark.skip(reason="blocked users can view their account")
    def test_read_account_info_blocked_account(self):
        contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        contributor.blocked = True
        self.session.flush()

        body = self.get_json_with_contributor("/users/account", status=403)
        self.assertErrorsContain(body, "Forbidden", "account blocked")

    def _update_account_field_discourse_up(self, field, value):
        url = "/users/account"
        currentpassword = self.global_passwords["contributor"]

        data = {"currentpassword": currentpassword}
        data[field] = value
        self.post_json_with_contributor(url, data, status=200)

        assert 1 == int(self.discourse_client.sync_sso.called_count)

    def _update_account_field_discourse_down(self, field, value):
        self.set_discourse_down()

        url = "/users/account"
        currentpassword = self.global_passwords["contributor"]

        data = {"currentpassword": currentpassword}
        data[field] = value
        self.post_json_with_contributor(url, data, status=500)

        assert 1 == int(self.discourse_client.sync_sso.called_count)

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_update_account_email_discourse_up(self, _send_email):
        new_email = "superemail@localhost.localhost"
        self._update_account_field_discourse_up("email", new_email)

        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        assert user.email_to_validate == new_email
        assert user.email != new_email

        _send_email.assert_called_once()

        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "validate_change_email")
        url_api_validation = "/users/validate_change_email/%s" % nonce
        self.app_post_json(url_api_validation, {}, status=200)

        self.expunge(user)
        user = self.query_get(User, user_id=user_id)
        assert user.email == new_email
        assert user.validation_nonce is None

    def test_update_account_email_discourse_down(self):
        new_email = "superemail@localhost.localhost"
        self._update_account_field_discourse_down("email", new_email)

    def test_update_account_name_discourse_up(self):
        self._update_account_field_discourse_up("name", "changed")

        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        assert user.name == "changed"

        # check that the search index is updated with the new name
        self.sync_es()
        search_doc = self.search_document(USERPROFILE_TYPE, user_id=user_id, index=elasticsearch_config["index"])

        # and check that the cache version of the user profile was updated
        self.check_cache_version(user_id, 2)

        assert search_doc["doc_type"] is not None
        assert search_doc["title_en"] == "contributor"

    def test_update_account_name_discourse_down(self):
        self._update_account_field_discourse_down("name", "changed")

    def test_update_account_forum_username_validity(self):
        url = "/users/account"
        i = 0
        for forum_username, value in forum_username_tests.items():
            i += 1
            body = {"currentpassword": self.global_passwords["contributor"], "forum_username": forum_username}
            if value is False:
                self.post_json_with_contributor(url, body, status=200)
            else:
                json = self.post_json_with_contributor(url, body, status=400)
                assert json["description"] == value

    def test_update_account_forum_username_unique(self):
        url = "/users/account"

        data = {"currentpassword": self.global_passwords["contributor"], "forum_username": "unique"}
        self.post_json_with_contributor(url, data, status=200)

        data = {"currentpassword": self.global_passwords["contributor2"], "forum_username": "Unique"}
        json = self.post_json_with_contributor(url, data, status=400, username="contributor2")
        assert json["description"] == "Name is already used"

    def test_update_account_forum_username_discourse_up(self):
        self._update_account_field_discourse_up("forum_username", "changed")

        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        assert user.forum_username == "changed"

    def test_update_account_forum_username_discourse_down(self):
        self._update_account_field_discourse_down("forum_username", "changed")

    def test_update_is_profile_public_discourse_down(self):
        data = {"currentpassword": self.global_passwords["contributor"], "is_profile_public": True}
        self.post_json_with_contributor("/users/account", data, status=200)

        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        assert user.is_profile_public == True

    def test_update_preferred_lang(self):
        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        assert user.lang == "fr"

        request_body = {"lang": "en"}
        url = self._prefix + "/update_preferred_language"
        self.post_json_with_contributor(url, request_body, status=200)

        self.expunge(user)
        user = self.query_get(User, user_id=user_id)
        assert user.lang == "en"
