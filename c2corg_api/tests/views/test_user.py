import pytest
from c2corg_api.legacy.scripts.es.sync import sync_es
from c2corg_api.legacy.search import search_documents, elasticsearch_config

# from pytest import mark

# from c2corg_api.models.token import Token
from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.legacy.models.user_profile import UserProfile, USERPROFILE_TYPE

from c2corg_api.tests.views import BaseTestRest
from c2corg_api.security.discourse_client import APIDiscourseClient, get_discourse_client, set_discourse_client

from urllib.parse import urlparse

import re

from unittest.mock import Mock, MagicMock, patch


forum_username_tests = {
    # min length
    "a": r"'a' does not match '^[^ @\\/?&]{3,64}$' on instance ['name']",
    "a" * 3: False,
    # max length (colander schema validation)
    "a" * 26: "Longer than maximum length 25",
    "a" * 25: False,
    # valid characters
    "test/test": r"'test/test' does not match '^[^ @\\/?&]{3,64}$' on instance ['name']",
    "test.test-test_test": False,
    # first char
    "-test": "First character is invalid",
    # last char
    "test.": "Last character is invalid",
    # double special char
    "test__test": ("Contains consecutive special characters"),
    # confusing suffix
    "test.jpg": "Ended by confusing suffix",
}


class BaseUserTestRest(BaseTestRest):
    def setup_method(self):
        self.original_discourse_client = get_discourse_client(self.settings)
        self._prefix = "/users"
        self._model = User
        BaseTestRest.setup_method(self)
        self.set_discourse_up()

    def teardown_method(self):
        BaseTestRest.teardown_method(self)
        self.set_discourse_not_mocked()

    def set_discourse_client_mock(self, client):
        self.discourse_client = client
        set_discourse_client(client)

    def set_discourse_not_mocked(self):
        self.set_discourse_client_mock(self.original_discourse_client)

    def set_discourse_up(self):
        # unittest.Mock works great with a completely fake object
        mock = Mock()
        mock.redirect_without_nonce = MagicMock(return_value="https://discourse_redirect")
        mock.redirect = MagicMock()
        mock.sync_sso = MagicMock()
        self.set_discourse_client_mock(mock)

    def set_discourse_down(self):
        # unittest.Mock wants a concrete object to throw correctly
        mock = APIDiscourseClient(self.settings)
        mock.redirect_without_nonce = MagicMock(return_value="https://discourse_redirect", side_effect=Exception)
        mock.redirect = MagicMock(side_effect=Exception)
        mock.sync_sso = MagicMock(side_effect=Exception)
        self.set_discourse_client_mock(mock)

    def extract_urls(self, data):
        return re.findall(
            r"http[s]?://"
            r"(?:"
            r"[a-zA-Z]|"
            r"[0-9]|"
            r"[$-_@#.&+]|"
            r"[!*\(\),]|"
            r"(?:%[0-9a-fA-F][0-9a-fA-F])"
            r")+[0-9a-zA-Z]",
            data,
        )

    def extract_nonce_TO_BE_DELETED(self, _send_mail, key):
        match = self.extract_urls(_send_mail.call_args_list[0][1]["body"])
        validation_url = match[0]
        fragment = urlparse(validation_url).fragment
        nonce = fragment.replace(key + "=", "")
        return nonce


