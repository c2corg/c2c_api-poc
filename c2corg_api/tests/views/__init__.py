from os import sync
from flask_camp.models import User
from sqlalchemy import select

from c2corg_api.hooks import on_user_creation, ProfilePageLink, on_user_validation
from c2corg_api.legacy.models.user import User as LegacyUser
from c2corg_api.legacy.models.user_profile import UserProfile
from c2corg_api.search import search
from c2corg_api.tests.conftest import BaseTestClass


class BaseTestRest(BaseTestClass):

    client = None
    global_userids = {}
    global_passwords = {}
    global_session_cookies = {}

    def setup_method(self):
        super().setup_method()

        self._add_global_test_data()

    def _add_global_test_data(self):
        self._add_user("contributor", "super pass")
        self._add_user("contributor2", "super pass")
        self._add_user("moderator", "super pass")

    def _add_user(self, name, password):
        user = User(name=name)
        self.api.database.session.add(user)

        user.set_password(password)
        user.set_email(f"{name}@camptocamp.org")
        on_user_creation(user, body={})

        user.validate_email(user._email_token)
        on_user_validation(user, sync_sso=False)

        self.api.database.session.flush()

        self.global_userids[user.name] = user.id
        self.global_passwords[user.name] = password

    ######### dedicated function for legacy tests
    def check_cache_version(self, user_id, cache_version):
        pass

    def optimized_login(self, user_name):
        if user_name not in self.global_session_cookies:
            self.login_user(user_name, self.global_passwords["contributor"])
            cookies = list(self.client.cookie_jar)
            session_cookie = [cookie for cookie in cookies if cookie.name == "session"][0]
            self.global_session_cookies[user_name] = session_cookie.value
        else:
            self.client.set_cookie("localhost.host", "session", self.global_session_cookies[user_name])

    def get_json_with_contributor(self, url, username="contributor", status=200):
        self.optimized_login(username)
        return self.get(url, prefix="", status=status).json

    def post_json_with_contributor(self, url, json, username="contributor", status=200):
        self.optimized_login(username)
        return self.post(url, prefix="", json=json, status=status).json

    def post_json_with_token(self, url, token, **kwargs):
        return self.app_send_json("post", url, {}, **kwargs)

    def app_post_json(self, url, json, **kwargs):
        return self.app_send_json("post", url, json, **kwargs)

    def app_send_json(self, action, url, json, **kwargs):
        return getattr(self, action)(url=url, prefix="", json=json, **kwargs)

    def query_get(self, klass, **kwargs):
        parameter_name, parameter_value = list(kwargs.items())[0]

        if klass is LegacyUser:
            if parameter_name == "user_id":
                # query = select(ProfilePageLink.user_id).where(ProfilePageLink.document_id == parameter_value)
                # result = self.session.execute(query)
                # user_id = list(result)[0][0]

                user = self.session.query(User).get(parameter_value)
                return LegacyUser.from_user(user)
            elif parameter_name == "username":
                user = self.session.query(User).filter_by(User.name == parameter_value).first()
                return LegacyUser.from_user(user)
            else:
                raise TypeError("TODO...")

        if klass is UserProfile:
            return UserProfile(parameter_value)

        raise TypeError("TODO...")

    def extract_nonce(self, _send_mail, key):
        message = _send_mail.call_args_list[0][0][0]
        body = message.body
        token = body.split("=")[1]
        return token

    def expunge(self, item):
        if isinstance(item, UserProfile):
            return
            # self.session.expunge(item._user)
        elif isinstance(item, LegacyUser):
            self.session.expunge(item._user)
        else:
            self.session.expunge(item)

    def assertErrorsContain(self, body, error_name):
        assert body["status"] != "ok"

    def search_document(self, document_type, id=None, user_id=None, index=None, ignore=None):

        document_ids = search(document_type=document_type, id=id, user_id=user_id)

        if len(document_ids) == 0:
            if ignore == 404:
                return None
            else:
                raise Exception()

        document_as_dict = self.api.get_cooked_document(document_ids[0])
        data = document_as_dict["data"]

        return {
            "doc_type": document_as_dict["data"].get("type"),
            "title_fr": data["locales"]["fr"]["title"],
            "title_en": data["locales"]["en"]["title"],
        }

    def sync_es(self):
        pass

    @property
    def settings(self):
        return self.app.config
