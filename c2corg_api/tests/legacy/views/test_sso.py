import pytest

pytestmark = pytest.mark.skip("not used anymore")
from unittest.mock import patch, Mock
from urllib.parse import urlparse, parse_qs

from pydiscourse.exceptions import DiscourseClientError

from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User

# 
from c2corg_api.security.discourse_client import set_discourse_client
from c2corg_api.tests.legacy.views import BaseTestRest

# 

sso_domain = "external.domain.net"
sso_key = "sso_test_key"


class TestSsoSyncRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._url = "/sync_sso"

        self.contributor = self.session.query(User).filter(User.username == "contributor").one()

        self.session_add(
            SsoKey(
                domain=sso_domain,
                key=sso_key,
            )
        )
        self.contributor_external_id = SsoExternalId(
            domain=sso_domain,
            external_id="1",
            user=self.contributor,
        )
        self.session_add(self.contributor_external_id)
        self.session.flush()

        set_discourse_client(None)

    def test_no_sso_key(self):
        request_body = {"external_id": "999", "email": "newuser@external.domain.net"}
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "sso_key" == errors[0].get("name")
        assert "Required" == errors[0].get("description")

    def test_bad_sso_key(self):
        request_body = {"sso_key": "bad_sso_key", "external_id": "999", "email": "newuser@external.domain.net"}
        body = self.app_post_json(self._url, request_body, status=403).json
        errors = body.get("errors")
        assert "sso_key" == errors[0].get("name")
        assert "Invalid" == errors[0].get("description")

    def test_no_external_id(self):
        request_body = {"sso_key": sso_key}
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "external_id" == errors[0].get("name")
        assert "Required" == errors[0].get("description")

    def test_new_user_no_email(self):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
        }
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "email" == errors[0].get("name")
        assert "Required" == errors[0].get("description")

    def test_new_user_existing_username(self):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": self.contributor.username,
            "lang": "fr",
            "groups": "group1,group2",
        }
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "already used username" == errors[0].get("description")

    def test_new_user_existing_forum_username(self):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": "newuser",
            "forum_username": self.contributor.forum_username,
            "lang": "fr",
            "groups": "group1,group2",
        }
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "A user still exists with this name" == errors[0].get("description")

    def test_new_user_forum_username_too_long(self):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": "newuser",
            "forum_username": "more_than_twenty_five_characters",
            "lang": "fr",
            "groups": "group1,group2",
        }
        body = self.app_post_json(self._url, request_body, status=400).json
        errors = body.get("errors")
        assert "forum_username" == errors[0].get("name")
        assert "Longer than maximum length 25" == errors[0].get("description")

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(
            by_external_id=Mock(side_effect=DiscourseClientError(response=Mock(status_code=404))),
            sync_sso=Mock(return_value={"id": 555}),
        ),
    )
    def test_new_user_success(self, discourse_mock):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": "newuser",
            "name": "New User",
            "forum_username": "NewUser",
            "lang": "fr",
        }
        body = self.app_post_json(self._url, request_body, status=200).json

        sso_external_id = (
            self.session.query(SsoExternalId)
            .filter(SsoExternalId.domain == sso_domain)
            .filter(SsoExternalId.external_id == "999")
            .one_or_none()
        )
        assert sso_external_id is not None
        sso_user = sso_external_id.user
        assert "newuser" == sso_user.username
        assert "New User" == sso_user.name
        assert "NewUser" == sso_user.forum_username

        assert sso_external_id.token == self.token_from_url(body.get("url"))

        client = discourse_mock.return_value
        client.by_external_id.assert_called_with(sso_external_id.user.id)
        client.sync_sso.assert_called_once_with(
            sso_secret=self.settings.get("discourse.sso_secret"),
            name="New User",
            username="NewUser",
            email="newuser@external.domain.net",
            external_id=sso_user.id,
            **{"custom.user_field_1": str(sso_user.id)}
        )

    def token_from_url(self, url):
        qs = parse_qs(urlparse(url).query)
        return qs.get("token")[0]

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(by_external_id=Mock(return_value={"id": 1, "username": "contributor"})),
    )
    def test_success_by_email(self, discourse_mock):
        request_body = {"sso_key": sso_key, "external_id": "1", "email": self.contributor.email}
        body = self.app_post_json(self._url, request_body, status=200).json

        sso_external_id = (
            self.session.query(SsoExternalId)
            .filter(SsoExternalId.domain == sso_domain)
            .filter(SsoExternalId.external_id == "1")
            .one_or_none()
        )
        assert sso_external_id is not None
        assert "contributor" == sso_external_id.user.username

        assert sso_external_id.token == self.token_from_url(body.get("url"))

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(by_external_id=Mock(return_value={"id": 1, "username": "contributor"})),
    )
    def test_success_by_external_id(self, discourse_mock):
        request_body = {
            "sso_key": sso_key,
            "external_id": "1",
            "email": "email@external.domain.net",
            "username": self.contributor.username,
            "name": self.contributor.name,
            "forum_username": self.contributor.forum_username,
            "lang": "fr",
        }
        body = self.app_post_json(self._url, request_body, status=200).json

        self.session.expire(self.contributor_external_id)
        assert self.contributor_external_id.token == self.token_from_url(body.get("url"))

        client = discourse_mock.return_value
        client.by_external_id.assert_called_once_with(self.contributor.id)

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(by_external_id=Mock(side_effect=ConnectionError())),
    )
    def test_discourse_down(self, discourse_mock):
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": "newuser",
            "name": "New User",
            "forum_username": "NewUser",
            "lang": "fr",
        }
        body = self.app_post_json(self._url, request_body, status=500).json
        errors = body.get("errors")
        assert "Error with Discourse" == errors[0].get("description")

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(
            by_external_id=Mock(side_effect=DiscourseClientError(response=Mock(status_code=404))),
            sync_sso=Mock(return_value={"id": 555}),
        ),
    )
    def test_new_user_no_name(self, discourse_mock):
        """name and forum_username should default to username"""
        request_body = {
            "sso_key": sso_key,
            "external_id": "999",
            "email": "newuser@external.domain.net",
            "username": "newuser",
            "lang": "fr",
        }
        self.app_post_json(self._url, request_body, status=200).json

        sso_external_id = (
            self.session.query(SsoExternalId)
            .filter(SsoExternalId.domain == sso_domain)
            .filter(SsoExternalId.external_id == "999")
            .one_or_none()
        )
        assert sso_external_id is not None
        sso_user = sso_external_id.user
        assert "newuser" == sso_user.username
        assert "newuser" == sso_user.name
        assert "newuser" == sso_user.forum_username

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(
            by_external_id=Mock(return_value={"id": 1, "username": "contributor"}),
            sync_sso=Mock(return_value={"id": 1}),
            groups=Mock(return_value=[]),
        ),
    )
    def test_not_found_group(self, discourse_mock):
        request_body = {
            "sso_key": sso_key,
            "external_id": "1",
            "group": "group_1",
        }
        self.app_post_json(self._url, request_body, status=200).json

    @patch(
        "c2corg_api.security.discourse_client.DiscourseClient",
        return_value=Mock(
            by_external_id=Mock(return_value={"id": 1, "username": "contributor"}),
            groups=Mock(return_value=[{"id": 222, "name": "group_1"}]),
            add_user_to_group=Mock(),
        ),
    )
    def test_existing_group(self, discourse_mock):
        request_body = {"sso_key": sso_key, "external_id": "1", "groups": "group_1"}
        self.app_post_json(self._url, request_body, status=200).json

        client = discourse_mock.return_value
        client.add_user_to_group.assert_called_once_with(222, 1)


class TestSsoLoginRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._url = "/sso_login"

        self.contributor = self.session.query(User).filter(User.username == "contributor").one()

        self.session_add(
            SsoKey(
                domain=sso_domain,
                key=sso_key,
            )
        )

        self.sso_external_id = SsoExternalId(
            domain=sso_domain,
            external_id="1",
            user=self.contributor,
        )
        self.sso_external_id.token = "good_token"
        self.session_add(self.sso_external_id)

        self.session.flush()

    def test_no_token(self):
        body = self.app_post_json(self._url, status=400).json
        errors = body.get("errors")
        assert "token" == errors[0].get("name")
        assert "Required" == errors[0].get("description")

    def test_invalid_token(self):
        body = self.app_post_json(self._url, {"token": "bad_token"}, status=403).json
        errors = body.get("errors")
        assert "token" == errors[0].get("name")
        assert "Invalid" == errors[0].get("description")

    def test_expired_token(self):
        self.sso_external_id.expire = localized_now()
        self.session.flush()

        body = self.app_post_json(self._url, params={"token": "good_token"}, status=403).json
        errors = body.get("errors")
        assert "token" == errors[0].get("name")
        assert "Invalid" == errors[0].get("description")

    def test_success(self):
        self.sso_external_id.expire = sso_expire_from_now()
        self.session.flush()

        body = self.app_post_json(self._url, {"discourse": True, "token": "good_token"}, status=200).json
        assert "token" in body

    @patch(
        "c2corg_api.views.sso.get_discourse_client",
        return_value=Mock(redirect_without_nonce=Mock(return_value="https://discourse_redirect")),
    )
    def test_success_discourse_up(self, discourse_mock):
        self.sso_external_id.expire = sso_expire_from_now()
        self.session.flush()

        body = self.app_post_json(self._url, {"discourse": True, "token": "good_token"}, status=200).json
        assert "token" in body

    @patch(
        "c2corg_api.views.sso.get_discourse_client",
        return_value=Mock(redirect_without_nonce=Mock(side_effect=Exception)),
    )
    def test_success_discourse_down(self, discourse_mock):
        # SSO login allowed even if Discourse is down.
        self.sso_external_id.expire = sso_expire_from_now()
        self.session.flush()

        body = self.app_post_json(self._url, {"discourse": True, "token": "good_token"}, status=200).json
        assert "token" in body