class TestUserRest(BaseUserTestRest):
    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_always_register_non_validated_users(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email_validated": True,
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        # First succeed in creating a new user
        body = self.app_post_json(url, request_body, status=200).json
        user_id = body.get("id")
        user = self.query_get(User, user_id=user_id)
        assert user.email_validated is False
        _send_email.check_call_once()

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_default_lang(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        body = self.app_post_json(url, request_body, status=200).json
        user_id = body.get("id")
        user = self.query_get(User, user_id=user_id)
        assert user.lang == "fr"
        _send_email.check_call_once()

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_passed_lang(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "test",
            "lang": "en",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        body = self.app_post_json(url, request_body, status=200).json
        user_id = body.get("id")
        user = self.query_get(User, user_id=user_id)
        assert user.lang == "en"
        _send_email.check_call_once()

    def test_register_invalid_lang(self):
        request_body = {
            "username": "test",
            "forum_username": "test",
            "lang": "nn",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"
        self.app_post_json(url, request_body, status=400).json

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_forum_username_validity(self, _send_email):
        url = self._prefix + "/register"
        i = 0
        for forum_username, value in forum_username_tests.items():
            i += 1
            request_body = {
                "username": forum_username,
                "forum_username": forum_username,
                "name": "Max Mustermann{}".format(i),
                "password": "super secret",
                "email": "some_user{}@camptocamp.org".format(i),
            }
            if value is False:
                self.app_post_json(url, request_body, status=200).json
            else:
                json = self.app_post_json(url, request_body, status=400).json
                assert json["description"] == value

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_forum_username_unique(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "contributor",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"
        json = self.app_post_json(url, request_body, status=400).json
        assert json["description"] == "A user still exists with this name"

    @patch("flask_camp._services._send_mail.SendMail.send")
    @pytest.mark.skip(reason="username is removed in new model")
    def test_register_username_email_not_equals_email(self, _send_email):
        request_body = {
            "username": "someone_else@camptocamp.org",
            "forum_username": "Contributor4",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"
        json = self.app_post_json(url, request_body, status=400).json
        self.assertEqual(
            json["description"],
            "An email address used as username should be the " + "same as the one used as the account email address.",
        )

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_username_email_equals_email(self, _send_email):
        request_body = {
            "username": "some_user@camptocamp.org",
            "forum_username": "Contributor4",
            "name": "Frankie Vincent",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"
        self.app_post_json(url, request_body, status=200)

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_invalid_email(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "contributor",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_useratcamptocamp.org",
        }
        url = self._prefix + "/register"
        json = self.app_post_json(url, request_body, status=400).json
        assert json["description"] == "'some_useratcamptocamp.org' is not a 'email' on instance ['email']"

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_discourse_up(self, _send_email):
        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        # First succeed in creating a new user
        body = self.app_post_json(url, request_body, status=200).json
        assert body.get("username") == "test"
        assert body.get("forum_username") == "test"
        assert body.get("name") == "Max Mustermann"
        assert body.get("email") == "some_user@camptocamp.org"
        assert "password" not in body
        assert "id" in body
        user_id = body.get("id")
        user = self.query_get(User, user_id=user_id)
        assert user is not None
        assert user.email_validated is False
        profile = self.query_get(UserProfile, user_id=user_id)
        assert profile is not None
        assert len(profile.versions) == 1
        _send_email.check_call_once()

        assert user.lang == "fr"
        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "validate_register_email")
        url_api_validation = "/users/validate_register_email/%s" % nonce
        self.app_post_json(url_api_validation, {}, status=200)

        # Need to expunge the profile and user so that the latest
        # version (the one from the view) is actually picked up.
        self.expunge(profile)
        self.expunge(user)
        profile = self.query_get(UserProfile, user_id=user_id)
        assert len(profile.versions) == 1
        user = self.query_get(User, user_id=user_id)
        assert user.email_validated is True

        # Now reject non unique attributes
        body = self.app_post_json(url, request_body, status=400).json
        self.assertErrorsContain(body, "email")
        self.assertErrorsContain(body, "username")

        # Require username, password and email attributes
        body = self.app_post_json(url, {}, status=400).json
        self.assertErrorsContain(body, "email")
        self.assertErrorsContain(body, "username")
        self.assertErrorsContain(body, "password")

        # Usage of utf8 password
        request_utf8 = {
            "username": "utf8",
            "name": "utf8",
            "forum_username": "utf8f",
            "password": "élève 日本",
            "email": "utf8@camptocamp.org",
        }
        body = self.app_post_json(url, request_utf8, status=200).json

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_search_index(self, _send_email):
        """Tests that user accounts are only indexed once they are confirmed."""
        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        body = self.app_post_json(url, request_body, status=200).json
        assert "id" in body
        user_id = body.get("id")

        # check that the profile is not inserted in the search index
        sync_es(self.session)
        search_doc = self.search_document(
            USERPROFILE_TYPE, user_id=user_id, index=elasticsearch_config["index"], ignore=404
        )
        assert search_doc is None

        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "validate_register_email")
        url_api_validation = "/users/validate_register_email/%s" % nonce
        self.app_post_json(url_api_validation, {}, status=200)

        # check that the profile is inserted in the index after confirmation
        self.sync_es()
        search_doc = self.search_document(USERPROFILE_TYPE, user_id=user_id, index=elasticsearch_config["index"])
        assert search_doc is not None

        assert search_doc["doc_type"] is not None
        assert search_doc["title_fr"] == "test"

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_register_discourse_down(self, _send_email):
        self.set_discourse_down()
        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }
        url = self._prefix + "/register"

        # First succeed in creating a new user
        self.app_post_json(url, request_body, status=200)

        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "validate_register_email")
        url_api_validation = "/users/validate_register_email/%s" % nonce

        self.app_post_json(url_api_validation, {}, status=500)

    def test_forgot_password_non_existing_email(self):
        url = "/users/request_password_change"
        body = self.app_post_json(url, {"email": "non_existing_oeuhsaeuh@camptocamp.org"}, status=200).json

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_forgot_password_discourse_up(self, _send_email):
        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        initial_encoded_password = user.password

        url = "/users/request_password_change"
        self.app_post_json(url, {"email": user.email}, status=200).json

        _send_email.check_call_once()

        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "change_password")
        url_api_validation = "/users/validate_new_password/%s" % nonce

        self.app_post_json(url_api_validation, {"password": "new pass"}, status=200)

        self.expunge(user)
        user = self.query_get(User, user_id=user_id)
        assert user.validation_nonce is None
        modified_encoded_password = user.password

        assert initial_encoded_password != modified_encoded_password

    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_forgot_password_discourse_down(self, _send_email):
        self.set_discourse_down()
        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)

        url = "/users/request_password_change"
        self.app_post_json(url, {"email": user.email}, status=200).json

        _send_email.check_call_once()

        # Simulate confirmation email validation
        nonce = self.extract_nonce(_send_email, "change_password")
        url_api_validation = "/users/validate_new_password/%s" % nonce

        # Succeed anyway since only the password has changed
        self.app_post_json(url_api_validation, {"password": "new pass"}, status=200)

    def test_forgot_password_blocked_account(self):
        user_id = self.global_userids["contributor"]
        user = self.query_get(User, user_id=user_id)
        user.blocked = True
        self.session.flush()

        url = "/users/request_password_change"
        self.app_post_json(url, {"email": user.email}, status=403)

    # @mark.jobs
    @patch("flask_camp._services._send_mail.SendMail.send")
    def test_purge_accounts(self, _send_email):
        from c2corg_api.jobs.purge_non_activated_accounts import purge_account
        from datetime import datetime, timedelta

        request_body = {
            "username": "test",
            "forum_username": "test",
            "name": "Max Mustermann",
            "password": "super secret",
            "email": "some_user@camptocamp.org",
        }

        now = datetime.utcnow()
        query = self.session.query(NewUser).filter(NewUser.name == "test")

        # First succeed in creating a new user
        url = "/users/register"
        self.app_post_json(url, request_body, status=200)

        # Then simulate a scheduled call to purge accounts
        purge_account()

        # The user should still exist
        user = query.one()

        # Expire nonce
        user.creation_date = now - timedelta(days=3)
        self.session.commit()

        # The user should be removed
        purge_account()
        assert 0 == query.count()

    # @mark.jobs
    @pytest.mark.skip(reason="No such model in flask_camp")
    def test_purge_tokens(self):
        from c2corg_api.jobs.purge_expired_tokens import purge_token
        from datetime import datetime, timedelta

        body = self.login("moderator", status=200).json
        token_value = body["token"]

        query = self.session.query(Token).filter(Token.value == token_value)

        now = datetime.utcnow()

        # Token should still exist
        purge_token(self.session)
        assert 1 == query.count()

        # Expire token
        token = query.one()
        token.expire = now

        # The token should be removed
        purge_token(self.session)
        assert 0 == query.count()

    def login(self, username, password=None, status=200, sso=None, sig=None, discourse=None):
        if not password:
            password = self.global_passwords[username]

        request_body = {"username": username, "password": password}

        if sso:
            request_body["sso"] = sso
        if sig:
            request_body["sig"] = sig
        if discourse:
            request_body["discourse"] = discourse

        url = "/users/login"
        response = self.app_post_json(url, request_body, status=status)
        return response

    def test_login_success_discourse_up(self):
        body = self.login("moderator", status=200).json
        assert "token" in body

    def test_login_success_discourse_down(self):
        # Topoguide login allowed even if Discourse is down.
        body = self.login("moderator", status=200).json
        assert "token" in body

    def test_login_success_use_email(self):
        # login allowed if providing the email instead of login
        body = self.login("moderator@camptocamp.org", self.global_passwords["moderator"], status=200).json
        assert "token" in body

    @pytest.mark.skip(reason="blocked users can log-in")
    def test_login_blocked_account(self):
        contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        contributor.blocked = True
        self.session.flush()

        body = self.login("contributor", status=403).json
        self.assertErrorsContain(body, "Forbidden", "account blocked")

    @pytest.mark.skip(reason="sso in login payload not used anymore?")
    def test_login_discourse_success(self):
        self.set_discourse_not_mocked()
        # noqa See https://meta.discourse.org/t/official-single-sign-on-for-discourse/13045
        sso = "bm9uY2U9Y2I2ODI1MWVlZmI1MjExZTU4YzAwZmYxMzk1ZjBjMGI%3D%0A"
        sig = "2828aa29899722b35a2f191d34ef9b3ce695e0e6eeec47deb46d588d70c7cb56"  # noqa

        moderator = self.session.query(NewUser).filter(NewUser.name == "moderator").one()
        redirect1 = self.discourse_client.redirect(moderator, sso, sig)

        body = self.login("moderator", sso=sso, sig=sig, discourse=True).json
        assert "token" in body
        redirect2 = body["redirect"]

        assert redirect1 == redirect2

    def test_login_failure(self):
        body = self.login("moderator", password="invalid", status=403).json
        assert body["status"] == "error"

    def assertExpireAlmostEqual(self, expire, days, seconds_delta):  # noqa
        import time

        now = int(round(time.time()))
        expected = days * 24 * 3600 + now  # 14 days from now
        if abs(expected - expire) > seconds_delta:
            raise self.failureException("%r == %r within %r seconds" % (expected, expire, seconds_delta))

    def test_login_logout_success(self):
        body = self.login("moderator").json
        token = body["token"]
        expire = body["expire"]
        self.assertExpireAlmostEqual(expire, 14, 5)

        body = self.post_json_with_token("/users/logout", token)

    @pytest.mark.skip(reason="/renew is not used")
    def test_renew_success(self):
        token = self.global_tokens["contributor"]

        body = self.post_json_with_token("/users/renew", token)
        expire = body["expire"]
        self.assertExpireAlmostEqual(expire, 14, 5)

        token2 = body["token"]
        body = self.get_json_with_token("/users/account", token2, status=200)
        assert body.get("name") == "contributor"

    @pytest.mark.skip(reason="/renew is not used")
    def test_renew_token_different_success(self):
        # Tokens created in the same second are identical
        token1 = self.login("contributor").json["token"]

        import time

        print("Waiting for more than 1s to get a different token")
        time.sleep(1.01)

        token2 = self.post_json_with_token("/users/renew", token1)["token"]
        assert token1 != token2

        body = self.get_json_with_token("/users/account", token2, status=200)
        assert body.get("name") == "contributor"

        self.post_json_with_token("/users/logout", token1)
        self.post_json_with_token("/users/logout", token2)
