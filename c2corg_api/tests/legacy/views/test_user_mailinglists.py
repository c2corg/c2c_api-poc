import pytest
from flask_camp.models import User as NewUser
from c2corg_api.legacy.models.user import User
from c2corg_api.legacy.models.mailinglist import Mailinglist
from c2corg_api.tests.legacy.views import BaseTestRest

# from c2corg_api.models.common.attributes import mailinglists


@pytest.mark.skip(reason="Not used in actual UI")
def TestUserMailinglistsRest(BaseTestRest):
    def setup_method(self):
        super().setup_method()
        self._prefix = "/users/mailinglists"

        self.contributor = self.query_get(User, user_id=self.global_userids["contributor"])
        ml1 = Mailinglist(
            listname="meteofrance-74", email=self.contributor.email, user_id=self.contributor.id, user=self.contributor
        )
        ml2 = Mailinglist(
            listname="avalanche.en", email=self.contributor.email, user_id=self.contributor.id, user=self.contributor
        )
        self.session_add_all([ml1, ml2])
        self.session.flush()

    def test_get_mailinglists_unauthenticated(self):
        self.get(self._prefix, status=403)

    def test_get_mailinglists(self):
        headers = self.add_authorization_header(username="contributor")
        response = self.get(self._prefix, status=200, headers=headers)
        body = response.json

        assert len(body) == len(mailinglists)
        for ml in mailinglists:
            assert ml in body
            if ml in ["meteofrance-74", "avalanche.en"]:
                self.assertTrue(body[ml])
            else:
                self.assertFalse(body[ml])

    def test_post_mailinglists_unauthenticated(self):
        self.app_post_json(self._prefix, {}, status=403)

    def test_post_mailinglists_invalid(self):
        request_body = {"wrong_mailinglist_name": True, "avalanche": "incorrect_value"}

        headers = self.add_authorization_header(username="contributor")
        response = self.app_post_json(self._prefix, request_body, status=400, headers=headers)

        body = response.json
        assert body.get("status") == "error"
        errors = body.get("errors")
        assert self.get_error(errors, "wrong_mailinglist_name") is not None
        assert self.get_error(errors, "avalanche") is not None

    def test_post_mailinglists(self):
        request_body = {"meteofrance-66": True, "meteofrance-74": False}

        headers = self.add_authorization_header(username="contributor")
        self.app_post_json(self._prefix, request_body, status=200, headers=headers)

        mls = self.session.query(Mailinglist.listname).filter(Mailinglist.email == self.contributor.email).all()
        subscribed_mailinglists = [list[0] for list in mls]
        assert len(subscribed_mailinglists) == 2
        assert "meteofrance-66" in subscribed_mailinglists
        assert "avalanche.en" in subscribed_mailinglists
        assert "meteofrance-74" not in subscribed_mailinglists
