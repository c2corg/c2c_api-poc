from pydiscourse.client import DiscourseClient

import logging

from base64 import b64encode, b64decode
from werkzeug.exceptions import BadRequest

import hmac
import hashlib
import requests
import urllib.error

from urllib.parse import parse_qs

log = logging.getLogger(__name__)


class APIDiscourseClient(object):
    def __init__(self, settings):
        self.settings = settings
        self.timeout = int(settings["url.timeout"])
        self.discourse_base_url = settings["discourse.url"]
        self.discourse_public_url = settings["discourse.public_url"]
        self.api_key = settings["discourse.api_key"]
        self.sso_key = str(settings["C2C_DISCOURSE_SSO_SECRET"])  # no unicode

        self.discourse_userid_cache = {}
        # FIXME: are we guaranteed usernames can never change? -> no!
        self.discourse_username_cache = {}

        self.client = DiscourseClient(
            self.discourse_base_url,
            api_username="system",  # the built-in Discourse user
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def get_userid(self, userid):
        discourse_userid = self.discourse_userid_cache.get(userid)
        if not discourse_userid:
            discourse_user = self.client.by_external_id(userid)
            discourse_userid = discourse_user["id"]
            self.discourse_userid_cache[userid] = discourse_userid
            self.discourse_username_cache[userid] = discourse_user["username"]
        return discourse_userid

    def sync_sso(self, user, email):
        result = self.client.sync_sso(
            sso_secret=self.sso_key,
            name=user.name,
            username=user.name,
            email=email,
            external_id=user.id,
            **{"custom.user_field_1": str(user.id)}
        )
        if result:
            self.discourse_userid_cache[user.id] = result["id"]
        return result

    def logout(self, userid):
        discourse_userid = self.get_userid(userid)
        self.client.log_out(discourse_userid)
        return discourse_userid

    def suspend(self, userid, duration, reason):
        discourse_userid = self.get_userid(userid)
        return self.client.suspend(discourse_userid, duration, reason)

    def unsuspend(self, userid):
        discourse_userid = self.get_userid(userid)
        return self.client.unsuspend(discourse_userid)

    # Below this: SSO provider
    def decode_payload(self, payload):
        decoded = b64decode(payload.encode("utf-8")).decode("utf-8")
        assert "nonce" in decoded
        assert len(payload) > 0
        return decoded

    def check_signature(self, payload, signature):
        key = self.sso_key.encode("utf-8")
        h = hmac.new(key, payload.encode("utf-8"), digestmod=hashlib.sha256)
        this_signature = h.hexdigest()

        if this_signature != signature:
            log.error("Signature mismatch")
            raise BadRequest("discourse login failed")

    def request_nonce(self):
        url = "%s/session/sso" % self.discourse_base_url
        try:
            r = requests.get(url, allow_redirects=False, timeout=self.timeout)
            assert r.status_code == 302
        except Exception as e:
            log.exception("Could not request nonce")
            raise Exception("Could not request nonce") from e

        location = r.headers["Location"]
        parsed = urllib.parse.urlparse(location)
        params = urllib.parse.parse_qs(parsed.query)
        sso = params["sso"][0]
        sig = params["sig"][0]

        self.check_signature(sso, sig)
        payload = self.decode_payload(sso)
        return parse_qs(payload)["nonce"][0]

    def create_response_payload(self, user, nonce, url_part):
        assert nonce is not None, "No nonce passed"

        params = {
            "nonce": nonce,
            "email": user["email"],  # I know what I do
            "external_id": user["id"],
            "username": user["name"],
            "name": user["name"],
            "custom.user_field_1": user["id"],
        }

        key = self.sso_key.encode("utf-8")
        r_payload = b64encode(urllib.parse.urlencode(params).encode("utf-8"))
        h = hmac.new(key, r_payload, digestmod=hashlib.sha256)
        qs = urllib.parse.urlencode({"sso": r_payload, "sig": h.hexdigest()})
        return "%s%s?%s" % (self.discourse_public_url, url_part, qs)

    def redirect_without_nonce(self, user):
        nonce = self.request_nonce()
        return self.create_response_payload(user, nonce, "/session/sso_login")


c = None


def get_discourse_client(settings):
    global c
    if c is None:
        c = APIDiscourseClient(settings)
    return c


def set_discourse_client(client):
    global c
    c = client
